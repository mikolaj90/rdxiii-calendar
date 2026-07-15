from __future__ import annotations

import io
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from urllib.parse import urljoin

import pytesseract
import requests
from bs4 import BeautifulSoup, Tag
from pdf2image import convert_from_bytes
from pypdf import PdfReader

from .dates import extract_dates

BIP_ROOT = "https://www.bip.krakow.pl/"
MEETING_NO = re.compile(r"(?<!\d)(\d{1,3})\s*/\s*(20\d{2})(?!\d)")
TIME_PATTERNS = [
    re.compile(r"(?:o\s+)?godz(?:inie|ina|\.)?\s*[:.]?\s*(\d{1,2})\s*[:.]\s*(\d{2})", re.I),
    re.compile(r"(?:o\s+)?godz(?:inie|ina|\.)?\s+(\d{1,2})\s+(\d{2})(?!\d)", re.I),
]
CANCEL_WORDS = ("odwoł", "odwol", "nie odbędzie", "nie odbedzie", "nie odbyło", "nie odbylo", "brak kworum", "brak quorum")


@dataclass(frozen=True)
class Commission:
    document_id: int
    name: str
    full_name: str
    emoji: str

    @property
    def page_url(self) -> str:
        return f"{BIP_ROOT}?dok_id={self.document_id}"


@dataclass
class Meeting:
    commission: Commission
    number: str
    meeting_date: date
    start_time: time
    location: str
    source_page: str
    attachment_card: str
    cancelled: bool = False

    @property
    def uid(self) -> str:
        suffix = self.number.replace("/", "-") if self.number else self.meeting_date.isoformat()
        return f"rdxiii-{self.commission.document_id}-{suffix}@mikolaj90.github.io"

    @property
    def starts_at(self) -> datetime:
        return datetime.combine(self.meeting_date, self.start_time)

    @property
    def ends_at(self) -> datetime:
        return self.starts_at + timedelta(hours=1)


class ParseError(RuntimeError):
    pass


class BipClient:
    def __init__(self, timeout: int = 30) -> None:
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "rdxiii-calendar/1.0 (+https://github.com/mikolaj90/rdxiii-calendar)"
        self.timeout = timeout

    def get(self, url: str) -> requests.Response:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response

    def meetings(self, commission: Commission, since: date) -> tuple[list[Meeting], list[str]]:
        soup = BeautifulSoup(self.get(commission.page_url).text, "html.parser")
        result: list[Meeting] = []
        warnings: list[str] = []
        seen: set[str] = set()
        for block in self._meeting_blocks(soup):
            text = " ".join(block.stripped_strings)
            number_match = MEETING_NO.search(text)
            number = f"{number_match[1]}/{number_match[2]}" if number_match else ""
            meeting_year = int(number_match[2]) if number_match else None
            dates = extract_dates(text, meeting_year)
            if not dates:
                warnings.append(f"Brak daty w bloku: {text[:120]}")
                continue
            table_date = dates[0]
            if table_date < since:
                continue
            key = number or table_date.isoformat()
            if key in seen:
                continue
            link = self._convocation_link(block)
            if not link:
                warnings.append(f"Brak linku do zwołania dla {number or table_date}")
                continue
            card_url = urljoin(commission.page_url, link)
            try:
                pdf, final_card = self._download_pdf(card_url)
                pdf_text = self._extract_pdf_text(pdf)
                pdf_date, start_time = self._date_and_time(pdf_text, meeting_year)
                if pdf_date != table_date:
                    raise ParseError(f"sprzeczne daty: tabela {table_date}, PDF {pdf_date}")
                location = self._location(pdf_text)
            except Exception as exc:
                warnings.append(f"{number or table_date}: {exc}")
                continue
            result.append(Meeting(
                commission, number, table_date, start_time, location,
                commission.page_url, final_card,
                self._is_cancelled(text) or self._is_cancelled(pdf_text),
            ))
            seen.add(key)
        return result, warnings

    @staticmethod
    def _meeting_blocks(soup: BeautifulSoup) -> list[Tag]:
        rows = [row for row in soup.find_all("tr") if "zwołanie posiedzenia" in row.get_text(" ", strip=True).lower()]
        if rows:
            return rows
        result: list[Tag] = []
        for anchor in soup.find_all("a"):
            if "zwołanie posiedzenia" not in anchor.get_text(" ", strip=True).lower():
                continue
            parent = anchor.find_parent(["li", "section", "article", "div"])
            if parent and parent not in result:
                result.append(parent)
        return result

    @staticmethod
    def _convocation_link(block: Tag) -> str | None:
        for anchor in block.find_all("a", href=True):
            if "zwołanie posiedzenia" in anchor.get_text(" ", strip=True).lower():
                return str(anchor["href"])
        return None

    def _download_pdf(self, url: str) -> tuple[bytes, str]:
        response = self.get(url)
        if "application/pdf" in response.headers.get("content-type", "").lower() or response.content.startswith(b"%PDF"):
            return response.content, url
        soup = BeautifulSoup(response.text, "html.parser")
        for anchor in soup.find_all("a", href=True):
            label = " ".join(anchor.stripped_strings).lower()
            href = str(anchor["href"])
            if "zobacz załącznik" in label or "plik.php" in href:
                pdf_response = self.get(urljoin(response.url, href))
                if "application/pdf" in pdf_response.headers.get("content-type", "").lower() or pdf_response.content.startswith(b"%PDF"):
                    return pdf_response.content, response.url
                raise ParseError("odnośnik z karty załącznika nie zwrócił PDF-u")
        raise ParseError("karta załącznika nie zawiera linku do PDF-u")

    @staticmethod
    def _extract_pdf_text(pdf: bytes) -> str:
        reader = PdfReader(io.BytesIO(pdf))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if len(text.strip()) >= 80:
            return text
        images = convert_from_bytes(pdf, dpi=250, first_page=1, last_page=min(2, len(reader.pages)))
        text = "\n".join(pytesseract.image_to_string(image, lang="pol") for image in images)
        if len(text.strip()) < 40:
            raise ParseError("nie udało się odczytać tekstu PDF-u ani przez OCR")
        return text

    @staticmethod
    def _date_and_time(text: str, meeting_year: int | None) -> tuple[date, time]:
        normalized = text.replace("\u00a0", " ")
        match = None
        for pattern in TIME_PATTERNS:
            match = pattern.search(normalized)
            if match:
                break
        if not match:
            raise ParseError("nie znaleziono godziny posiedzenia w PDF-ie")
        try:
            start_time = time(int(match[1]), int(match[2]))
        except ValueError as exc:
            raise ParseError(f"niepoprawna godzina {match[1]}:{match[2]}") from exc
        dates = extract_dates(normalized[max(0, match.start() - 500):match.start()], meeting_year)
        if not dates:
            raise ParseError("nie znaleziono daty posiedzenia w pobliżu godziny")
        return dates[-1], start_time

    @staticmethod
    def _location(text: str) -> str:
        lines = [" ".join(line.split()) for line in text.splitlines() if line.strip()]
        if any("trybie zdalnym" in line.lower() or "posiedzenie zdalne" in line.lower() for line in lines):
            return "Online"
        address = re.compile(r"((?:Rynek|Plac|Aleja|al\.|ul\.|ulica|os\.)\s+[\wąćęłńóśźżĄĆĘŁŃÓŚŹŻ .'-]+?\s+\d+[A-Za-z]?(?:/\d+)?)", re.I)
        for line in lines:
            match = address.search(line)
            if match:
                value = re.sub(r"\s+w\s+Krakowie\b", "", match[1], flags=re.I).strip(" ,.")
                return value if "krak" in value.lower() else value + ", Kraków"
        return ""

    @staticmethod
    def _is_cancelled(text: str) -> bool:
        lowered = text.lower()
        folded = unicodedata.normalize("NFKD", lowered)
        return any(word in lowered or word in folded for word in CANCEL_WORDS)


def load_commissions(path: Path) -> list[Commission]:
    import json
    return [Commission(**item) for item in json.loads(path.read_text(encoding="utf-8"))]

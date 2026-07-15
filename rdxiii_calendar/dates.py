import re
from datetime import date

MONTHS = {
    "stycznia": 1, "styczen": 1, "styczeń": 1, "lutego": 2, "luty": 2,
    "marca": 3, "marzec": 3, "kwietnia": 4, "kwiecien": 4, "kwiecień": 4,
    "maja": 5, "maj": 5, "czerwca": 6, "czerwiec": 6, "lipca": 7, "lipiec": 7,
    "sierpnia": 8, "sierpien": 8, "sierpień": 8,
    "wrzesnia": 9, "września": 9, "wrzesien": 9, "wrzesień": 9,
    "pazdziernika": 10, "października": 10, "pazdziernik": 10, "październik": 10,
    "listopada": 11, "listopad": 11, "grudnia": 12, "grudzien": 12, "grudzień": 12,
}
NUMERIC_DATE = re.compile(r"(?<!\d)(\d{1,2})\s*[.\-/ ]\s*(\d{1,2})\s*[.\-/ ]\s*(\d{4})(?!\d)")
ISO_DATE = re.compile(r"(?<!\d)(\d{4})-(\d{1,2})-(\d{1,2})(?!\d)")
WORD_DATE = re.compile(r"(?<!\d)(\d{1,2})\s+(" + "|".join(sorted(map(re.escape, MONTHS), key=len, reverse=True)) + r")\s+(\d{4})(?:\s*r\.?)?", re.I)


def extract_dates(text: str, meeting_year: int | None = None) -> list[date]:
    """Rozpoznaje daty mimo brakujących kropek i polskich nazw miesięcy."""
    found: list[tuple[int, date]] = []
    clean = text.replace("\u00a0", " ").replace("\u202f", " ")

    def add(position: int, year: int, month: int, day: int) -> None:
        if meeting_year and abs(year - meeting_year) == 1:
            year = meeting_year
        try:
            value = date(year, month, day)
        except ValueError:
            return
        if (position, value) not in found:
            found.append((position, value))

    for match in ISO_DATE.finditer(clean):
        add(match.start(), int(match[1]), int(match[2]), int(match[3]))
    for match in NUMERIC_DATE.finditer(clean):
        add(match.start(), int(match[3]), int(match[2]), int(match[1]))
    for match in WORD_DATE.finditer(clean):
        add(match.start(), int(match[3]), MONTHS[match[2].lower()], int(match[1]))
    return [value for _, value in sorted(found)]


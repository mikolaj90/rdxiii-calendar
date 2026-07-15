# Komisje RD XIII – kalendarz

Automatyczny kalendarz posiedzeń komisji Rady Dzielnicy XIII Podgórze. Skrypt codziennie odczytuje strony komisji w BIP Krakowa, pobiera PDF-y „Zwołanie posiedzenia” i generuje kalendarz iCalendar.

## Zasady

- obejmuje 11 komisji i posiedzenia od 15 lipca 2026 r.;
- data jest odczytywana ze strony BIP i potwierdzana w PDF-ie;
- godzina oraz lokalizacja pochodzą z PDF-u;
- posiedzenie trwa domyślnie 60 minut;
- alarmy są ustawione 24 godziny oraz 1 godzinę wcześniej;
- skrypt zatrzymuje aktualizację przy niejednoznacznej dacie lub godzinie;
- kalendarz aktualizuje się codziennie około 15:30 czasu polskiego.

## Uruchomienie ręczne

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest
pytest -q
python generate_calendar.py
```

Wynik zostanie zapisany jako `docs/komisje-rd-xiii.ics` i opublikowany przez GitHub Pages.

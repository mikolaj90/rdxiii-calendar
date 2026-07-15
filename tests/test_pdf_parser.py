from datetime import date, time
from rdxiii_calendar.bip import BipClient

SAMPLE = """Kraków, dnia 30 czerwca 2026 r.
Uprzejmie informuję, iż zwołuję posiedzenie Komisji, które odbędzie się:
3 lipca 2026 r. (piątek)
o godzinie 19:00
w siedzibie Rady Dzielnicy XIII Podgórze, Rynek Podgórski 1 w Krakowie."""


def test_date_near_time_wins_over_document_date():
    assert BipClient._date_and_time(SAMPLE, 2026) == (date(2026, 7, 3), time(19, 0))


def test_location_is_normalized():
    assert BipClient._location(SAMPLE) == "Rynek Podgórski 1, Kraków"


from datetime import date, time
from rdxiii_calendar.bip import Commission, Meeting
from rdxiii_calendar.calendar import build_calendar


def test_calendar_contains_title_duration_location_and_alarms():
    commission = Commission(175977, "TORD", "Komisja Transportu i Organizacji Ruchu Drogowego Rady Dzielnicy XIII Podgórze", "🚌")
    meeting = Meeting(commission, "32/2026", date(2026, 7, 22), time(17, 30), "Rynek Podgórski 1, Kraków", "https://example/page", "https://example/card")
    text = build_calendar([meeting]).decode("utf-8").replace("\r\n ", "")
    assert "SUMMARY:🚌 TORD" in text
    assert "DTSTART;TZID=Europe/Warsaw:20260722T173000" in text
    assert "DTEND;TZID=Europe/Warsaw:20260722T183000" in text
    assert "LOCATION:Rynek Podgórski 1\\, Kraków" in text
    assert text.count("BEGIN:VALARM") == 2


def test_unchanged_calendar_is_byte_for_byte_stable():
    commission = Commission(175977, "TORD", "Komisja Transportu i Organizacji Ruchu Drogowego Rady Dzielnicy XIII Podgórze", "🚌")
    meeting = Meeting(commission, "32/2026", date(2026, 7, 22), time(17, 30), "Rynek Podgórski 1, Kraków", "https://example/page", "https://example/card")
    first = build_calendar([meeting])
    second = build_calendar([meeting], previous=first)
    assert second == first

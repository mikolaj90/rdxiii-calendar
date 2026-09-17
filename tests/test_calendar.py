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


def test_provisional_meeting_is_all_day_without_time_based_alarms():
    commission = Commission(
        175953,
        "Praworządności i Bezpieczeństwa",
        "Komisja Praworządności i Bezpieczeństwa Rady Dzielnicy XIII Podgórze",
        "👮‍♂️",
    )
    meeting = Meeting(
        commission,
        "33/2026",
        date(2026, 9, 21),
        None,
        "",
        "https://example/page",
        "https://example/page",
        provisional=True,
    )

    text = build_calendar([meeting]).decode("utf-8").replace("\r\n ", "")

    assert "SUMMARY:⚠️ Praworządności i Bezpieczeństwa – godzina nieznana" in text
    assert "DTSTART;VALUE=DATE:20260921" in text
    assert "DTEND;VALUE=DATE:20260922" in text
    assert "BIP nie opublikował jeszcze zwołania z godziną i miejscem posied" in text
    assert "BEGIN:VALARM" not in text


def test_provisional_and_timed_versions_use_the_same_uid():
    commission = Commission(175953, "Komisja", "Komisja", "👮‍♂️")
    provisional = Meeting(
        commission, "33/2026", date(2026, 9, 21), None, "",
        "https://example/page", "https://example/page", provisional=True,
    )
    timed = Meeting(
        commission, "33/2026", date(2026, 9, 21), time(18, 0),
        "Rynek Podgórski 1, Kraków", "https://example/page", "https://example/card",
    )

    assert provisional.uid == timed.uid

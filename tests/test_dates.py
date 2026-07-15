from datetime import date
import pytest
from rdxiii_calendar.dates import extract_dates


@pytest.mark.parametrize("value", [
    "01.01.2026", "1.1.2026", "01 01 2026", "01.01 2026", "01 01.2026",
    "1 stycznia 2026", "1 stycznia 2026 r.", "2026-01-01",
])
def test_supported_date_formats(value):
    assert date(2026, 1, 1) in extract_dates(value)


def test_meeting_number_year_corrects_single_year_typo():
    assert extract_dates("22.07.2025", meeting_year=2026) == [date(2026, 7, 22)]


def test_archive_year_is_not_rewritten_without_evidence():
    assert extract_dates("22.07.2025") == [date(2025, 7, 22)]


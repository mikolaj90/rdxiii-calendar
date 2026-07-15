from datetime import date

from bs4 import BeautifulSoup

from rdxiii_calendar.bip import SessionClient


def test_year_links_are_not_hardcoded():
    soup = BeautifulSoup('<a href="/?dok_id=1">2026</a><a href="/?dok_id=2">2027</a>', "html.parser")
    years = {int(a.get_text(strip=True)) for a in soup.find_all("a")}
    assert years == {2026, 2027}


def test_session_location_and_duration():
    text = "31 sierpnia 2026 - godz. 18:00, siedziba Rady Dzielnicy, ul. Rynek Podgórski 1"
    assert SessionClient._location(text).endswith(", Kraków")

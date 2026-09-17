from datetime import date

from bs4 import BeautifulSoup

from rdxiii_calendar.bip import BipClient, Commission


class StubBipClient(BipClient):
    def __init__(self, html: str) -> None:
        self.html = html

    def get(self, url: str):
        class Response:
            text = self.html

        return Response()


def test_missing_convocation_link_creates_nonblocking_all_day_meeting():
    html = """
    <table><tr>
      <td>33/2026</td><td>21.09.2026</td>
      <td>Zwołanie posiedzenia - Protokół z posiedzenia -
          <a href="/lista">Lista obecności</a></td>
    </tr></table>
    """
    commission = Commission(175953, "Komisja", "Komisja", "👮‍♂️")

    meetings, problems = StubBipClient(html).meetings(commission, date(2026, 7, 15))

    assert len(meetings) == 1
    assert meetings[0].number == "33/2026"
    assert meetings[0].meeting_date == date(2026, 9, 21)
    assert meetings[0].start_time is None
    assert meetings[0].provisional is True
    assert len(problems) == 1
    assert problems[0].blocking is False
    assert "Brak linku do zwołania dla 33/2026" in str(problems[0])


def test_parse_problem_remains_blocking_for_missing_date():
    soup = BeautifulSoup(
        '<table><tr><td>Zwołanie posiedzenia <a href="/z">Zwołanie posiedzenia</a></td></tr></table>',
        "html.parser",
    )
    assert BipClient._meeting_blocks(soup)

    commission = Commission(1, "Komisja", "Komisja", "X")
    meetings, problems = StubBipClient(str(soup)).meetings(commission, date(2026, 7, 15))

    assert meetings == []
    assert len(problems) == 1
    assert problems[0].blocking is True

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from icalendar import Alarm, Calendar, Event

from .bip import Meeting

WARSAW = ZoneInfo("Europe/Warsaw")


def build_calendar(meetings: list[Meeting]) -> bytes:
    calendar = Calendar()
    calendar.add("prodid", "-//mikolaj90//Komisje RD XIII//PL")
    calendar.add("version", "2.0")
    calendar.add("calscale", "GREGORIAN")
    calendar.add("method", "PUBLISH")
    calendar.add("x-wr-calname", "Komisje RD XIII")
    calendar.add("x-wr-timezone", "Europe/Warsaw")
    now = datetime.now(tz=ZoneInfo("UTC"))
    for meeting in sorted(meetings, key=lambda item: item.starts_at):
        event = Event()
        title = f"{meeting.commission.emoji} {meeting.commission.name}"
        if meeting.cancelled:
            title = f"ODWOŁANE – {title}"
            event.add("status", "CANCELLED")
        event.add("uid", meeting.uid)
        event.add("summary", title)
        event.add("dtstamp", now)
        event.add("dtstart", meeting.starts_at.replace(tzinfo=WARSAW))
        event.add("dtend", meeting.ends_at.replace(tzinfo=WARSAW))
        if meeting.location:
            event.add("location", meeting.location)
        event.add("description", (
            f"{meeting.commission.full_name}\n"
            f"Numer posiedzenia: {meeting.number or 'nie podano'}\n\n"
            f"Zwołanie posiedzenia: {meeting.attachment_card}\n"
            f"Strona komisji: {meeting.source_page}"
        ))
        event.add("url", meeting.attachment_card)
        for delta, label in ((timedelta(hours=-24), "Komisja jutro"), (timedelta(hours=-1), "Komisja za godzinę")):
            alarm = Alarm()
            alarm.add("action", "DISPLAY")
            alarm.add("description", label)
            alarm.add("trigger", delta)
            event.add_component(alarm)
        calendar.add_component(event)
    return calendar.to_ical()


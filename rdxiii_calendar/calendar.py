from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from icalendar import Alarm, Calendar, Event

from .bip import Meeting

WARSAW = ZoneInfo("Europe/Warsaw")


def _value(component, key):
    value = component.get(key)
    if value is None:
        return None
    decoded = value.dt if hasattr(value, "dt") else value
    return decoded.isoformat() if hasattr(decoded, "isoformat") else str(decoded)


def _signature(event: Event) -> tuple:
    alarms = []
    for component in event.subcomponents:
        if component.name == "VALARM":
            alarms.append((_value(component, "ACTION"), _value(component, "DESCRIPTION"), _value(component, "TRIGGER")))
    return tuple(_value(event, key) for key in (
        "SUMMARY", "DTSTART", "DTEND", "LOCATION", "DESCRIPTION", "URL", "STATUS"
    )) + (tuple(alarms),)


def build_calendar(meetings: list[Meeting], previous: bytes | None = None) -> bytes:
    calendar = Calendar()
    calendar.add("prodid", "-//mikolaj90//Komisje RD XIII//PL")
    calendar.add("version", "2.0")
    calendar.add("calscale", "GREGORIAN")
    calendar.add("method", "PUBLISH")
    calendar.add("x-wr-calname", "Komisje RD XIII")
    calendar.add("x-wr-timezone", "Europe/Warsaw")
    now = datetime.now(tz=ZoneInfo("UTC")).replace(microsecond=0)
    previous_events = {}
    if previous:
        old_calendar = Calendar.from_ical(previous)
        previous_events = {
            str(component.get("UID")): component
            for component in old_calendar.walk("VEVENT")
            if component.get("UID")
        }
    for meeting in sorted(meetings, key=lambda item: item.starts_at):
        event = Event()
        title = f"{meeting.commission.emoji} {meeting.commission.name}"
        if meeting.cancelled:
            title = f"ODWOŁANE – {title}"
            event.add("status", "CANCELLED")
        event.add("uid", meeting.uid)
        event.add("summary", title)
        event.add("dtstart", meeting.starts_at.replace(tzinfo=WARSAW))
        event.add("dtend", meeting.ends_at.replace(tzinfo=WARSAW))
        if meeting.location:
            event.add("location", meeting.location)
        if meeting.kind == "session":
            description = (
                f"{meeting.commission.full_name}\n\n"
                f"Szczegóły sesji: {meeting.attachment_card}\n"
                f"Terminy sesji: {meeting.source_page}"
            )
        else:
            description = (
                f"{meeting.commission.full_name}\n"
                f"Numer posiedzenia: {meeting.number or 'nie podano'}\n\n"
                f"Zwołanie posiedzenia: {meeting.attachment_card}\n"
                f"Strona komisji: {meeting.source_page}"
            )
        event.add("description", description)
        event.add("url", meeting.attachment_card)
        for delta, label in ((timedelta(hours=-24), "Komisja jutro"), (timedelta(hours=-1), "Komisja za godzinę")):
            alarm = Alarm()
            alarm.add("action", "DISPLAY")
            alarm.add("description", label)
            alarm.add("trigger", delta)
            event.add_component(alarm)
        old_event = previous_events.get(meeting.uid)
        if old_event is not None and _signature(old_event) == _signature(event):
            event.add("dtstamp", old_event.decoded("DTSTAMP"))
        else:
            event.add("dtstamp", now)
        calendar.add_component(event)
    return calendar.to_ical()

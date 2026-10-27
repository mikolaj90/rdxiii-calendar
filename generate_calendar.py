#!/usr/bin/env python3
import argparse
import logging
from datetime import date
from pathlib import Path

from rdxiii_calendar.bip import BipClient, BipFetchError, SessionClient, load_commissions
from rdxiii_calendar.calendar import build_calendar


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", type=date.fromisoformat, default=date(2026, 7, 15))
    parser.add_argument("--output", type=Path, default=Path("docs/komisje-rd-xiii.ics"))
    parser.add_argument("--problems-output", type=Path, default=Path("generation-problems.txt"))
    args = parser.parse_args()
    args.problems_output.unlink(missing_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    client = BipClient()
    meetings = []
    blocking_problems = []
    preserve_source_ids = set()
    try:
        for commission in load_commissions(Path("config/commissions.json")):
            found, problems = client.meetings(commission, args.since)
            meetings.extend(found)
            for problem in problems:
                message = f"{commission.name}: {problem}"
                if problem.blocking:
                    blocking_problems.append(message)
                    preserve_source_ids.add(commission.document_id)
                else:
                    logging.warning(message)
            logging.info("%s: %d posiedzeń", commission.name, len(found))
        sessions, session_problems = SessionClient().meetings(args.since)
    except BipFetchError as exc:
        logging.error("Nie zaktualizowano kalendarza – %s", exc)
        return 2
    meetings.extend(sessions)
    for problem in session_problems:
        message = f"Sesje: {problem}"
        if problem.blocking:
            blocking_problems.append(message)
            preserve_source_ids.add(SessionClient.SESSION.document_id)
        else:
            logging.warning(message)
    logging.info("Sesje Rady Dzielnicy XIII: %d terminów", len(sessions))
    if blocking_problems:
        diagnosis = (
            "Częściowa aktualizacja – pominięto niejednoznaczne rekordy:\n"
            + "\n".join(f"- {problem}" for problem in blocking_problems)
        )
        logging.error(diagnosis)
        args.problems_output.write_text(diagnosis + "\n", encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    previous = args.output.read_bytes() if args.output.exists() else None
    args.output.write_bytes(build_calendar(
        meetings,
        previous=previous,
        preserve_source_ids=preserve_source_ids,
    ))
    logging.info("Zapisano %d wydarzeń w %s", len(meetings), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
import argparse
import logging
from datetime import date
from pathlib import Path

from rdxiii_calendar.bip import BipClient, load_commissions
from rdxiii_calendar.calendar import build_calendar


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", type=date.fromisoformat, default=date(2026, 7, 15))
    parser.add_argument("--output", type=Path, default=Path("docs/komisje-rd-xiii.ics"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    client = BipClient()
    meetings = []
    warnings = []
    for commission in load_commissions(Path("config/commissions.json")):
        found, problems = client.meetings(commission, args.since)
        meetings.extend(found)
        warnings.extend(f"{commission.name}: {item}" for item in problems)
        logging.info("%s: %d posiedzeń", commission.name, len(found))
    if warnings:
        raise SystemExit("Nie zaktualizowano kalendarza z powodu niejednoznacznych danych:\n" + "\n".join(warnings))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(build_calendar(meetings))
    logging.info("Zapisano %d wydarzeń w %s", len(meetings), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Estimate Kaggle daily submission usage for the PTCG ABC simulation competition.

Kaggle's CLI/SDK exposes maxDailySubmissions in competition metadata, but the
observed API does not expose a direct "remaining submissions" field. This helper
therefore counts submissions whose timestamps fall on the current UTC date.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from typing import Any

from kaggle.api.kaggle_api_extended import KaggleApi


def get_attr(obj: Any, *names: str) -> Any:
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


def as_utc_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    raise TypeError(f"unsupported date type: {type(value).__name__}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("competition", nargs="?", default="pokemon-tcg-ai-battle")
    parser.add_argument("--max-daily", type=int, default=5)
    parser.add_argument(
        "--utc-date",
        default=datetime.now(timezone.utc).date().isoformat(),
        help="UTC date to count, YYYY-MM-DD. Defaults to today in UTC.",
    )
    args = parser.parse_args()

    target_date = datetime.fromisoformat(args.utc_date).date()

    api = KaggleApi()
    api.authenticate()
    submissions = api.competition_submissions(args.competition)

    todays = []
    for sub in submissions:
        dt = as_utc_datetime(get_attr(sub, "date", "_date"))
        if dt.date() == target_date:
            todays.append((dt, sub))

    todays.sort(key=lambda item: item[0])
    used = len(todays)
    remaining = max(0, args.max_daily - used)
    next_reset = datetime.combine(target_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)

    print(f"competition={args.competition}")
    print(f"utc_date={target_date.isoformat()}")
    print(f"max_daily_submissions={args.max_daily}")
    print(f"used_today_utc={used}")
    print(f"estimated_remaining={remaining}")
    print(f"next_reset_utc={next_reset.isoformat().replace('+00:00', 'Z')}")
    print("submissions_today_utc:")
    for dt, sub in todays:
        ref = get_attr(sub, "ref", "_ref")
        file_name = get_attr(sub, "file_name", "_file_name")
        status = get_attr(sub, "status", "_status")
        score = get_attr(sub, "public_score", "_public_score")
        print(
            f"- {dt.isoformat().replace('+00:00', 'Z')} ref={ref} "
            f"status={status} publicScore={score} file={file_name}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

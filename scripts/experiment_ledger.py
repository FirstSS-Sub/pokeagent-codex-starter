#!/usr/bin/env python3
"""Append and summarize local experiment results for looped agent research.

The ledger defaults to `runs/experiment_ledger.jsonl`, which is intentionally
ignored. Keep raw battle outputs and candidate packages local; commit only the
sanitized scripts/docs.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import sys
from typing import Any


DEFAULT_LEDGER = Path("runs/experiment_ledger.jsonl")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def iter_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open() as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
    return rows


def winrate(wins: int, losses: int, draws: int) -> float:
    decisive = wins + losses
    if decisive <= 0:
        return 0.0
    return wins / decisive


def append_manual(args: argparse.Namespace) -> int:
    row = {
        "schema_version": 1,
        "record_type": "eval_result",
        "created_at_utc": now_utc(),
        "profile_id": args.profile_id,
        "candidate": args.candidate,
        "baseline": args.baseline,
        "bucket": args.bucket,
        "bucket_ja": args.bucket_ja,
        "proxy_label": args.proxy_label,
        "proxy_role": args.proxy_role,
        "operator": args.operator,
        "games": args.games,
        "wins": args.wins,
        "losses": args.losses,
        "draws": args.draws,
        "errors_or_fallback_games": args.errors,
        "fallbacks": args.fallbacks,
        "fallback_rate": args.fallback_rate,
        "winrate_no_draws": winrate(args.wins, args.losses, args.draws),
        "weighted_score_component": args.weight * winrate(args.wins, args.losses, args.draws),
        "bucket_weight": args.weight,
        "decision": args.decision,
        "reason": args.reason,
    }
    append_jsonl(args.ledger, row)
    print(f"appended {args.ledger}")
    return 0


def init_ledger(args: argparse.Namespace) -> int:
    if args.ledger.exists() and not args.force:
        print(f"ledger already exists: {args.ledger}", file=sys.stderr)
        return 1
    header = {
        "schema_version": 1,
        "record_type": "ledger_header",
        "created_at_utc": now_utc(),
        "purpose": "PTCG ABC loop-engineering experiment ledger",
        "notes": [
            "Do not commit this ledger if it contains raw candidate paths, private notes, or local results.",
            "Use meta_eval_profile weights and holdout roles when deciding submissions.",
        ],
    }
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    args.ledger.write_text(json.dumps(header, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"initialized {args.ledger}")
    return 0


def summarize(args: argparse.Namespace) -> int:
    rows = [row for row in iter_rows(args.ledger) if row.get("record_type") == "eval_result"]
    if not rows:
        print(f"no eval_result rows in {args.ledger}")
        return 0

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        if args.profile_id and row.get("profile_id") != args.profile_id:
            continue
        key = (str(row.get("candidate")), str(row.get("bucket")))
        grouped.setdefault(key, []).append(row)

    print(f"ledger={args.ledger}")
    if args.profile_id:
        print(f"profile_id={args.profile_id}")
    print("candidate bucket games wins losses draws wr fallback_rate weighted_component")
    candidate_totals: dict[str, dict[str, float]] = {}
    for (candidate, bucket), items in sorted(grouped.items()):
        games = sum(int(item.get("games") or 0) for item in items)
        wins = sum(int(item.get("wins") or 0) for item in items)
        losses = sum(int(item.get("losses") or 0) for item in items)
        draws = sum(int(item.get("draws") or 0) for item in items)
        wr = winrate(wins, losses, draws)
        fallback_rates = [float(item.get("fallback_rate") or 0.0) for item in items]
        fallback_rate = statistics.mean(fallback_rates) if fallback_rates else 0.0
        weighted = sum(float(item.get("weighted_score_component") or 0.0) for item in items)
        print(
            f"{candidate} {bucket} {games} {wins} {losses} {draws} "
            f"{wr:.4f} {fallback_rate:.6f} {weighted:.5f}"
        )
        total = candidate_totals.setdefault(candidate, {"weighted": 0.0, "games": 0.0})
        total["weighted"] += weighted
        total["games"] += games

    print("\nweighted totals:")
    for candidate, total in sorted(candidate_totals.items(), key=lambda item: item[1]["weighted"], reverse=True):
        print(f"- {candidate}: weighted={total['weighted']:.5f} games={int(total['games'])}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=init_ledger)

    append = sub.add_parser("append")
    append.add_argument("--profile-id", required=True)
    append.add_argument("--candidate", required=True)
    append.add_argument("--baseline")
    append.add_argument("--bucket", required=True)
    append.add_argument("--bucket-ja", default="")
    append.add_argument("--proxy-label", required=True)
    append.add_argument("--proxy-role", default="unknown")
    append.add_argument("--operator", default="")
    append.add_argument("--games", type=int, required=True)
    append.add_argument("--wins", type=int, required=True)
    append.add_argument("--losses", type=int, required=True)
    append.add_argument("--draws", type=int, default=0)
    append.add_argument("--errors", type=int, default=0)
    append.add_argument("--fallbacks", type=int, default=0)
    append.add_argument("--fallback-rate", type=float, default=0.0)
    append.add_argument("--weight", type=float, default=0.0)
    append.add_argument("--decision", default="recorded")
    append.add_argument("--reason", default="")
    append.set_defaults(func=append_manual)

    summary = sub.add_parser("summary")
    summary.add_argument("--profile-id")
    summary.set_defaults(func=summarize)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

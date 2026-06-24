#!/usr/bin/env python3
"""Evaluate candidate agents against a meta-evaluation profile.

This runner connects:

- a `meta_eval_profile_*.json`,
- a local proxy map (`runs/eval_proxy_map.local.json`), and
- one or more candidate submission directories.

It can either print the matrix commands (`--dry-run`) or run them directly.
On macOS, use `--docker` so the official Linux `cg/libcg.so` can load.
Results are appended to `runs/experiment_ledger.jsonl`.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


DEFAULT_LEDGER = Path("runs/experiment_ledger.jsonl")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_label_path(raw: str) -> tuple[str, Path]:
    label, sep, path = raw.partition("=")
    if not sep or not label or not path:
        raise argparse.ArgumentTypeError("expected LABEL=PATH")
    return label, Path(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def repo_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def command_for_pair(
    candidate: Path,
    proxy: Path,
    candidate_label: str,
    proxy_label: str,
    games: int,
    max_steps: int,
    docker: bool,
) -> list[str]:
    inner = [
        "python",
        "scripts/eval_submission_pair.py",
        "--agent0",
        repo_rel(candidate),
        "--agent1",
        repo_rel(proxy),
        "--label0",
        candidate_label,
        "--label1",
        proxy_label,
        "--games",
        str(games),
        "--max-steps",
        str(max_steps),
    ]
    if not docker:
        return inner
    return [
        "docker",
        "run",
        "--rm",
        "-i",
        "--platform",
        "linux/amd64",
        "-v",
        f"{Path.cwd()}:/work",
        "-w",
        "/work",
        "python:3.11-slim",
        *inner,
    ]


SUMMARY_RE = re.compile(r"games=(?P<games>\d+) wins=(?P<wins>\d+) losses=(?P<losses>\d+) draws=(?P<draws>\d+) errors=(?P<errors>\d+)")
FALLBACK_RE = re.compile(r"fallbacks=(?P<fallbacks>\d+) decisions=(?P<decisions>\d+) fallback_rate=(?P<fallback_rate>[0-9.]+)")
WR_RE = re.compile(r"winrate_no_draws=(?P<wr>[0-9.]+)")


def parse_eval_stdout(stdout: str) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for line in stdout.splitlines():
        if m := SUMMARY_RE.search(line):
            summary.update({key: int(value) for key, value in m.groupdict().items()})
        if m := FALLBACK_RE.search(line):
            summary["fallbacks"] = int(m.group("fallbacks"))
            summary["decisions"] = int(m.group("decisions"))
            summary["fallback_rate"] = float(m.group("fallback_rate"))
        if m := WR_RE.search(line):
            summary["winrate_no_draws"] = float(m.group("wr"))
    if "games" not in summary:
        raise ValueError("could not parse eval summary")
    summary.setdefault("fallbacks", 0)
    summary.setdefault("decisions", 0)
    summary.setdefault("fallback_rate", 0.0)
    return summary


def profile_buckets(profile: dict[str, Any], include_roles: set[str] | None, limit: int | None) -> list[dict[str, Any]]:
    rows = []
    for bucket in profile.get("buckets", []):
        if include_roles and bucket.get("role") not in include_roles:
            continue
        rows.append(bucket)
    rows.sort(key=lambda item: float(item.get("weight") or 0.0), reverse=True)
    if limit is not None:
        rows = rows[:limit]
    return rows


def run_matrix(args: argparse.Namespace) -> int:
    profile = load_json(args.profile)
    proxy_map = load_json(args.proxy_map)
    profile_id = str(profile.get("profile_id") or args.profile.stem)
    proxy_buckets = proxy_map.get("buckets", {})
    candidates = [parse_label_path(item) for item in args.candidate]
    include_roles = set(args.include_role or []) or None
    buckets = profile_buckets(profile, include_roles, args.limit_buckets)

    planned: list[tuple[dict[str, Any], str, dict[str, Any], str, Path, str, Path, int]] = []
    for bucket in buckets:
        bucket_key = str(bucket.get("key"))
        proxies = proxy_buckets.get(bucket_key, [])
        if not proxies:
            if args.require_all_buckets:
                print(f"missing proxies for bucket: {bucket_key}", file=sys.stderr)
                return 2
            continue
        proxy_count = len(proxies)
        for candidate_label, candidate_path in candidates:
            for proxy in proxies:
                planned.append(
                    (
                        bucket,
                        candidate_label,
                        proxy,
                        str(proxy.get("label") or bucket_key),
                        candidate_path,
                        str(proxy.get("role") or bucket.get("role") or "unknown"),
                        Path(str(proxy.get("path"))),
                        proxy_count,
                    )
                )

    if not planned:
        print("no evaluation pairs planned", file=sys.stderr)
        return 1

    print(f"profile_id={profile_id} pairs={len(planned)} games_each={args.games}")
    for bucket, candidate_label, proxy, proxy_label, candidate_path, proxy_role, proxy_path, proxy_count in planned:
        bucket_weight = float(bucket.get("weight") or 0.0)
        proxy_weight = bucket_weight / max(1, proxy_count)
        cmd = command_for_pair(
            candidate_path,
            proxy_path,
            candidate_label,
            proxy_label,
            args.games,
            args.max_steps,
            args.docker,
        )
        print(
            f"PAIR candidate={candidate_label} bucket={bucket.get('key')} "
            f"proxy={proxy_label} role={proxy_role} "
            f"bucket_weight={bucket_weight:.5f} proxy_weight={proxy_weight:.5f}"
        )
        if args.dry_run:
            print("  " + " ".join(cmd))
            continue

        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.stdout:
            print(proc.stdout, end="")
        if proc.stderr:
            print(proc.stderr, end="", file=sys.stderr)
        try:
            parsed = parse_eval_stdout(proc.stdout)
        except ValueError as exc:
            parsed = {
                "games": args.games,
                "wins": 0,
                "losses": 0,
                "draws": 0,
                "errors": args.games,
                "fallbacks": 0,
                "decisions": 0,
                "fallback_rate": 1.0,
                "parse_error": str(exc),
            }

        row = {
            "schema_version": 1,
            "record_type": "eval_result",
            "created_at_utc": now_utc(),
            "profile_id": profile_id,
            "candidate": candidate_label,
            "bucket": bucket.get("key"),
            "bucket_ja": bucket.get("ja_name"),
            "bucket_role": bucket.get("role"),
            "bucket_weight": bucket_weight,
            "proxy_weight": proxy_weight,
            "proxy_label": proxy_label,
            "proxy_role": proxy_role,
            "proxy_path": repo_rel(proxy_path),
            "candidate_path": repo_rel(candidate_path),
            "games": int(parsed.get("games") or args.games),
            "wins": int(parsed.get("wins") or 0),
            "losses": int(parsed.get("losses") or 0),
            "draws": int(parsed.get("draws") or 0),
            "errors_or_fallback_games": int(parsed.get("errors") or 0),
            "fallbacks": int(parsed.get("fallbacks") or 0),
            "fallback_rate": float(parsed.get("fallback_rate") or 0.0),
            "winrate_no_draws": float(parsed.get("winrate_no_draws") or 0.0),
            "weighted_score_component": proxy_weight * float(parsed.get("winrate_no_draws") or 0.0),
            "returncode": proc.returncode,
            "decision": "recorded" if proc.returncode == 0 else "failed_eval",
        }
        if "parse_error" in parsed:
            row["parse_error"] = parsed["parse_error"]
        append_jsonl(args.ledger, row)
        if proc.returncode != 0 and args.stop_on_failure:
            return proc.returncode
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--proxy-map", required=True, type=Path)
    parser.add_argument("--candidate", action="append", required=True, help="LABEL=PATH")
    parser.add_argument("--games", type=int, default=100)
    parser.add_argument("--max-steps", type=int, default=5000)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--include-role", action="append", help="Only evaluate buckets with this role; repeatable.")
    parser.add_argument("--limit-buckets", type=int)
    parser.add_argument("--docker", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--require-all-buckets", action="store_true")
    parser.add_argument("--stop-on-failure", action="store_true")
    args = parser.parse_args()
    return run_matrix(args)


if __name__ == "__main__":
    raise SystemExit(main())

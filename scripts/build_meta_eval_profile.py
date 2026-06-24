#!/usr/bin/env python3
"""Build a versioned meta-evaluation profile for PTCG ABC agent research.

The output is intentionally written under ignored local storage by default
(`runs/`) because it can contain time-sensitive ladder observations. The script
itself only uses public/community sources and optional local summary CSVs.

The profile is not a claim about the hidden evaluation distribution. It is a
versioned validation *hypothesis* used to prevent loss-chasing and local
overfitting during looped research.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any
from urllib.request import Request, urlopen


DEFAULT_API_BASE = "https://ptcg-ladder-meta.vercel.app/api"

DEFAULT_SOURCE_WEIGHTS = {
    "public_meta": 0.45,
    "top_teams": 0.25,
    "live_replays": 0.20,
    "loss_clusters": 0.10,
}

CORE_BUCKETS = {
    "Alakazam",
    "Dudunsparce",
    "Hop's Trevenant",
    "Mega Lucario ex",
    "Dragapult ex",
}

COVERAGE_BUCKETS = {
    "Mega Starmie ex",
    "Mega Froslass ex",
    "Chandelure",
    "Team Rocket's Spidops",
    "Walrein",
    "Crustle",
    "Iono's Bellibolt ex",
    "Iono’s Bellibolt ex",
    "Thwackey",
}

ARCHETYPE_JA: dict[str, str] = {
    "Alakazam": "フーディン",
    "Dudunsparce": "ノココッチ",
    "Hop's Trevenant": "ホップのオーロット",
    "Mega Lucario ex": "メガルカリオex",
    "Dragapult ex": "ドラパルトex",
    "Mega Starmie ex": "メガスターミーex",
    "Mega Froslass ex": "メガユキメノコex",
    "Chandelure": "シャンデラ",
    "Team Rocket's Spidops": "ロケット団のワナイダー",
    "Walrein": "トドゼルガ",
    "Crustle": "イワパレス",
    "Iono's Bellibolt ex": "ナンジャモのハラバリーex",
    "Iono’s Bellibolt ex": "ナンジャモのハラバリーex",
    "Thwackey": "バチンキー",
    "Mega Abomasnow ex": "メガユキノオーex",
    "Mega Kangaskhan ex": "メガガルーラex",
    "Cinderace": "エースバーン",
    "Other": "その他",
}

# Local replay summaries in this repo use official Japanese names. Normalize
# them to the public meta API's English archetype keys.
LOCAL_ARCH_TO_BUCKET: dict[str, str] = {
    "フーディン系": "Alakazam",
    "ノココッチ系": "Dudunsparce",
    "ホップのオーロット系": "Hop's Trevenant",
    "ホップのボクレー/ホップのオーロット系": "Hop's Trevenant",
    "メガルカリオex/ソルロック/ルナトーン系": "Mega Lucario ex",
    "ドラパルトex系": "Dragapult ex",
    "メガユキメノコex/メガスターミーex系": "Mega Froslass ex",
    "メガユキメノコex系": "Mega Froslass ex",
    "メガスターミーex系": "Mega Starmie ex",
    "トドゼルガ/スボミー系": "Walrein",
    "イワパレス/闘系": "Crustle",
    "シャンデラ/キュワワー系": "Chandelure",
    "ナンジャモのハラバリーex系": "Iono's Bellibolt ex",
    "エースバーン/クラッシュハンマー系": "Cinderace",
    "その他": "Other",
}


@dataclass
class BucketSignals:
    public_share: float = 0.0
    public_count: int = 0
    public_field_wr: float | None = None
    public_field_n: int | None = None
    top_team_share: float = 0.0
    top_team_count: int = 0
    live_share: float = 0.0
    live_count: int = 0
    live_losses: int = 0
    loss_share: float = 0.0
    notes: list[str] = field(default_factory=list)


def fetch_json(url: str, timeout: int = 30) -> dict[str, Any]:
    req = Request(url, headers={"User-Agent": "pokeagent-codex-starter/1.0"})
    with urlopen(req, timeout=timeout) as res:
        return json.load(res)


def normalize(values: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, value) for value in values.values())
    if total <= 0:
        return {key: 0.0 for key in values}
    return {key: max(0.0, value) / total for key, value in values.items()}


def normalized_weight_config(raw: str | None) -> dict[str, float]:
    weights = dict(DEFAULT_SOURCE_WEIGHTS)
    if raw:
        for item in raw.split(","):
            if not item.strip():
                continue
            name, _, value = item.partition("=")
            if name not in weights or not value:
                raise ValueError(f"unknown or malformed source weight: {item!r}")
            weights[name] = float(value)
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("source weights must sum to a positive value")
    return {key: value / total for key, value in weights.items()}


def add_public_meta(
    buckets: dict[str, BucketSignals],
    strategies: list[dict[str, Any]],
    min_public_share: float,
) -> None:
    for row in strategies:
        name = str(row.get("archetype", ""))
        share = float(row.get("share") or 0.0)
        if share < min_public_share and name not in CORE_BUCKETS and name not in COVERAGE_BUCKETS:
            continue
        b = buckets.setdefault(name, BucketSignals())
        b.public_share = share
        b.public_count = int(row.get("count") or 0)
        b.public_field_wr = row.get("field_wr")
        b.public_field_n = row.get("field_n")


def add_top_team_meta(
    buckets: dict[str, BucketSignals],
    teams: list[dict[str, Any]],
    top_n: int,
) -> None:
    counts: dict[str, float] = {}
    selected = teams[:top_n]
    for team in selected:
        name = str(team.get("modal_archetype") or "")
        if not name:
            continue
        counts[name] = counts.get(name, 0.0) + 1.0
    shares = normalize(counts)
    for name, share in shares.items():
        b = buckets.setdefault(name, BucketSignals())
        b.top_team_share = share
        b.top_team_count = int(counts[name])


def latest_csv_by_mtime(paths: list[str]) -> list[Path]:
    resolved: list[Path] = []
    for item in paths:
        path = Path(item)
        if path.is_dir():
            resolved.extend(sorted(path.glob("**/*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)[:1])
        elif path.exists():
            resolved.append(path)
    return resolved


def add_live_replay_meta(
    buckets: dict[str, BucketSignals],
    csv_paths: list[Path],
) -> None:
    counts: dict[str, float] = {}
    losses: dict[str, float] = {}
    for path in csv_paths:
        with path.open(newline="") as f:
            for row in csv.DictReader(f):
                local_arch = (row.get("arch") or "").strip()
                bucket = LOCAL_ARCH_TO_BUCKET.get(local_arch, local_arch or "Other")
                counts[bucket] = counts.get(bucket, 0.0) + 1.0
                if (row.get("result") or "").strip().lower() == "loss":
                    losses[bucket] = losses.get(bucket, 0.0) + 1.0
    count_shares = normalize(counts)
    loss_shares = normalize(losses)
    for name in set(count_shares) | set(loss_shares):
        b = buckets.setdefault(name, BucketSignals())
        b.live_share = count_shares.get(name, 0.0)
        b.live_count = int(counts.get(name, 0.0))
        b.live_losses = int(losses.get(name, 0.0))
        b.loss_share = loss_shares.get(name, 0.0)


def bucket_role(name: str, signals: BucketSignals) -> str:
    if name in CORE_BUCKETS:
        return "core"
    if signals.live_losses > 0:
        return "loss_cluster"
    if name in COVERAGE_BUCKETS or signals.top_team_share > 0:
        return "coverage_holdout"
    return "other"


def degradation_limits(role: str) -> dict[str, float] | None:
    if role == "core":
        return {"max_drop_vs_champion_pp": 1.5}
    if role == "loss_cluster":
        return {"max_drop_vs_champion_pp": 1.0, "target_gain_vs_champion_pp": 3.0}
    if role == "coverage_holdout":
        return {"max_catastrophic_drop_vs_champion_pp": 5.0}
    return None


def build_profile(args: argparse.Namespace) -> dict[str, Any]:
    source_weights = normalized_weight_config(args.source_weights)
    fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    sources: dict[str, Any] = {
        "source_weights": source_weights,
        "public_meta_api": args.api_base,
        "live_summary_csv": [],
        "caveat": "Observed public surface only; not the hidden evaluation distribution.",
    }

    buckets: dict[str, BucketSignals] = {}

    if not args.no_fetch:
        strategies_payload = fetch_json(f"{args.api_base.rstrip('/')}/strategies")
        teams_payload = fetch_json(f"{args.api_base.rstrip('/')}/teams?limit={args.top_teams}")
        strategies = strategies_payload.get("data", {}).get("strategies", [])
        teams = teams_payload.get("data", {}).get("teams", [])
        sources["strategies_generated_at"] = strategies_payload.get("generated_at")
        sources["teams_generated_at"] = teams_payload.get("generated_at")
        sources["snapshot_id"] = strategies_payload.get("data", {}).get("snapshot_id")
        add_public_meta(buckets, strategies, args.min_public_share)
        add_top_team_meta(buckets, teams, args.top_teams)

    csv_paths = latest_csv_by_mtime(args.live_summary_csv)
    if csv_paths:
        sources["live_summary_csv"] = [str(path) for path in csv_paths]
        add_live_replay_meta(buckets, csv_paths)

    # Ensure the expected core and coverage buckets exist even if the current
    # public snapshot omits them.
    for name in CORE_BUCKETS | COVERAGE_BUCKETS:
        buckets.setdefault(name, BucketSignals())

    public = {name: sig.public_share for name, sig in buckets.items()}
    top = {name: sig.top_team_share for name, sig in buckets.items()}
    live = {name: sig.live_share for name, sig in buckets.items()}
    loss = {name: sig.loss_share for name, sig in buckets.items()}

    combined_raw: dict[str, float] = {}
    for name in buckets:
        combined_raw[name] = (
            source_weights["public_meta"] * public.get(name, 0.0)
            + source_weights["top_teams"] * top.get(name, 0.0)
            + source_weights["live_replays"] * live.get(name, 0.0)
            + source_weights["loss_clusters"] * loss.get(name, 0.0)
        )
    combined = normalize(combined_raw)

    bucket_rows = []
    for name, weight in sorted(combined.items(), key=lambda item: item[1], reverse=True):
        sig = buckets[name]
        if weight < args.min_output_weight and name not in CORE_BUCKETS and name not in COVERAGE_BUCKETS:
            continue
        role = bucket_role(name, sig)
        bucket_rows.append(
            {
                "key": name,
                "ja_name": ARCHETYPE_JA.get(name, name),
                "role": role,
                "weight": weight,
                "signals": {
                    "public_share": sig.public_share,
                    "public_count": sig.public_count,
                    "public_field_wr": sig.public_field_wr,
                    "public_field_n": sig.public_field_n,
                    "top_team_share": sig.top_team_share,
                    "top_team_count": sig.top_team_count,
                    "live_share": sig.live_share,
                    "live_count": sig.live_count,
                    "live_losses": sig.live_losses,
                    "loss_share": sig.loss_share,
                },
                "gate": degradation_limits(role),
            }
        )

    return {
        "schema_version": 1,
        "profile_id": args.profile_id or datetime.now().strftime("%Y%m%d-%H%M%S"),
        "created_at_utc": fetched_at,
        "description": args.description,
        "champion_label": args.champion_label,
        "replacement_target_label": args.replacement_target_label,
        "sources": sources,
        "buckets": bucket_rows,
        "submission_gate": {
            "fallback_rate_must_be": 0.0,
            "preferred_weighted_gain_vs_champion_pp": 0.5,
            "companion_allowed_if": "weighted score is near champion and improves champion weak buckets without core regressions",
            "core_max_drop_vs_champion_pp": {
                "Mega Lucario ex": 1.5,
                "Alakazam": 1.5,
                "Hop's Trevenant": 2.0,
            },
            "targeted_loss_cluster_gain_pp": 3.0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base", default=DEFAULT_API_BASE)
    parser.add_argument("--no-fetch", action="store_true", help="Do not fetch public meta API data.")
    parser.add_argument("--live-summary-csv", action="append", default=[], help="Local replay summary CSV or directory.")
    parser.add_argument("--top-teams", type=int, default=30)
    parser.add_argument("--min-public-share", type=float, default=0.005)
    parser.add_argument("--min-output-weight", type=float, default=0.003)
    parser.add_argument("--source-weights", help="Comma list, e.g. public_meta=0.45,top_teams=0.25,...")
    parser.add_argument("--profile-id")
    parser.add_argument("--description", default="loop-engineering meta evaluation profile")
    parser.add_argument("--champion-label", default="v85")
    parser.add_argument("--replacement-target-label", default="v84")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    profile = build_profile(args)
    out = args.out
    if out is None:
        out = Path("runs") / f"meta_eval_profile_{profile['profile_id']}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {out}")
    if args.print_summary:
        print("top buckets:")
        for row in profile["buckets"][:15]:
            print(
                f"- {row['ja_name']} ({row['key']}): "
                f"weight={row['weight']:.4f} role={row['role']} "
                f"public={row['signals']['public_share']:.3f} "
                f"top={row['signals']['top_team_share']:.3f} "
                f"live={row['signals']['live_share']:.3f} "
                f"loss={row['signals']['loss_share']:.3f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

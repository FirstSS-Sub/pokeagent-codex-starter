#!/usr/bin/env python3
"""
Run local cg-engine games between two submission directories.

This script is intended to run on Linux/x86_64 because the bundled cg/libcg.so
from the official sample submission is a Linux shared object. On macOS, run via
Docker, for example:

  docker run --rm -i --platform linux/amd64 \
    -v "$PWD":/work -w /work python:3.11-slim \
    python scripts/eval_submission_pair.py \
      --agent0 local_submissions/candidate \
      --agent1 local_submissions/lucario-v2 \
      --games 60
"""

from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import sys
import time
from types import ModuleType
from typing import Callable


def load_agent(submission_dir: Path, module_name: str) -> ModuleType:
    """Import a submission's main.py as an isolated module."""
    submission_dir = submission_dir.resolve()
    main_py = submission_dir / "main.py"
    deck_csv = submission_dir / "deck.csv"
    if not main_py.exists():
        raise FileNotFoundError(f"missing main.py: {main_py}")
    if not deck_csv.exists():
        raise FileNotFoundError(f"missing deck.csv: {deck_csv}")

    old_cwd = Path.cwd()
    old_path = list(sys.path)
    try:
        os.chdir(submission_dir)
        sys.path.insert(0, str(submission_dir))
        spec = importlib.util.spec_from_file_location(module_name, main_py)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load module spec: {main_py}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        os.chdir(old_cwd)
        sys.path[:] = old_path


def deck_from_module(module: ModuleType) -> list[int]:
    """Read the 60-card deck from common submission module globals."""
    for attr in ("my_deck", "MY_DECK", "DECK"):
        value = getattr(module, attr, None)
        if isinstance(value, list) and len(value) == 60:
            return list(value)
    # Avoid calling agent({"select": None}); some official templates expect a
    # fully shaped Observation dataclass. Fall back to the adjacent deck.csv.
    module_file = Path(getattr(module, "__file__")).resolve()
    rows = [
        int(line.strip())
        for line in (module_file.parent / "deck.csv").read_text().splitlines()
        if line.strip()
    ]
    if len(rows) != 60:
        raise ValueError(f"deck must have 60 cards: {module_file.parent / 'deck.csv'}")
    return rows


def safe_agent_call(agent: Callable[[dict], list[int]], obs: dict) -> tuple[list[int], str | None]:
    """Call an agent and return a legal fallback marker on failure."""
    try:
        selected = agent(obs)
    except Exception as exc:  # pragma: no cover - diagnostic path
        selected = None
        err = f"{type(exc).__name__}: {exc}"
    else:
        err = None

    option_count = len(obs.get("select", {}).get("option", []) or [])
    min_count = int(obs.get("select", {}).get("minCount", 0) or 0)
    max_count = int(obs.get("select", {}).get("maxCount", 0) or 0)
    if not isinstance(selected, list):
        err = err or f"agent returned non-list: {type(selected).__name__}"
        selected = []

    legal: list[int] = []
    seen: set[int] = set()
    for idx in selected:
        if isinstance(idx, int) and 0 <= idx < option_count and idx not in seen:
            legal.append(idx)
            seen.add(idx)
        else:
            err = err or f"illegal option index: {idx!r}"

    target = min(max_count, option_count)
    if len(legal) < min_count:
        for idx in range(option_count):
            if idx not in seen:
                legal.append(idx)
                seen.add(idx)
            if len(legal) >= min_count:
                break
        err = err or "fallback:min_count"
    if len(legal) > target:
        legal = legal[:target]
    return legal, err


def play_game(
    battle_start,
    battle_select,
    battle_finish,
    deck0: list[int],
    deck1: list[int],
    agent0: Callable[[dict], list[int]],
    agent1: Callable[[dict], list[int]],
    max_steps: int,
) -> dict:
    obs, start_data = battle_start(deck0, deck1)
    if obs is None or getattr(start_data, "errorPlayer", -1) >= 0:
        return {
            "result": None,
            "steps": 0,
            "error": f"start_failed:player={getattr(start_data, 'errorPlayer', None)}:"
            f"type={getattr(start_data, 'errorType', None)}",
            "fallbacks": 0,
            "turn": None,
        }

    steps = 0
    fallbacks = 0
    error: str | None = None
    try:
        while obs["current"]["result"] < 0 and steps < max_steps:
            your_index = obs["current"]["yourIndex"]
            agent = agent0 if your_index == 0 else agent1
            selected, err = safe_agent_call(agent, obs)
            if err:
                fallbacks += 1
                if error is None:
                    error = err
            obs = battle_select(selected)
            steps += 1
        result = obs["current"]["result"]
        if result < 0:
            error = error or "max_steps"
        return {
            "result": result,
            "steps": steps,
            "error": error,
            "fallbacks": fallbacks,
            "turn": obs["current"]["turn"],
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {
            "result": None,
            "steps": steps,
            "error": f"{type(exc).__name__}: {exc}",
            "fallbacks": fallbacks,
            "turn": obs.get("current", {}).get("turn") if isinstance(obs, dict) else None,
        }
    finally:
        try:
            battle_finish()
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent0", required=True, type=Path)
    parser.add_argument("--agent1", required=True, type=Path)
    parser.add_argument("--games", type=int, default=20)
    parser.add_argument("--max-steps", type=int, default=2500)
    parser.add_argument("--label0", default="agent0")
    parser.add_argument("--label1", default="agent1")
    args = parser.parse_args()

    # Import cg from agent0 by default; all official samples bundle identical cg/.
    a0 = load_agent(args.agent0, "_eval_agent0")
    a1 = load_agent(args.agent1, "_eval_agent1")
    deck0 = deck_from_module(a0)
    deck1 = deck_from_module(a1)

    from cg.game import battle_finish, battle_select, battle_start

    rows = []
    start = time.monotonic()
    for game in range(args.games):
        if game % 2 == 0:
            out = play_game(
                battle_start,
                battle_select,
                battle_finish,
                deck0,
                deck1,
                a0.agent,
                a1.agent,
                args.max_steps,
            )
            candidate_seat = 0
        else:
            out = play_game(
                battle_start,
                battle_select,
                battle_finish,
                deck1,
                deck0,
                a1.agent,
                a0.agent,
                args.max_steps,
            )
            candidate_seat = 1

        result = out["result"]
        if result == 2:
            outcome = "draw"
        elif result == candidate_seat:
            outcome = "win"
        elif result in (0, 1):
            outcome = "loss"
        else:
            outcome = "error"
        out["outcome0"] = outcome
        rows.append(out)
        print(
            f"game={game + 1:03d} seat={candidate_seat} outcome={outcome:5s} "
            f"result={result} steps={out['steps']} turn={out['turn']} "
            f"fallbacks={out['fallbacks']} error={out['error'] or ''}",
            flush=True,
        )

    wins = sum(1 for row in rows if row["outcome0"] == "win")
    losses = sum(1 for row in rows if row["outcome0"] == "loss")
    draws = sum(1 for row in rows if row["outcome0"] == "draw")
    errors = sum(1 for row in rows if row["outcome0"] == "error" or row["error"])
    fallbacks = sum(int(row["fallbacks"]) for row in rows)
    decisions = sum(int(row["steps"]) for row in rows)
    elapsed = time.monotonic() - start
    winrate = wins / max(1, wins + losses)
    fallback_rate = fallbacks / max(1, decisions)

    print("--- summary ---")
    print(f"{args.label0} vs {args.label1}")
    print(f"games={args.games} wins={wins} losses={losses} draws={draws} errors={errors}")
    print(f"winrate_no_draws={winrate:.4f}")
    print(f"fallbacks={fallbacks} decisions={decisions} fallback_rate={fallback_rate:.6f}")
    print(f"elapsed_sec={elapsed:.2f}")
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

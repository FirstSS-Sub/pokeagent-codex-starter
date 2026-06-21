"""Minimal PTCG ABC Kaggle agent.

This file is intentionally simple:
- On the initial call, it returns the 60-card deck loaded from deck.csv.
- On normal turns, it returns deterministic legal option indices.

It is a packaging/validation starting point, not a competitive agent.
"""

from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Any


def _deck_path() -> Path:
    candidates = [
        Path("deck.csv"),
        Path("/kaggle_simulations/agent/deck.csv"),
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("deck.csv not found at top-level submission directory")


def _load_deck() -> list[int]:
    rows = [line.strip() for line in _deck_path().read_text().splitlines()]
    rows = [line for line in rows if line]
    if len(rows) < 60:
        raise ValueError(f"deck.csv must contain at least 60 non-empty rows; got {len(rows)}")
    deck = [int(x) for x in rows[:60]]
    if len(deck) != 60:
        raise ValueError("deck must contain exactly 60 cards")
    return deck


MY_DECK = _load_deck()
RANDOMIZE = os.environ.get("PTCG_AGENT_RANDOM", "0") == "1"


def _safe_action(select: dict[str, Any]) -> list[int]:
    options = select.get("option") or []
    min_count = int(select.get("minCount", 0))
    max_count = int(select.get("maxCount", min_count))

    if max_count < min_count:
        max_count = min_count

    count = min(max_count, len(options))
    if count < min_count:
        # The environment should not present this, but return as many legal indices as possible.
        count = len(options)

    indices = list(range(len(options)))
    if RANDOMIZE:
        random.shuffle(indices)
    return sorted(indices[:count])


def agent(obs_dict: dict[str, Any]) -> list[int]:
    select = obs_dict.get("select")
    if select is None:
        return MY_DECK
    return _safe_action(select)

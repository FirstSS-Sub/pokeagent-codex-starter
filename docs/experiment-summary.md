# Experiment Summary: PTCG ABC Rule-Based Agent Iteration

Date range: 2026-06-20 to 2026-06-22

This document is a sanitized public summary of an AI-assisted development session for the Pokémon Trading Card Game AI Battle Challenge Simulation category. It intentionally omits local filesystem paths, credentials, raw competition data, and generated submission packages.

## Goal

Improve a Kaggle Simulation agent through a disciplined loop:

1. establish a valid baseline submission,
2. run local package and battle checks,
3. inspect public leaderboard / episode signals,
4. make small, testable agent/deck changes,
5. submit only validated candidates,
6. record which hypotheses transferred to the live environment.

## Best observed direction

The strongest direction was an **Alakazam hand-size damage deck**:

- Build the Abra / Kadabra / Alakazam line consistently.
- Use Dunsparce / Dudunsparce and supporter cards to keep hand size high.
- Convert hand size into attack damage.
- Use targeted disruption and Boss-style effects only when they improve the prize race.
- Guard against deck-out and illegal choices.

A one-of hand-disruption tech was promising in live scoring, while adding a second copy overfit local mirrors and transferred poorly to the public environment.

## Development path

### 1. Baseline validation

The first milestone was to package and validate an official-style sample agent. This established:

- the required `main.py + deck.csv` shape,
- inclusion of bundled competition engine files when needed,
- Kaggle validation behavior,
- the initial public-score baseline.

### 2. Rule-based Lucario improvements

Early iterations improved a Mega Lucario-style rule-based agent by emphasizing:

- setup sequencing,
- energy attachment priority,
- lethal attack targeting,
- prize-race awareness,
- avoiding invalid or low-value actions.

These changes were useful engineering practice but did not close the gap to stronger public leaderboard strategies.

### 3. Switch to Alakazam-family strategies

Public leaderboard and replay signals suggested that Alakazam-family decks were a stronger foundation. The agent was shifted toward:

- denser evolution lines,
- more reliable draw/search engines,
- fewer low-impact tech cards,
- better target selection and deck-safety heuristics.

This produced the largest score improvement in the session.

### 4. Local evaluation as a submission gate

The local evaluator was used to compare candidate submissions against known local baselines before using limited Kaggle submissions.

Local checks were most useful for:

- catching syntax/package problems,
- detecting illegal action fallbacks,
- measuring known matchup regressions,
- filtering clearly weak candidates.

They were not sufficient to guarantee public score improvements because the live opponent pool contains unknown agents and a different matchup distribution.

### 5. Negative result: overfitting to local mirrors

A final double-disruption variant looked strong in local head-to-head tests but performed poorly in early public scoring. The main lesson:

> A candidate can beat the current local best while still being worse against the live public pool.

This reinforced the need to maintain proxy opponents for known public archetypes and to analyze public replays whenever available.

## Key lessons

1. **Start from a strong archetype.** Agent heuristics matter, but deck/archetype choice dominated early progress.
2. **Keep changes small and attributable.** One-card deltas and focused scoring tweaks made it possible to interpret results.
3. **Use local simulation as a filter, not an oracle.** Local wins are necessary evidence, not final proof.
4. **Track negative results.** The failed double-disruption experiment is useful evidence against overfitting.
5. **Respect submission windows.** Kaggle daily submission limits are counted by UTC date; tooling should make that explicit.

## Reproducible tooling in this repository

- `scripts/package_submission.sh`: creates Kaggle-compatible archives.
- `scripts/eval_submission_pair.py`: runs local agent-vs-agent battles via Docker/Linux.
- `scripts/fetch_public_metadata.sh`: captures public competition metadata snapshots.
- `scripts/kaggle_submission_quota.py`: estimates daily submission usage from Kaggle timestamps.

## Public-data policy

This repository intentionally does not include:

- raw competition card datasets,
- raw episode replays,
- local candidate submissions,
- packaged `.tar.gz` submissions,
- credentials or local environment files.

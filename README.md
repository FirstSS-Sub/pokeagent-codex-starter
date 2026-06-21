# PTCG ABC Codex Starter

A public starter and experiment workspace for the **Pokémon Trading Card Game AI Battle Challenge**.

This repository demonstrates a practical workflow for building, validating, and iterating on rule-based Pokémon TCG agents with AI-assisted development. It focuses on reproducible local packaging/evaluation, public metadata analysis, and safe Kaggle submission operations.

## Highlights

- Competition research notes for the Simulation and Strategy categories.
- Minimal `main.py` submission template.
- Packaging script for Kaggle-compatible `.tar.gz` submissions.
- Local agent-vs-agent evaluation harness using the bundled competition engine.
- Public metadata snapshot helper for leaderboard and episode-index research.
- Daily submission quota estimator based on Kaggle UTC timestamps.
- Experiment summary documenting the path from baseline agents to stronger Alakazam variants.

## Competition links

- Official site: <https://ptcg-abc.pokemon.co.jp/>
- Kaggle Simulation: <https://www.kaggle.com/competitions/pokemon-tcg-ai-battle>
- Kaggle Strategy: <https://www.kaggle.com/competitions/pokemon-tcg-ai-battle-challenge-strategy>
- API docs: <https://matsuoinstitute.github.io/cabt/>

## Repository map

```text
.
├── AGENTS.md                         # Repository-specific Codex instructions
├── README.md
├── config/sources.txt                # Public source list
├── docs/
│   ├── research-brief.md             # Competition overview and constraints
│   ├── codex-battle-plan.md          # AI-assisted development plan
│   ├── experiment-summary.md         # Sanitized experiment summary
│   └── setup-checklist.md
├── prompts/                          # Reusable Codex task prompts
├── scripts/
│   ├── check_prereqs.sh
│   ├── fetch_public_metadata.sh
│   ├── package_submission.sh
│   ├── eval_submission_pair.py
│   └── kaggle_submission_quota.py
└── templates/submission_minimal/
    └── main.py
```

Ignored local-only directories:

```text
cache/              # public metadata cache
local_submissions/  # local candidate submissions
data/               # competition data
runs/               # packaged submissions and experiment outputs
.venv/              # Python virtual environment
```

## Quick start

```bash
git clone git@github.com:<owner>/pokeagent-codex-starter.git
cd pokeagent-codex-starter
./scripts/check_prereqs.sh
./scripts/fetch_public_metadata.sh --dry-run
```

Create a minimal local candidate:

```bash
mkdir -p local_submissions/minimal-agent
cp templates/submission_minimal/main.py local_submissions/minimal-agent/main.py
# Place a competition-valid deck.csv in local_submissions/minimal-agent/.
./scripts/package_submission.sh local_submissions/minimal-agent runs/submission-minimal.tar.gz
```

`local_submissions/` and `runs/` are intentionally ignored.

## Local evaluation

The competition sample engine ships a Linux shared library, so local battles are run in Docker on macOS:

```bash
docker run --rm -i --platform linux/amd64 \
  -v "$PWD":/work -w /work python:3.11-slim \
  python scripts/eval_submission_pair.py \
    --agent0 local_submissions/candidate-a \
    --agent1 local_submissions/candidate-b \
    --label0 candidate-a \
    --label1 candidate-b \
    --games 100
```

The evaluator reports wins, losses, draws, fallback rate, and runtime errors. This is useful for regression testing and known-matchup tuning, but it does not fully reproduce the live Kaggle opponent pool.

## Kaggle submission quota helper

Kaggle Simulation submissions are counted by UTC date. The helper estimates daily usage by counting the current UTC day's submissions:

```bash
.venv/bin/python scripts/kaggle_submission_quota.py
```

It prints:

- current UTC date,
- `maxDailySubmissions`,
- used submissions for that UTC date,
- estimated remaining submissions,
- next UTC reset time.

## Experiment summary

See [`docs/experiment-summary.md`](docs/experiment-summary.md) for the sanitized development narrative:

1. validate a baseline sample agent,
2. improve rule-based Lucario heuristics,
3. switch to stronger Alakazam-family strategies based on public evidence,
4. use local agent-vs-agent tests as a submission gate,
5. identify that a one-of disruption tech was promising while doubling down on it overfit local mirrors.

## Safety and data policy

- Do not commit Kaggle credentials, API keys, `.env`, datasets, caches, packaged submissions, or local candidate directories.
- Do not redistribute competition data outside the competition's permitted channels.
- Keep full card lists, raw episode replays, and generated submission packages out of git.
- Treat local evaluation results as a filter, not as a replacement for live validation.

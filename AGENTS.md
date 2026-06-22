# AGENTS.md - PTCG ABC Codex Starter

This repository is a public workspace for researching and iterating on agents for the **Pokémon Trading Card Game AI Battle Challenge**.

## Project scope

- Target competition: **The Pokémon Company - PTCG AI Battle Challenge**.
- Simulation category: submit an AI agent and `deck.csv` to Kaggle.
- Strategy category: write up the agent logic, deck concept, and validation methodology.
- This is a Pokémon TCG agent project, not a Pokémon Showdown project.

## Operating rules

1. Prefer official/public sources.
   - Official site: `https://ptcg-abc.pokemon.co.jp/`
   - Kaggle Simulation: `https://www.kaggle.com/competitions/pokemon-tcg-ai-battle`
   - Kaggle Strategy: `https://www.kaggle.com/competitions/pokemon-tcg-ai-battle-challenge-strategy`
   - API docs: `https://matsuoinstitute.github.io/cabt/`
2. Record external sources and retrieval dates when using web/forum information.
3. Treat competition data as Competition Use Only.
   - Do not commit `data/`, `cache/`, `runs/`, `local_submissions/`, raw replays, full card datasets, or packaged submissions.
4. Never print or commit credentials.
   - `.env`, Kaggle API files, tokens, and OAuth caches must stay local.
5. Before a Kaggle submission, run local package checks and, when possible, local agent-vs-agent evaluation.
6. Generated `_gen`-style or competition-provided data files should not be hand-edited unless the source workflow requires it.

## Recommended workflow

1. Refresh public metadata and leaderboard context.
2. Build candidate submissions under ignored `local_submissions/`.
3. Package candidates with `scripts/package_submission.sh`.
4. Evaluate candidates locally with `scripts/eval_submission_pair.py`.
5. Submit only candidates with a clear hypothesis and validation evidence.
6. Capture sanitized experiment results in docs, not raw private logs.

## Best-submission registry

- Whenever a Kaggle submission reaches a new confirmed best public score, record
  enough local information to re-submit the exact implementation later.
- Keep the detailed registry in ignored local storage, currently
  `runs/best-submission-registry.md`.
- Each best-record entry should include the submission ref, Kaggle filename,
  confirmed score, candidate name, relative source directory, relative package
  path, package SHA-256, and a short strategy summary.
- Do not commit packaged submissions, raw replays, raw logs, or competition
  datasets just to preserve this registry.

## Done criteria for public changes

- No local absolute paths.
- No usernames, local machine identifiers, or private account names unless intentionally public.
- No secrets or credential file contents.
- No raw competition datasets, full card lists, replays, or packaged submissions.
- Scripts run or at least pass syntax checks when modified.

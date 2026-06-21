#!/bin/bash
set -euo pipefail

cat <<'MSG'
This repository no longer bootstraps PokéAgent/Pokémon Showdown OSS repos.

PTCG ABC is a Kaggle simulation competition. Start with:

  ./scripts/check_prereqs.sh
  ./scripts/fetch_public_metadata.sh --dry-run
  ./scripts/fetch_public_metadata.sh --out cache/public/latest

Then read:

  docs/research-brief.md
  docs/codex-battle-plan.md
  docs/setup-checklist.md

If you need a submission package:

  mkdir -p local_submissions/minimal-agent
  cp templates/submission_minimal/main.py local_submissions/minimal-agent/main.py
  # Place a legal deck.csv from Kaggle official Data/Starter Notebook.
  ./scripts/package_submission.sh local_submissions/minimal-agent runs/submission-minimal.tar.gz
MSG

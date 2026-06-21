# Minimal PTCG ABC submission template

This template intentionally does **not** include a `deck.csv`.

Use it after you have joined the Kaggle competition and obtained/created a legal deck from the official Data page or Starter Notebooks.

Expected package layout:

```text
main.py
deck.csv
```

Package example:

```bash
mkdir -p local_submissions/minimal-agent
cp templates/submission_minimal/main.py local_submissions/minimal-agent/main.py
# Place your legal deck.csv at local_submissions/minimal-agent/deck.csv
./scripts/package_submission.sh local_submissions/minimal-agent runs/submission-minimal.tar.gz
```

`main.py` is deliberately weak. It only proves the submission shape and legal-action guard. Build a real scorer before expecting leaderboard performance.

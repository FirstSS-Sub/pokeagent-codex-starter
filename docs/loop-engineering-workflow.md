# Loop Engineering Workflow

This document defines the local preparation needed before running long
goal-driven research loops for the Pokémon TCG AI Battle Challenge.

The purpose is to avoid a common failure mode:

> Patch the latest loss, regress against the broader meta, submit, repeat.

Instead, every candidate should be evaluated against a versioned meta profile,
with explicit tuning/holdout separation and a machine-readable experiment
ledger.

## Components

### 1. Meta evaluation profile

Generate a profile with:

```bash
python3 scripts/build_meta_eval_profile.py \
  --live-summary-csv cache/kaggle/monitor_YYYYMMDD/summary.csv \
  --print-summary
```

Default output:

```text
runs/meta_eval_profile_<profile_id>.json
```

The profile combines:

- observed public meta from the community ladder API,
- top-team modal archetypes,
- this team's recent live replay distribution,
- capped recent loss clusters.

Default source weights:

```text
public_meta   45%
top_teams     25%
live_replays  20%
loss_clusters 10%
```

The loss-cluster cap is intentional. It keeps the loop from optimizing only
against the latest bad matchup.

### 2. Local proxy map

Copy the example:

```bash
cp config/eval_proxy_map.example.json runs/eval_proxy_map.local.json
```

Then edit the local copy to point to ignored local submissions. Keep the local
copy out of git if it contains raw or private experiment details.

Each bucket can have multiple proxies:

```json
{
  "buckets": {
    "Alakazam": [
      {
        "label": "alakazam_reference",
        "path": "local_submissions/example-alakazam",
        "role": "core_holdout"
      }
    ]
  }
}
```

Use `role` consistently:

- `tuning`: recent loss or a proxy used to design the candidate.
- `core_holdout`: high-weight meta bucket not directly tuned on.
- `coverage_holdout`: lower-frequency but important upper-ladder bucket.
- `smoke`: sanity-check opponent.

### 3. Experiment ledger

Initialize:

```bash
python3 scripts/experiment_ledger.py init
```

Default output:

```text
runs/experiment_ledger.jsonl
```

Summarize:

```bash
python3 scripts/experiment_ledger.py summary
```

The ledger stores per-candidate, per-bucket, per-proxy results and weighted
score components. It should be used for submission decisions instead of
one-off impressions.

### 4. Profile matrix evaluation

Dry-run the matrix:

```bash
python3 scripts/eval_profile_matrix.py \
  --profile runs/meta_eval_profile_<profile_id>.json \
  --proxy-map runs/eval_proxy_map.local.json \
  --candidate champion=local_submissions/current-champion \
  --candidate challenger=local_submissions/new-candidate \
  --include-role core \
  --limit-buckets 5 \
  --games 100 \
  --docker \
  --dry-run
```

Run it for real:

```bash
python3 scripts/eval_profile_matrix.py \
  --profile runs/meta_eval_profile_<profile_id>.json \
  --proxy-map runs/eval_proxy_map.local.json \
  --candidate champion=local_submissions/current-champion \
  --candidate challenger=local_submissions/new-candidate \
  --include-role core \
  --limit-buckets 5 \
  --games 250 \
  --docker
```

On macOS, `--docker` is normally required because the official simulator
shared library is Linux/x86_64.

## Submission gates

Use the current champion as the baseline. A candidate should not be submitted
just because it improves one recent loss.

Recommended gates:

1. Package/import smoke passes.
2. Fallback/error rate is zero.
3. Candidate is evaluated in the same profile as the champion and fallback.
4. Weighted expected win rate is preferably at least champion + 0.5pp.
5. If the candidate is a companion rather than a champion replacement, it must
   improve champion weak buckets without damaging high-frequency buckets.
6. Core bucket no-regression:
   - メガルカリオex: no worse than champion by 1.5pp.
   - フーディン: no worse than champion by 1.5pp.
   - ホップのオーロット: no worse than champion by 2.0pp.
7. A targeted anti-ドラパルトex hypothesis should improve ドラパルトex by
   roughly 3.0pp or more, without violating the core no-regression gates.

## Night loop outline

For long-running goal work:

1. Refresh submissions, scores, episode counts, replays, leaderboard, and meta
   API.
2. Build a new `meta_eval_profile`.
3. Cluster losses, but cap their profile contribution.
4. Generate candidates from explicit operators:
   - small deck edits,
   - ハロンタウン gating,
   - ボスの指令 target priority,
   - クセロシキのたくらみ timing,
   - evolution/search/energy/bench management,
   - optional offline rollout or teacher-label distillation.
5. Run progressive halving:
   - cheap screen,
   - medium tournament,
   - deep holdout.
6. Append every result to the ledger.
7. Package only candidates that pass gates.
8. Submit only when the current goal explicitly permits it.

## Public repository hygiene

Do not commit:

- `runs/`,
- `cache/`,
- `local_submissions/`,
- packaged submissions,
- raw replays,
- full card datasets,
- credentials.

Run before pushing:

```bash
python3 scripts/public_repo_audit.py
```

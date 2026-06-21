#!/bin/bash
set -euo pipefail

OUT="cache/public/$(date +%Y%m%d-%H%M%S)"
DRY_RUN=0

usage() {
  cat <<USAGE
Usage: $0 [--dry-run] [--out DIR]

Fetches public PTCG ABC metadata from official/Kaggle public endpoints:
  - Kaggle competition metadata for Simulation and Strategy
  - Kaggle competition pages (overview/evaluation/rules text via public web API)
  - Simulation public leaderboard snapshot
  - Daily top episodes manifest

No Kaggle secrets are printed. cache/ is gitignored.
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --out) OUT="${2:-}"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

if [ -z "$OUT" ]; then
  echo "--out must not be empty" >&2
  exit 2
fi

cat <<PLAN
Output directory: $OUT
Will fetch:
  1. https://www.kaggle.com/competitions/pokemon-tcg-ai-battle
  2. https://www.kaggle.com/competitions/pokemon-tcg-ai-battle-challenge-strategy
  3. public leaderboard for competitionId 116727
  4. https://www.kaggle.com/datasets/kaggle/pokemon-tcg-ai-battle-episodes-index manifest.csv
PLAN

if [ "$DRY_RUN" -eq 1 ]; then
  echo "dry-run only; no network fetch performed"
  exit 0
fi

mkdir -p "$OUT"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

get_xsrf() {
  local url="$1"
  curl -L --silent --show-error --fail -c "$tmp/cookies.txt" "$url" >/dev/null
  awk '$6=="XSRF-TOKEN" {print $7}' "$tmp/cookies.txt" | tail -1
}

post_kaggle() {
  local body="$1"
  local endpoint="$2"
  local xsrf="$3"
  curl --silent --show-error \
    -b "$tmp/cookies.txt" \
    -H "Content-Type: application/json" \
    -H "X-XSRF-TOKEN: $xsrf" \
    --data "$body" \
    "$endpoint"
}

for comp in pokemon-tcg-ai-battle pokemon-tcg-ai-battle-challenge-strategy; do
  echo "fetch competition: $comp"
  xsrf=$(get_xsrf "https://www.kaggle.com/competitions/$comp")
  post_kaggle "{\"competitionName\":\"$comp\"}" \
    'https://www.kaggle.com/api/i/competitions.CompetitionService/GetCompetition' \
    "$xsrf" > "$OUT/${comp}.competition.json"
  id=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' "$OUT/${comp}.competition.json")
  post_kaggle "{\"competitionId\":$id}" \
    'https://www.kaggle.com/api/i/competitions.PageService/ListPages' \
    "$xsrf" > "$OUT/${comp}.pages.json"
done

xsrf=$(get_xsrf 'https://www.kaggle.com/competitions/pokemon-tcg-ai-battle/leaderboard')
post_kaggle '{"competitionId":116727}' \
  'https://www.kaggle.com/api/i/competitions.LeaderboardService/GetLeaderboard' \
  "$xsrf" > "$OUT/pokemon-tcg-ai-battle.leaderboard.json"

curl -L --silent --show-error --fail \
  -o "$OUT/pokemon-tcg-ai-battle-episodes-index.zip" \
  'https://www.kaggle.com/api/v1/datasets/download/kaggle/pokemon-tcg-ai-battle-episodes-index'
unzip -p "$OUT/pokemon-tcg-ai-battle-episodes-index.zip" manifest.csv > "$OUT/pokemon-tcg-ai-battle-episodes-index.manifest.csv"
rm -f "$OUT/pokemon-tcg-ai-battle-episodes-index.zip"

python3 - "$OUT" <<'PY'
import csv, json, pathlib, sys
out = pathlib.Path(sys.argv[1])
leader = json.load(open(out / 'pokemon-tcg-ai-battle.leaderboard.json'))
teams = {t['teamId']: t for t in leader.get('teams', [])}
rows = []
for row in leader.get('publicLeaderboard', [])[:30]:
    team = teams.get(row['teamId'], {})
    rows.append({
        'rank': row.get('rank'),
        'score': row.get('displayScore'),
        'team': team.get('teamName'),
        'submissionId': row.get('submissionId'),
        'teamId': row.get('teamId'),
    })
with open(out / 'leaderboard_top30.json', 'w') as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)
with open(out / 'summary.md', 'w') as f:
    f.write('# PTCG ABC public metadata snapshot\n\n')
    f.write(f'Output: `{out}`\n\n')
    f.write('## Leaderboard top 30\n\n')
    for r in rows:
        f.write(f"- #{r['rank']} {r['score']} {r['team']} submission={r['submissionId']} teamId={r['teamId']}\n")
    f.write('\n## Daily episodes manifest\n\n')
    with open(out / 'pokemon-tcg-ai-battle-episodes-index.manifest.csv') as mf:
        for line in mf:
            f.write('- ' + line.strip() + '\n')
print(out / 'summary.md')
PY

echo "done: $OUT"

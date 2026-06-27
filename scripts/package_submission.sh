#!/bin/bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $0 SUBMISSION_DIR OUT_TAR_GZ

SUBMISSION_DIR must contain top-level:
  - main.py
  - deck.csv

All other top-level files/directories in SUBMISSION_DIR are included too.
This is important for official starter submissions that import bundled
modules such as cg/.

Example:
  $0 local_submissions/minimal-agent runs/submission-minimal.tar.gz
USAGE
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ] || [ "$#" -ne 2 ]; then
  usage
  exit 0
fi

src="$1"
out="$2"

if [ ! -d "$src" ]; then
  echo "submission dir not found: $src" >&2
  exit 1
fi
if [ ! -f "$src/main.py" ]; then
  echo "missing: $src/main.py" >&2
  exit 1
fi
if [ ! -f "$src/deck.csv" ]; then
  echo "missing: $src/deck.csv" >&2
  exit 1
fi

rows=$(awk 'NF {count++} END {print count+0}' "$src/deck.csv")
if [ "$rows" -ne 60 ]; then
  echo "deck.csv must contain exactly 60 non-empty rows; got $rows" >&2
  exit 1
fi

mkdir -p "$(dirname "$out")"
out_abs="$(cd "$(dirname "$out")" && pwd)/$(basename "$out")"
rm -f "$out_abs"
(
  cd "$src"
  entries=()
  while IFS= read -r -d '' entry; do
    base=$(basename "$entry")
    case "$base" in
      __pycache__|.pytest_cache|.mypy_cache|.DS_Store)
        continue
        ;;
      *.tar|*.tar.gz|*.zip)
        continue
        ;;
    esac
    entries+=("$base")
  done < <(find . -mindepth 1 -maxdepth 1 -print0)

  if [ "${#entries[@]}" -eq 0 ]; then
    echo "submission dir has no package entries: $src" >&2
    exit 1
  fi

  COPYFILE_DISABLE=1 tar \
    --exclude='__pycache__' \
    --exclude='*/__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='.mypy_cache' \
    --exclude='.DS_Store' \
    --exclude='._*' \
    --exclude='*/._*' \
    --exclude='__MACOSX' \
    --exclude='*/__MACOSX' \
    --exclude='*.tar' \
    --exclude='*.tar.gz' \
    --exclude='*.zip' \
    -czf "$out_abs" "${entries[@]}"
)

printf 'created: %s\n' "$out"
printf 'contents:\n'
tar -tzf "$out_abs"

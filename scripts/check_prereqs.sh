#!/bin/bash
set -u

ok=0
warn=0
fail=0

check_cmd() {
  local name="$1"
  local cmd="$2"
  local required="$3"
  if command -v "$cmd" >/dev/null 2>&1; then
    printf 'OK   %-18s found\n' "$name"
    ok=$((ok+1))
  else
    if [ "$required" = "required" ]; then
      printf 'FAIL %-18s not found\n' "$name"
      fail=$((fail+1))
    else
      printf 'WARN %-18s not found (optional)\n' "$name"
      warn=$((warn+1))
    fi
  fi
}

printf '%s\n' '== PTCG ABC Codex Starter prerequisite check =='
printf 'repo: %s\n' "$(basename "$(pwd)")"
printf '\n-- commands --\n'
check_cmd git git required
check_cmd python3 python3 required
check_cmd curl curl required
check_cmd tar tar required
check_cmd gzip gzip required
check_cmd unzip unzip optional
check_cmd jq jq optional
check_cmd kaggle kaggle optional
check_cmd codex codex optional
check_cmd docker docker optional
check_cmd nvidia-smi nvidia-smi optional

print_version() {
  local c="$1"
  if ! command -v "$c" >/dev/null 2>&1; then
    return
  fi
  printf '%s: ' "$c"
  case "$c" in
    unzip) "$c" -v 2>&1 | head -n 1 || true ;;
    codex) "$c" --version 2>/dev/null | head -n 1 || true ;;
    *) "$c" --version 2>&1 | head -n 1 || true ;;
  esac
}

printf '\n-- versions --\n'
for c in git python3 curl tar gzip unzip jq kaggle codex docker nvidia-smi; do
  print_version "$c"
done

printf '\n-- kaggle credentials --\n'
kaggle_config="${KAGGLE_CONFIG_DIR:-$HOME/.kaggle}/kaggle.json"
if [ -f "$kaggle_config" ]; then
  printf 'OK   Kaggle credential file exists (values not displayed)\n'
elif [ -f .env ] && grep -Eq '^KAGGLE_(USERNAME|KEY)=' .env; then
  printf 'OK   Kaggle env keys appear in .env (values not displayed)\n'
else
  printf 'WARN Kaggle API credentials not found; browser upload still works, but CLI/API downloads may require setup\n'
  warn=$((warn+1))
fi

printf '\n-- local env files --\n'
if [ -f .env ]; then
  printf 'OK   .env exists (values not displayed)\n'
else
  printf 'WARN .env not found; copy .env.example only if credentials are needed\n'
  warn=$((warn+1))
fi

printf '\n-- disk --\n'
df -h . | awk 'NR==2 {print "available_disk=" $4}'

printf '\nsummary: ok=%d warn=%d fail=%d\n' "$ok" "$warn" "$fail"
if [ "$fail" -gt 0 ]; then
  exit 1
fi

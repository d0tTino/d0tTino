#!/usr/bin/env bash
set -euo pipefail

OUTPUT_DIR=".cache/tino/nvim-startup"
LOG_FILE="${OUTPUT_DIR}/startup.log"
SUMMARY_FILE="${OUTPUT_DIR}/summary.txt"
TOP_COUNT="${TOP_COUNT:-20}"

mkdir -p "${OUTPUT_DIR}"

if ! command -v nvim >/dev/null 2>&1; then
  echo "Neovim (nvim) is not installed or not on PATH." >&2
  exit 1
fi

printf 'Running Neovim startup benchmark...\n'
nvim --headless --startuptime "${LOG_FILE}" +qa

{
  printf 'Neovim startup benchmark\n'
  printf 'Generated: %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  printf 'Log file: %s\n\n' "${LOG_FILE}"
  printf 'Top %s startup entries (ms)\n' "${TOP_COUNT}"
  printf '%s\n' '----------------------------------------'

  awk -F':' '
    match($1, /([0-9]+\.[0-9]+)/, m) {
      line = $2
      gsub(/^ +/, "", line)
      gsub(/ +$/, "", line)
      if (line != "") {
        printf "%.3f\t%s\n", m[1], line
      }
    }
  ' "${LOG_FILE}" \
    | sort -nr -k1,1 \
    | head -n "${TOP_COUNT}" \
    | awk -F'\t' '{printf "%9.3f | %s\n", $1, $2}'
} > "${SUMMARY_FILE}"

printf 'Startup log saved to: %s\n' "${LOG_FILE}"
printf 'Summary saved to: %s\n' "${SUMMARY_FILE}"

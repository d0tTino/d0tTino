#!/usr/bin/env bash
set -euo pipefail

cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}"
cache_file="$cache_dir/tmux-status-metrics"
cache_ttl=10

mkdir -p "$cache_dir"

file_mtime() {
  local file="$1"
  local mtime

  if mtime="$(stat -c %Y "$file" 2>/dev/null)"; then
    printf '%s\n' "$mtime"
    return 0
  fi

  if mtime="$(stat -f %m "$file" 2>/dev/null)"; then
    printf '%s\n' "$mtime"
    return 0
  fi

  printf '0\n'
}

now="$(date +%s)"
if [[ -f "$cache_file" ]]; then
  modified="$(file_mtime "$cache_file")"
  if (( now - modified < cache_ttl )); then
    cat "$cache_file"
    exit 0
  fi
fi

if [[ -r /proc/loadavg ]]; then
  read -r loadavg _ < /proc/loadavg
  output="󰻠 ${loadavg}"
else
  output="󰻠 n/a"
fi

printf '%s\n' "$output" > "$cache_file"
printf '%s\n' "$output"

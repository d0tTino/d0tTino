#!/usr/bin/env bash
set -euo pipefail

cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}"
cache_file="$cache_dir/tmux-status-metrics"
cache_ttl=10

mkdir -p "$cache_dir"

now="$(date +%s)"
if [[ -f "$cache_file" ]]; then
  modified="$(stat -c %Y "$cache_file" 2>/dev/null || echo 0)"
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

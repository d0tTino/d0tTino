#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "${BASH_SOURCE[0]%/*}" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <service> [docker compose args...]" >&2
    exit 1
fi

service="$1"
shift

if ! command -v docker >/dev/null 2>&1; then
    echo "docker is required but not installed." >&2
    exit 1
fi

cd "$repo_root"
exec docker compose up "$service" "$@"

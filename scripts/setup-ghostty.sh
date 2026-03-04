#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
terminal_provider_setup="$repo_root/scripts/setup-terminal-provider.sh"

if [[ ! -x "$terminal_provider_setup" ]]; then
    echo "Error: missing terminal provider setup at $terminal_provider_setup" >&2
    exit 1
fi

bash "$terminal_provider_setup" ghostty

echo "Ghostty configured via setup-terminal-provider.sh."

#!/usr/bin/env bash
set -euo pipefail

hooks_path=$(git config --get core.hooksPath || true)
if [[ -z "$hooks_path" ]]; then
    echo "Git hooks are not configured. Run ./scripts/setup-hooks.sh to enable them." >&2
else
    echo "Git hooks path is set to '$hooks_path'"
fi

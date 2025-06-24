#!/usr/bin/env bash
set -euo pipefail

# Configure Git to use local hooks directory if not already set
current_path=$(git config --get core.hooksPath || true)
if [[ -z "$current_path" ]]; then
    git config core.hooksPath .githooks
    echo "Git hooks enabled using .githooks"
else
    echo "Git hooks already configured at '$current_path'"
fi

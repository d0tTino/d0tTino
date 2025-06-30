#!/usr/bin/env bash
set -euo pipefail

# Exit early if Git is not installed
if ! command -v git >/dev/null 2>&1; then
    echo "git is required" >&2
    exit 1
fi

# Configure Git to use local hooks directory if not already set
current_path=$(git config --get core.hooksPath || true)
if [[ -z "$current_path" ]]; then
    git config core.hooksPath .githooks
    verify_path=$(git config --get core.hooksPath || true)
    if [[ "$verify_path" != ".githooks" ]]; then
        echo "Error: core.hooksPath verification failed" >&2
        exit 1
    fi
    echo "Git hooks enabled using .githooks"
else
    echo "Git hooks already configured at '$current_path'"
fi

#!/usr/bin/env bash
set -euo pipefail

# Configure Git to use local hooks directory
git config core.hooksPath .githooks

echo "Git hooks enabled using .githooks"

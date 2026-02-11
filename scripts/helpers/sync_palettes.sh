#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$repo_root/scripts/helpers/generate_palette_artifacts.py"
python3 "$repo_root/windows-terminal/generate_settings.py" "$repo_root/windows-terminal/settings.base.json" "$repo_root/windows-terminal/settings.json"

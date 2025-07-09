#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scripts="$repo_root/scripts"

bash "$scripts/setup-hooks.sh"
bash "$scripts/helpers/install_fonts.sh"
bash "$scripts/helpers/sync_palettes.sh"

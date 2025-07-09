#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "$script_dir/helpers/install_fonts.sh"
bash "$script_dir/helpers/sync_palettes.sh"

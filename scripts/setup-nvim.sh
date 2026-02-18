#!/usr/bin/env bash
set -euo pipefail

lazy_path="${XDG_DATA_HOME:-$HOME/.local/share}/nvim/lazy/lazy.nvim"
lazy_repo="https://github.com/folke/lazy.nvim.git"

if [[ -d "$lazy_path/.git" ]]; then
    echo "lazy.nvim already installed at $lazy_path"
    exit 0
fi

if [[ -e "$lazy_path" ]]; then
    echo "Error: $lazy_path exists but is not a lazy.nvim git checkout." >&2
    exit 1
fi

mkdir -p "$(dirname "$lazy_path")"
git clone --filter=blob:none --branch=stable "$lazy_repo" "$lazy_path"
echo "Installed lazy.nvim to $lazy_path"

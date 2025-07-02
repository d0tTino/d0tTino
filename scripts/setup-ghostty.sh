#!/usr/bin/env bash
set -euo pipefail

# Install Ghostty via cargo if not already installed
if ! command -v cargo >/dev/null 2>&1; then
    echo "Error: cargo is required to install Ghostty" >&2
    exit 1
fi

if ! command -v ghostty >/dev/null 2>&1; then
    cargo install --locked ghostty
fi

config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/ghostty"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
config_file="$config_dir/ghostty.toml"
mkdir -p "$config_dir"

if [[ -e "$config_file" ]]; then
    echo "Configuration already exists at $config_file"
else
    cp "$repo_root/dotfiles/ghostty/ghostty.toml" "$config_file"
    echo "Configuration copied to $config_file"
fi

echo "Ghostty installed."


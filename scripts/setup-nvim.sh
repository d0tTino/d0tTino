#!/usr/bin/env bash
set -euo pipefail

lazy_path="${XDG_DATA_HOME:-$HOME/.local/share}/nvim/lazy/lazy.nvim"
lazy_repo="https://github.com/folke/lazy.nvim.git"
required_lsp_servers=(lua_ls pyright ts_ls bashls)

if ! command -v nvim >/dev/null 2>&1; then
    echo "Error: nvim is required for Neovim provisioning." >&2
    exit 1
fi

if [[ -d "$lazy_path/.git" ]]; then
    echo "lazy.nvim already installed at $lazy_path"
elif [[ -e "$lazy_path" ]]; then
    echo "Error: $lazy_path exists but is not a lazy.nvim git checkout." >&2
    exit 1
else
    mkdir -p "$(dirname "$lazy_path")"
    git clone --filter=blob:none --branch=stable "$lazy_repo" "$lazy_path"
    echo "Installed lazy.nvim to $lazy_path"
fi

echo "Syncing Neovim plugins (headless)..."
nvim --headless "+Lazy! sync" +qa

echo "Installing Mason LSP servers (headless): ${required_lsp_servers[*]}"
nvim --headless "+MasonInstall ${required_lsp_servers[*]}" +qa

echo "Neovim provisioning complete."

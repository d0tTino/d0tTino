#!/usr/bin/env bash
set -euo pipefail

lazy_path="${XDG_DATA_HOME:-$HOME/.local/share}/nvim/lazy/lazy.nvim"
lazy_repo="https://github.com/folke/lazy.nvim.git"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
lsp_servers_file="$repo_root/dotfiles/nvim/.config/nvim/lsp_servers.txt"
minimum_nvim_version="0.8"
benchmark_script="$repo_root/scripts/benchmark_nvim_startup.sh"
benchmark_startup="${TINO_NVIM_BENCHMARK_STARTUP:-0}"
benchmark_threshold="${TINO_NVIM_MAX_STARTUP_MS:-}"

version_gte() {
    local current="$1"
    local minimum="$2"
    [[ "$(printf '%s\n%s\n' "$minimum" "$current" | sort -V | head -n1)" == "$minimum" ]]
}

if [[ ! -f "$lsp_servers_file" ]]; then
    echo "Error: expected canonical LSP server inventory at $lsp_servers_file" >&2
    exit 1
fi

mapfile -t required_lsp_servers < <(sed -e 's/#.*$//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' "$lsp_servers_file" | awk 'NF')
if [[ ${#required_lsp_servers[@]} -eq 0 ]]; then
    echo "Error: no LSP servers were defined in $lsp_servers_file" >&2
    exit 1
fi

if ! command -v nvim >/dev/null 2>&1; then
    echo "Error: nvim is required for Neovim provisioning." >&2
    exit 1
fi

nvim_version_line="$(nvim --version | head -n1)"
if [[ "$nvim_version_line" =~ v([0-9]+\.[0-9]+(\.[0-9]+)?) ]]; then
    nvim_version="${BASH_REMATCH[1]}"
else
    echo "Error: could not parse Neovim version from: $nvim_version_line" >&2
    exit 1
fi

if ! version_gte "$nvim_version" "$minimum_nvim_version"; then
    echo "Error: Neovim $minimum_nvim_version+ is required for setup-nvim.sh (found $nvim_version)." >&2
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

if [[ "$benchmark_startup" == "1" ]]; then
    if [[ -f "$benchmark_script" ]]; then
        echo "Running startup benchmark (TINO_NVIM_BENCHMARK_STARTUP=1)..."
        if [[ -n "$benchmark_threshold" ]]; then
            TINO_NVIM_MAX_STARTUP_MS="$benchmark_threshold" bash "$benchmark_script"
        else
            bash "$benchmark_script"
        fi
    else
        echo "Warning: benchmark script not found at $benchmark_script" >&2
    fi
fi

echo "Neovim provisioning complete."

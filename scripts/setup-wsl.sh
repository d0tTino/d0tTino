#!/usr/bin/env bash
set -euo pipefail

# Ensure sudo is available before attempting any privileged commands
if ! command -v sudo >/dev/null; then
    if [ "$(id -u)" -eq 0 ]; then
        sudo() { "$@"; }
    else
        echo "Error: sudo is required but not installed." >&2
        echo "Please install sudo using your package manager and re-run this script." >&2
        exit 1
    fi
fi

# Fail fast if the expected package manager is missing
if ! command -v apt-get >/dev/null; then
    echo "Error: apt-get is required but not installed." >&2
    echo "Please run this script on a Debian/Ubuntu system with apt-get available." >&2
    exit 1
fi

sudo apt-get update
sudo apt-get install -y \
    git \
    ripgrep \
    fd-find \
    git-delta \
    bat \
    fzf \
    build-essential \
    starship \
    zoxide \
    curl

# Verify that curl is available; exit with a helpful message if not.
if ! command -v curl >/dev/null; then
    echo "Error: curl is required but could not be installed." >&2
    echo "Please install curl using your package manager and re-run this script." >&2
    exit 1
fi

# Ensure starship is available; install from the official script if apt didn't
# provide it.
if ! command -v starship >/dev/null; then
    curl -sS https://starship.rs/install.sh | sh -s -- -y
    if ! command -v starship >/dev/null; then
        echo "Error: starship installation failed." >&2
        exit 1
    fi
fi

# Ensure zoxide is available; prefer Cargo for installation with a curl-based
# fallback when Cargo is missing.
if ! command -v zoxide >/dev/null; then
    if command -v cargo >/dev/null; then
        cargo install --locked zoxide
    else
        curl -sS https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh \
            | bash -s -- --yes
    fi
    if ! command -v zoxide >/dev/null; then
        echo "Error: zoxide installation failed." >&2
        exit 1
    fi
fi

# Provide helpful symlinks for batcat and fdfind if they exist
if command -v batcat >/dev/null && ! command -v bat >/dev/null; then
    sudo ln -sf "$(command -v batcat)" /usr/local/bin/bat
fi
if command -v fdfind >/dev/null && ! command -v fd >/dev/null; then
    sudo ln -sf "$(command -v fdfind)" /usr/local/bin/fd
fi

# Add starship and zoxide initialization to ~/.bashrc if missing
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bashrc="$HOME/.bashrc"
if [ ! -f "$bashrc" ]; then
    touch "$bashrc"
fi
if ! grep -Fq 'starship init bash' "$bashrc" 2>/dev/null; then
    starship_config_path="$repo_root/starship.toml"
    {
        printf 'starship_config="%s"\n' "$starship_config_path"
        printf 'if command -v starship >/dev/null; then\n'
        printf '    eval "$(starship init bash --config \"$starship_config\")"\n'
        printf 'fi\n'
        printf 'if command -v zoxide >/dev/null; then\n'
        printf '    eval "$(zoxide init bash)"\n'
        printf 'fi\n'
    } >>"$bashrc"

fi

#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y \
    git \
    ripgrep \
    fd-find \
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
fi

# Provide helpful symlinks for batcat and fdfind if they exist
if command -v batcat >/dev/null && ! command -v bat >/dev/null; then
    sudo ln -sf $(command -v batcat) /usr/local/bin/bat
fi
if command -v fdfind >/dev/null && ! command -v fd >/dev/null; then
    sudo ln -sf $(command -v fdfind) /usr/local/bin/fd
fi

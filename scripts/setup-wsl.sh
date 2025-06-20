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
    zoxide

# Provide helpful symlinks for batcat and fdfind if they exist
if command -v batcat >/dev/null && ! command -v bat >/dev/null; then
    sudo ln -sf $(command -v batcat) /usr/local/bin/bat
fi
if command -v fdfind >/dev/null && ! command -v fd >/dev/null; then
    sudo ln -sf $(command -v fdfind) /usr/local/bin/fd
fi

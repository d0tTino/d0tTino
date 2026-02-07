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
    curl \
    zsh \
    neovim \
    tmux

install_terminal() {
    local terminal="alacritty"

    if command -v "$terminal" >/dev/null 2>&1; then
        return
    fi

    sudo apt-get install -y "$terminal"

    if ! command -v "$terminal" >/dev/null 2>&1; then
        echo "Error: $terminal installation failed." >&2
        exit 1
    fi
}

install_terminal

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

# Ensure zsh is available.
if ! command -v zsh >/dev/null; then
    echo "Error: zsh installation failed." >&2
    exit 1
fi

# Provide helpful symlinks for batcat and fdfind if they exist
if command -v batcat >/dev/null && ! command -v bat >/dev/null; then
    sudo ln -sf "$(command -v batcat)" /usr/local/bin/bat
fi
if command -v fdfind >/dev/null && ! command -v fd >/dev/null; then
    sudo ln -sf "$(command -v fdfind)" /usr/local/bin/fd
fi

# Set zsh as the default shell only when it is not already the login shell.
zsh_path="$(command -v zsh)"
if command -v chsh >/dev/null; then
    current_shell="$(getent passwd "$(id -un)" 2>/dev/null | cut -d: -f7 || true)"
    if [ -z "$current_shell" ]; then
        current_shell="${SHELL:-}"
    fi

    if [ "$current_shell" != "$zsh_path" ]; then
        chsh -s "$zsh_path"
    fi
fi

#!/usr/bin/env bash
set -euo pipefail

host_override=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --host)
            if [[ -z "${2:-}" ]]; then
                echo "Error: --host requires a hostname" >&2
                exit 1
            fi
            host_override="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

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

# Keep baseline CLI dependencies aligned with scripts/install_common.sh
sudo apt-get install -y \
    curl \
    unzip \
    git \
    zsh \
    starship \
    tmux \
    neovim \
    cargo \
    stow \
    ripgrep \
    fd-find \
    git-delta \
    bat \
    fzf \
    build-essential \
    zoxide

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$script_dir/setup-ghostty.sh" ]]; then
    if ! bash "$script_dir/setup-ghostty.sh"; then
        echo "Warning: Ghostty setup failed; continuing." >&2
    fi
fi

ensure_shallow_plugin_repo() {
    local repo_url="$1"
    local repo_name="$2"
    local plugin_dir="$HOME/.local/share/zsh/plugins/$repo_name"

    mkdir -p "$HOME/.local/share/zsh/plugins"

    if [ -d "$plugin_dir/.git" ]; then
        git -C "$plugin_dir" remote set-url origin "$repo_url"
        git -C "$plugin_dir" fetch --depth 1 origin

        local origin_head=""
        origin_head="$(git -C "$plugin_dir" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || true)"
        if [ -z "$origin_head" ]; then
            git -C "$plugin_dir" remote set-head origin --auto >/dev/null 2>&1 || true
            origin_head="$(git -C "$plugin_dir" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || true)"
        fi

        if [ -n "$origin_head" ]; then
            git -C "$plugin_dir" checkout --quiet "${origin_head#origin/}" 2>/dev/null || true
            git -C "$plugin_dir" reset --hard "$origin_head"
        fi
    elif [ -d "$plugin_dir" ]; then
        echo "Error: $plugin_dir exists but is not a git repository." >&2
        exit 1
    else
        git clone --depth 1 "$repo_url" "$plugin_dir"
    fi
}

ensure_shallow_plugin_repo "https://github.com/zsh-users/zsh-autosuggestions" "zsh-autosuggestions"
ensure_shallow_plugin_repo "https://github.com/zsh-users/zsh-syntax-highlighting" "zsh-syntax-highlighting"

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
        cargo install --locked zoxide || true
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

dotfiles_args=()
repo_root="$(cd "$script_dir/.." && pwd)"
if [[ -n "$host_override" ]]; then
    if [[ ! -d "$repo_root/hosts/$host_override" ]]; then
        echo "Error: host overlay '$host_override' does not exist" >&2
        exit 1
    fi
    dotfiles_args+=(--host "$host_override")
else
    detected_host="$(hostname 2>/dev/null || true)"
    if [[ -n "$detected_host" && -d "$repo_root/hosts/$detected_host" ]]; then
        dotfiles_args+=(--host "$detected_host")
    fi
fi
bash "$script_dir/install_dotfiles.sh" --conflict=abort "${dotfiles_args[@]}"

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

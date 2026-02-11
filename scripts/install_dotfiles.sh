#!/usr/bin/env bash
set -euo pipefail

# Ensure GNU Stow is available before proceeding
if ! command -v stow >/dev/null 2>&1; then
    echo "Error: GNU Stow is required but not installed." >&2
    exit 1
fi

usage() {
    cat <<USAGE
Usage: $(basename "$0") [--dry-run] [--target DIR] [--packages LIST] [--host NAME]

Link dotfile packages into the target directory using GNU Stow.

  -n, --dry-run      Show what would be done without modifying files
  -t, --target DIR   Target directory (defaults to $HOME)
  -p, --packages     Comma-separated package list (defaults to: shell,nvim,tmux,terminal)
      --host NAME    Apply host overlay from hosts/NAME after core packages
  -h, --help         Show this help message
USAGE
}

dry_run=0
target="$HOME"
packages_csv=""
host_name=""
core_packages=(shell nvim tmux terminal)

while [[ $# -gt 0 ]]; do
    case "$1" in
        -n|--dry-run)
            dry_run=1
            shift
            ;;
        -t|--target)
            if [[ -z "${2:-}" ]]; then
                echo "Error: --target requires a directory" >&2
                exit 1
            fi
            target="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -p|--packages)
            if [[ -z "${2:-}" ]]; then
                echo "Error: --packages requires a comma-separated list" >&2
                exit 1
            fi
            packages_csv="$2"
            shift 2
            ;;
        --host)
            if [[ -z "${2:-}" ]]; then
                echo "Error: --host requires a hostname" >&2
                exit 1
            fi
            host_name="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage
            exit 1
            ;;
    esac
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dotfiles_dir="$repo_root/dotfiles"
hosts_dir="$repo_root/hosts"

declare -a selected_packages=()
if [[ -n "$packages_csv" ]]; then
    IFS=',' read -r -a selected_packages <<< "$packages_csv"
else
    selected_packages=("${core_packages[@]}")
fi

for pkg in "${selected_packages[@]}"; do
    if [[ -z "$pkg" ]]; then
        echo "Error: empty package name in --packages list" >&2
        exit 1
    fi
    if [[ ! -d "$dotfiles_dir/$pkg" ]]; then
        echo "Error: dotfiles package '$pkg' does not exist" >&2
        exit 1
    fi
done

if [[ -n "$host_name" && ! -d "$hosts_dir/$host_name" ]]; then
    echo "Error: host overlay '$host_name' does not exist" >&2
    exit 1
fi

if [[ ! -d "$target" ]]; then
    mkdir -p "$target"
    if [[ $dry_run -eq 1 ]]; then
        echo "Created target directory $target for dry-run validation"
    fi
fi

link_package() {
    local base_dir="$1"
    local pkg="$2"
    echo "Processing $pkg" >&2
    local output
    output=$(stow -d "$base_dir" -t "$target" -nv "$pkg" 2>&1 || true)
    if echo "$output" | grep -q "existing target"; then
        echo "$output"
        if [[ $dry_run -eq 1 ]]; then
            return
        fi
        read -r -p "Overwrite these files for $pkg? [y/N] " resp
        if [[ ! $resp =~ ^[Yy]$ ]]; then
            echo "Skipping $pkg" >&2
            return
        fi
        files=$(echo "$output" | grep "existing target" | awk -F: '{print $2}' | xargs || true)
        for f in $files; do
            rm -rf "$target/$f"
        done
    fi
    if [[ $dry_run -eq 1 ]]; then
        stow -d "$base_dir" -t "$target" -nv "$pkg"
    else
        stow -d "$base_dir" -t "$target" -v "$pkg"
    fi
}

for pkg in "${selected_packages[@]}"; do
    link_package "$dotfiles_dir" "$pkg"
done

if [[ -n "$host_name" ]]; then
    link_package "$hosts_dir" "$host_name"
fi

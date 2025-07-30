#!/usr/bin/env bash
set -euo pipefail

# Ensure GNU Stow is available before proceeding
if ! command -v stow >/dev/null 2>&1; then
    echo "Error: GNU Stow is required but not installed." >&2
    exit 1
fi

usage() {
    cat <<'USAGE'
Usage: $(basename "$0") [--dry-run] [--target DIR]

Link dotfile packages into the target directory using GNU Stow.

  -n, --dry-run      Show what would be done without modifying files
  -t, --target DIR   Target directory (defaults to $HOME)
  -h, --help         Show this help message
USAGE
}

dry_run=0
target="$HOME"

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
        *)
            echo "Unknown option: $1" >&2
            usage
            exit 1
            ;;
    esac
done

stow_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../dotfiles" && pwd)"

if [[ ! -d "$target" ]]; then
    if [[ $dry_run -eq 1 ]]; then
        echo "Target directory $target would be created"
    else
        mkdir -p "$target"
    fi
fi

link_package() {
    local pkg="$1"
    echo "Processing $pkg" >&2
    local output
    output=$(stow -d "$stow_dir" -t "$target" -nv "$pkg" 2>&1 || true)
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
        stow -d "$stow_dir" -t "$target" -nv "$pkg"
    else
        stow -d "$stow_dir" -t "$target" -v "$pkg"
    fi
}

for pkg_path in "$stow_dir"/*; do
    [[ -d "$pkg_path" ]] || continue
    link_package "$(basename "$pkg_path")"
done

#!/usr/bin/env bash
set -euo pipefail

# Ensure GNU Stow is available before proceeding
if ! command -v stow >/dev/null 2>&1; then
    echo "Error: GNU Stow is required but not installed." >&2
    exit 1
fi

usage() {
    cat <<USAGE
Usage: $(basename "$0") [--dry-run] [--target DIR] [--packages LIST] [--host NAME] [--conflict MODE]

Link dotfile packages into the target directory using GNU Stow.

  -n, --dry-run      Show what would be done without modifying files
  -t, --target DIR   Target directory (defaults to $HOME)
  -p, --packages     Comma-separated package list (defaults to: shell,nvim,tmux,terminal)
      --host NAME    Apply host overlay from hosts/NAME after core packages
      --conflict     Conflict handling mode: abort (default), backup, overwrite
  -h, --help         Show this help message
USAGE
}

dry_run=0
target="$HOME"
packages_csv=""
host_name=""
conflict_mode="abort"
core_packages=(shell nvim tmux terminal)

is_tty=false
if [[ -t 0 && -t 1 ]]; then
    is_tty=true
fi

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
        --conflict)
            if [[ -z "${2:-}" ]]; then
                echo "Error: --conflict requires a mode (abort|backup|overwrite)" >&2
                exit 1
            fi
            conflict_mode="$2"
            shift 2
            ;;
        --conflict=*)
            conflict_mode="${1#*=}"
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage
            exit 1
            ;;
    esac
done

case "$conflict_mode" in
    abort|backup|overwrite) ;;
    *)
        echo "Error: unsupported --conflict mode '$conflict_mode' (expected abort, backup, or overwrite)" >&2
        exit 1
        ;;
esac

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
    local conflicts=()
    output=$(stow -d "$base_dir" -t "$target" -nv "$pkg" 2>&1 || true)
    if echo "$output" | grep -q "existing target"; then
        echo "$output"
        if [[ $dry_run -eq 1 ]]; then
            return
        fi
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            conflicts+=("$line")
        done < <(
            echo "$output" | sed -n -E 's/.*existing target[^:]*: (.*)$/\1/p'
        )

        if [[ ${#conflicts[@]} -eq 0 ]]; then
            echo "Error: stow reported conflicts for $pkg but no paths were parsed." >&2
            return 1
        fi

        case "$conflict_mode" in
            abort)
                echo "Aborting due to existing targets in package '$pkg'. Re-run with --conflict=backup or --conflict=overwrite." >&2
                return 1
                ;;
            backup)
                local timestamp backup_root rel_path backup_path
                timestamp="$(date +%Y%m%d%H%M%S)"
                backup_root="$target/.dotfiles-backups/$timestamp/$pkg"
                echo "Backing up conflicting targets to $backup_root" >&2
                for rel_path in "${conflicts[@]}"; do
                    backup_path="$backup_root/$rel_path"
                    mkdir -p "$(dirname "$backup_path")"
                    mv "$target/$rel_path" "$backup_path"
                done
                ;;
            overwrite)
                local rel_path
                if ! $is_tty; then
                    echo "Running non-interactively with explicit --conflict=overwrite; removing conflicting targets." >&2
                fi
                for rel_path in "${conflicts[@]}"; do
                    rm -rf "$target/$rel_path"
                done
                ;;
        esac
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

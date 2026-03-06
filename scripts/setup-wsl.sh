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

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
install_common_args=(--terminal ghostty --set-default-shell=force)

if [[ -n "$host_override" ]]; then
    install_common_args+=(--host "$host_override")
fi

bash "$script_dir/install_common.sh" "${install_common_args[@]}"

#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scripts_dir="$repo_root/scripts"

plan_mode=0
host_overlay=""
provider_override=""
set_default_shell_mode="prompt"
report_dir="${TINO_BOOTSTRAP_REPORT_DIR:-$repo_root/.cache/tino/bootstrap-dev-env}"

usage() {
    cat <<USAGE
Usage: $(basename "$0") [--plan] [--host NAME] [--provider NAME] [--set-default-shell MODE] [--report-dir DIR]

Declarative bootstrap for development environments with auditable stages.

  --plan            Print exact actions without mutating state
  --host NAME       Explicit host overlay passed to install_dotfiles.sh
  --provider NAME   Terminal provider override (ghostty|wezterm|kitty|alacritty|windows-terminal)
  --set-default-shell MODE
                    Default-shell policy forwarded to install_common.sh (prompt|force|skip; default: prompt)
  --report-dir DIR  Output directory for reports (default: $report_dir)
  -h, --help        Show this help message
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --plan)
            plan_mode=1
            shift
            ;;
        --host)
            host_overlay="${2:-}"
            shift 2
            ;;
        --provider)
            provider_override="${2:-}"
            shift 2
            ;;
        --set-default-shell)
            set_default_shell_mode="${2:-}"
            shift 2
            ;;
        --set-default-shell=*)
            set_default_shell_mode="${1#*=}"
            shift
            ;;
        --report-dir)
            report_dir="${2:-}"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

if [[ -z "$set_default_shell_mode" ]]; then
    echo "Error: --set-default-shell requires one of: prompt, force, skip" >&2
    exit 1
fi

case "$set_default_shell_mode" in
    prompt|force|skip) ;;
    *)
        echo "Error: unsupported --set-default-shell mode '$set_default_shell_mode' (expected: prompt, force, skip)" >&2
        exit 1
        ;;
esac

terminal_provider_supported() {
    case "$1" in
        ghostty|wezterm|kitty|alacritty|windows-terminal)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

resolve_host_overlay() {
    local raw_host="$1"
    local hosts_root="$repo_root/hosts"

    [[ -z "$raw_host" ]] && return 0

    local normalized_lower="${raw_host,,}"
    local normalized_slug
    normalized_slug="$(printf '%s' "$normalized_lower" | sed -E 's/[^a-z0-9]+/_/g; s/^_+|_+$//g')"
    local short_host="${normalized_lower%%.*}"
    local short_slug
    short_slug="$(printf '%s' "$short_host" | sed -E 's/[^a-z0-9]+/_/g; s/^_+|_+$//g')"

    local -a candidates=("$raw_host" "$normalized_lower" "$normalized_slug" "$short_host" "$short_slug")
    local candidate
    for candidate in "${candidates[@]}"; do
        [[ -z "$candidate" ]] && continue
        if [[ -d "$hosts_root/$candidate" ]]; then
            printf '%s' "$candidate"
            return 0
        fi
    done
}

resolve_provider() {
    local resolved_host="$1"
    local provider=""
    local defaults_path="$repo_root/dotfiles/terminal/.config/tino/terminal-defaults.sh"
    local host_override_path=""

    if [[ -f "$defaults_path" ]]; then
        # shellcheck disable=SC1090
        source "$defaults_path"
    fi

    if [[ -n "$resolved_host" ]]; then
        host_override_path="$repo_root/hosts/$resolved_host/.config/tino/host-overrides.sh"
        if [[ -f "$host_override_path" ]]; then
            # shellcheck disable=SC1090
            source "$host_override_path"
        fi
    fi

    provider="${provider_override:-${TINO_TERMINAL_PROVIDER:-}}"
    if [[ -z "$provider" ]]; then
        case "${OSTYPE:-}" in
            msys*|cygwin*|win32*|windows*) provider="windows-terminal" ;;
            *) provider="ghostty" ;;
        esac
    fi

    if ! terminal_provider_supported "$provider"; then
        echo "Error: unsupported provider '$provider'" >&2
        exit 1
    fi

    printf '%s' "$provider"
}

version_of() {
    local binary="$1"
    if command -v "$binary" >/dev/null 2>&1; then
        "$binary" --version 2>/dev/null | head -n1 || true
    else
        printf 'unavailable'
    fi
}

json_escape() {
    local value="$1"
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    value="${value//$'\n'/\\n}"
    printf '%s' "$value"
}

run_stage() {
    local stage="$1"
    local command="$2"

    planned_actions+=("$stage::$command")

    if [[ $plan_mode -eq 1 ]]; then
        skipped_steps+=("$stage (plan mode)")
        return 0
    fi

    eval "$command"
}

if [[ -z "$host_overlay" ]]; then
    detected_host="$(hostname 2>/dev/null || true)"
    host_overlay="$(resolve_host_overlay "$detected_host")"
fi

provider_chosen="$(resolve_provider "$host_overlay")"

mkdir -p "$report_dir"
json_report="$report_dir/bootstrap-summary.json"
text_report="$report_dir/bootstrap-summary.txt"
renderer_report="$report_dir/renderer-contract.json"

planned_actions=()
skipped_steps=()

dependency_install_mode="planned"
dependency_install_dry_run=1

# Stages
dependency_install_cmd="bash '$scripts_dir/install_common.sh' --dry-run --set-default-shell=skip --terminal '$provider_chosen'"
if [[ $plan_mode -eq 0 ]]; then
    dependency_install_cmd="bash '$scripts_dir/install_common.sh' --set-default-shell='$set_default_shell_mode' --terminal '$provider_chosen'"
    dependency_install_mode="applied"
    dependency_install_dry_run=0
fi
run_stage "dependency-install" "$dependency_install_cmd"

dotfiles_cmd="bash '$scripts_dir/install_dotfiles.sh' --conflict=abort"
if [[ -n "$host_overlay" ]]; then
    dotfiles_cmd+=" --host '$host_overlay'"
fi
run_stage "install-dotfiles" "$dotfiles_cmd"

run_stage "setup-nvim" "bash '$scripts_dir/setup-nvim.sh'"
run_stage "setup-terminal-provider" "bash '$scripts_dir/setup-terminal-provider.sh' '$provider_chosen'"
run_stage "renderer-contract-validation" "bash '$repo_root/dotfiles/terminal/.config/tino/validate-renderer-contract.sh' --report-format json --report-file '$renderer_report'"

versions_keys=(bash python nvim stow)
versions_values=("$(version_of bash)" "$(version_of python)" "$(version_of nvim)" "$(version_of stow)")
provider_binary="$provider_chosen"
if [[ "$provider_chosen" == "windows-terminal" ]]; then
    provider_binary="python"
fi
provider_version="$(version_of "$provider_binary")"

{
    printf 'Bootstrap development environment summary\n'
    printf '=====================================\n'
    printf 'Mode: %s\n' "$( [[ $plan_mode -eq 1 ]] && echo 'plan' || echo 'apply' )"
    printf 'Host overlay: %s\n' "${host_overlay:-none}"
    printf 'Provider chosen: %s\n' "$provider_chosen"
    printf 'Provider version: %s\n' "$provider_version"
    printf 'Dependency install mode: %s\n' "$dependency_install_mode"
    printf 'Dependency install dry-run: %s\n' "$( [[ $dependency_install_dry_run -eq 1 ]] && echo 'yes' || echo 'no' )"
    printf '\nPlanned actions:\n'
    for action in "${planned_actions[@]}"; do
        printf '  - %s\n' "$action"
    done
    if [[ ${#skipped_steps[@]} -gt 0 ]]; then
        printf '\nSkipped steps:\n'
        for skip in "${skipped_steps[@]}"; do
            printf '  - %s\n' "$skip"
        done
    fi
    printf '\nVersions:\n'
    for i in "${!versions_keys[@]}"; do
        printf '  - %s: %s\n' "${versions_keys[$i]}" "${versions_values[$i]}"
    done
} > "$text_report"

{
    printf '{\n'
    printf '  "mode": "%s",\n' "$( [[ $plan_mode -eq 1 ]] && echo 'plan' || echo 'apply' )"
    printf '  "host_overlay": "%s",\n' "$(json_escape "${host_overlay:-none}")"
    printf '  "provider_chosen": "%s",\n' "$(json_escape "$provider_chosen")"
    printf '  "provider_version": "%s",\n' "$(json_escape "$provider_version")"
    printf '  "dependency_install_mode": "%s",\n' "$(json_escape "$dependency_install_mode")"
    printf '  "dependency_install_dry_run": %s,\n' "$( [[ $dependency_install_dry_run -eq 1 ]] && echo 'true' || echo 'false' )"
    printf '  "planned_actions": [\n'
    for i in "${!planned_actions[@]}"; do
        comma=","
        [[ $i -eq $((${#planned_actions[@]}-1)) ]] && comma=""
        printf '    "%s"%s\n' "$(json_escape "${planned_actions[$i]}")" "$comma"
    done
    printf '  ],\n'
    printf '  "skipped_steps": [\n'
    for i in "${!skipped_steps[@]}"; do
        comma=","
        [[ $i -eq $((${#skipped_steps[@]}-1)) ]] && comma=""
        printf '    "%s"%s\n' "$(json_escape "${skipped_steps[$i]}")" "$comma"
    done
    printf '  ],\n'
    printf '  "versions": {\n'
    for i in "${!versions_keys[@]}"; do
        comma=","
        [[ $i -eq $((${#versions_keys[@]}-1)) ]] && comma=""
        printf '    "%s": "%s"%s\n' "$(json_escape "${versions_keys[$i]}")" "$(json_escape "${versions_values[$i]}")" "$comma"
    done
    printf '  }\n'
    printf '}\n'
} > "$json_report"

cat "$text_report"
echo "JSON report: $json_report"

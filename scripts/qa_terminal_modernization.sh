#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
report_dir="${TINO_QA_REPORT_DIR:-$repo_root/.cache/tino/qa-terminal-modernization}"
json_report="${TINO_QA_JSON_REPORT:-$report_dir/report.json}"
renderer_json_report="${TINO_QA_RENDERER_JSON_REPORT:-$report_dir/renderer-contract.json}"

resolve_host_overlay() {
    local hosts_root="$1"
    local raw_host="$2"

    if [[ -z "$raw_host" ]]; then
        return
    fi

    local normalized_lower="${raw_host,,}"
    local normalized_slug
    normalized_slug="$(printf '%s' "$normalized_lower" | sed -E 's/[^a-z0-9]+/_/g; s/^_+|_+$//g')"
    local short_host="${normalized_lower%%.*}"
    local short_slug
    short_slug="$(printf '%s' "$short_host" | sed -E 's/[^a-z0-9]+/_/g; s/^_+|_+$//g')"

    local -a candidates=(
        "$raw_host"
        "$normalized_lower"
        "$normalized_slug"
        "$short_host"
        "$short_slug"
    )

    local candidate
    for candidate in "${candidates[@]}"; do
        [[ -z "$candidate" ]] && continue
        if [[ -d "$hosts_root/$candidate" ]]; then
            printf '%s\n' "$candidate"
            return
        fi
    done
}

resolve_benchmark_threshold() {
    local default_threshold="100"
    local selected_host="${TINO_HOST_PROFILE:-}"

    if [[ -z "$selected_host" ]]; then
        local detected_host
        detected_host="$(hostname 2>/dev/null || true)"
        selected_host="$(resolve_host_overlay "$repo_root/hosts" "$detected_host")"
    fi

    if [[ -n "$selected_host" ]]; then
        local host_override_path="$repo_root/hosts/$selected_host/.config/tino/host-overrides.sh"
        if [[ -f "$host_override_path" ]]; then
            local host_threshold=""
            local profile_default_threshold=""
            host_threshold="$({ source "$host_override_path"; printf '%s' "${TINO_NVIM_MAX_STARTUP_MS:-}"; })"
            profile_default_threshold="$({ source "$host_override_path"; printf '%s' "${TINO_NVIM_PROFILE_DEFAULT_MAX_STARTUP_MS:-}"; })"
            if [[ -n "$host_threshold" ]]; then
                printf '%s\n' "$host_threshold"
                return
            fi
            if [[ -n "$profile_default_threshold" ]]; then
                printf '%s\n' "$profile_default_threshold"
                return
            fi
        fi
    fi

    printf '%s\n' "$default_threshold"
}

benchmark_threshold="${TINO_QA_NVIM_MAX_STARTUP_MS:-${TINO_NVIM_MAX_STARTUP_MS:-$(resolve_benchmark_threshold)}}"
zsh_startup_budget_warm_ms="${TINO_QA_ZSH_STARTUP_BUDGET_WARM_MS:-${TINO_ZSH_STARTUP_BUDGET_WARM_MS:-80}}"
zsh_startup_budget_cold_ms="${TINO_QA_ZSH_STARTUP_BUDGET_COLD_MS:-${TINO_ZSH_STARTUP_BUDGET_COLD_MS:-150}}"
zsh_startup_use_zprof="${TINO_QA_ZSH_STARTUP_USE_ZPROF:-0}"
minimum_nvim_version="0.10"

mkdir -p "$report_dir"

declare -a CHECK_IDS=()
declare -a CHECK_DESCRIPTIONS=()
declare -a CHECK_STATUSES=()
declare -a CHECK_DETAILS=()

json_escape() {
    local value="$1"
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    value="${value//$'\n'/\\n}"
    value="${value//$'\r'/}"
    printf '%s' "$value"
}

record_check() {
    CHECK_IDS+=("$1")
    CHECK_DESCRIPTIONS+=("$2")
    CHECK_STATUSES+=("$3")
    CHECK_DETAILS+=("$4")
}

run_check_command() {
    local check_id="$1"
    local description="$2"
    shift 2

    local output
    if output="$("$@" 2>&1)"; then
        record_check "$check_id" "$description" "pass" "${output:-ok}"
        return 0
    fi

    record_check "$check_id" "$description" "fail" "${output:-command failed}"
    return 1
}

capture_terminal_runtime_diagnostic() {
    local check_id="$1"
    local description="$2"
    local binary_name="$3"
    local version_subcommand="$4"
    local hint_subcommand="$5"
    local hint_label="$6"

    if ! command -v "$binary_name" >/dev/null 2>&1; then
        record_check "$check_id" "$description" "warn" "$binary_name not found on PATH; runtime diagnostics skipped"
        return
    fi

    local version_output=""
    if ! version_output="$(bash -lc "$version_subcommand" 2>&1)"; then
        record_check "$check_id" "$description" "warn" "$binary_name found but failed to collect version diagnostics: ${version_output:-command failed}"
        return
    fi

    local details="version: ${version_output:-unknown}"
    if [[ -n "$hint_subcommand" ]]; then
        local hint_output=""
        if hint_output="$(bash -lc "$hint_subcommand" 2>&1)"; then
            details+=" | ${hint_label}: ${hint_output:-none}"
            record_check "$check_id" "$description" "pass" "$details"
            return
        fi

        details+=" | ${hint_label}: unavailable (${hint_output:-command failed})"
        record_check "$check_id" "$description" "warn" "$details"
        return
    fi

    record_check "$check_id" "$description" "pass" "$details"
}

measure_zsh_startup_ms() {
    local zsh_path="$1"
    local profile_flag="$2"

    local elapsed
    elapsed="$(TIMEFORMAT='%3R'; { time env \
        ZDOTDIR="$repo_root/dotfiles/shell" \
        HOME="$HOME" \
        TINO_ZSH_PROFILE="$profile_flag" \
        TINO_ZSH_DEFER="1" \
        "$zsh_path" -i -c 'exit' >/dev/null 2>/dev/null; } 2>&1)"

    python3 -c 'import sys
raw=sys.argv[1].strip()
if not raw:
    raise SystemExit(1)
print(f"{float(raw) * 1000:.2f}")' "$elapsed"
}

zshrc_path="$repo_root/dotfiles/shell/.zshrc"
starship_config_path="$repo_root/dotfiles/shell/.config/starship.toml"
tmux_config_path="$repo_root/dotfiles/tmux/.tmux.conf"
renderer_contract_script="$repo_root/dotfiles/terminal/.config/tino/validate-renderer-contract.sh"
terminal_profile_script="$repo_root/dotfiles/terminal/.config/tino/terminal-profile.sh"
terminal_defaults_path="$repo_root/dotfiles/terminal/.config/tino/terminal-defaults.sh"
lockfile_check_script="$repo_root/scripts/check-nvim-lockfile.py"
benchmark_script="$repo_root/scripts/benchmark_nvim_startup.sh"

if [[ -f "$zshrc_path" ]]; then
    record_check "zsh_config_presence" "dotfiles/shell/.zshrc exists" "pass" "$zshrc_path"
else
    record_check "zsh_config_presence" "dotfiles/shell/.zshrc exists" "fail" "missing: $zshrc_path"
fi

if rg -q 'zsh-autosuggestions/zsh-autosuggestions\.zsh' "$zshrc_path" \
    && rg -q 'zsh-syntax-highlighting/zsh-syntax-highlighting\.zsh' "$zshrc_path"; then
    record_check "zsh_plugin_declarations" "zsh plugin entrypoints are declared in .zshrc" "pass" "autosuggestions + syntax-highlighting declarations found"
else
    record_check "zsh_plugin_declarations" "zsh plugin entrypoints are declared in .zshrc" "fail" "missing required plugin source declarations in .zshrc"
fi

zsh_plugin_root="${ZSH_PLUGIN_DIR:-$HOME/.local/share/zsh/plugins}"
if [[ -r "$zsh_plugin_root/zsh-autosuggestions/zsh-autosuggestions.zsh" ]]; then
    record_check "zsh_plugin_path_autosuggestions" "zsh-autosuggestions plugin file is readable" "pass" "$zsh_plugin_root/zsh-autosuggestions/zsh-autosuggestions.zsh"
else
    record_check "zsh_plugin_path_autosuggestions" "zsh-autosuggestions plugin file is readable" "warn" "missing runtime plugin path: $zsh_plugin_root/zsh-autosuggestions/zsh-autosuggestions.zsh"
fi

if [[ -r "$zsh_plugin_root/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]]; then
    record_check "zsh_plugin_path_syntax_highlighting" "zsh-syntax-highlighting plugin file is readable" "pass" "$zsh_plugin_root/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
else
    record_check "zsh_plugin_path_syntax_highlighting" "zsh-syntax-highlighting plugin file is readable" "warn" "missing runtime plugin path: $zsh_plugin_root/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
fi

if command -v zsh >/dev/null 2>&1; then
    zsh_path="$(command -v zsh)"
    profile_flag="0"
    method_label="timing"
    if [[ "$zsh_startup_use_zprof" == "1" ]]; then
        profile_flag="1"
        method_label="timing+zprof"
    fi

    cold_ms="$(measure_zsh_startup_ms "$zsh_path" "$profile_flag" 2>/dev/null || true)"
    warm_ms="$(measure_zsh_startup_ms "$zsh_path" "$profile_flag" 2>/dev/null || true)"

    if [[ -z "$cold_ms" || -z "$warm_ms" ]]; then
        record_check "zsh_startup_threshold" "zsh startup benchmark is within warm/cold thresholds" "fail" "unable to measure zsh startup time (method=${method_label})"
    elif python3 -c 'import sys
warm=float(sys.argv[1]); warm_budget=float(sys.argv[2]); cold=float(sys.argv[3]); cold_budget=float(sys.argv[4])
raise SystemExit(0 if warm <= warm_budget and cold <= cold_budget else 1)' "$warm_ms" "$zsh_startup_budget_warm_ms" "$cold_ms" "$zsh_startup_budget_cold_ms"; then
        record_check "zsh_startup_threshold" "zsh startup benchmark is within warm/cold thresholds" "pass" "method=${method_label} warm=${warm_ms}ms<=${zsh_startup_budget_warm_ms}ms cold=${cold_ms}ms<=${zsh_startup_budget_cold_ms}ms"
    elif python3 -c 'import sys
warm=float(sys.argv[1]); warm_budget=float(sys.argv[2]); cold=float(sys.argv[3]); cold_budget=float(sys.argv[4])
raise SystemExit(0 if warm <= warm_budget or cold <= cold_budget else 1)' "$warm_ms" "$zsh_startup_budget_warm_ms" "$cold_ms" "$zsh_startup_budget_cold_ms"; then
        record_check "zsh_startup_threshold" "zsh startup benchmark is within warm/cold thresholds" "warn" "method=${method_label} warm=${warm_ms}ms (budget=${zsh_startup_budget_warm_ms}ms), cold=${cold_ms}ms (budget=${zsh_startup_budget_cold_ms}ms)"
    else
        record_check "zsh_startup_threshold" "zsh startup benchmark is within warm/cold thresholds" "fail" "method=${method_label} warm=${warm_ms}ms>${zsh_startup_budget_warm_ms}ms cold=${cold_ms}ms>${zsh_startup_budget_cold_ms}ms"
    fi
else
    record_check "zsh_startup_threshold" "zsh startup benchmark is within warm/cold thresholds" "warn" "zsh binary not found on PATH; skipped startup benchmark"
fi

run_check_command "starship_toml_parse" "starship TOML parses cleanly" \
    python3 -c 'import pathlib, tomllib; tomllib.loads(pathlib.Path(__import__("sys").argv[1]).read_text(encoding="utf-8")); print("toml parse ok")' "$starship_config_path" || true

if command -v starship >/dev/null 2>&1; then
    run_check_command "starship_cli_validation" "starship can render effective config" \
        starship print-config --config "$starship_config_path" || true
else
    record_check "starship_cli_validation" "starship can render effective config" "warn" "starship binary not found on PATH; skipped CLI validation"
fi

run_check_command "nvim_lockfile" "Neovim lazy-lock.json covers declared plugins" \
    python3 "$lockfile_check_script" || true

if command -v nvim >/dev/null 2>&1; then
    nvim_version_line="$(nvim --version | head -n1)"
    if [[ "$nvim_version_line" =~ v([0-9]+\.[0-9]+(\.[0-9]+)?) ]]; then
        nvim_version="${BASH_REMATCH[1]}"
        if [[ "$(printf '%s\n%s\n' "$minimum_nvim_version" "$nvim_version" | sort -V | head -n1)" == "$minimum_nvim_version" ]]; then
            record_check "nvim_version_policy" "Neovim version meets minimum supported baseline (${minimum_nvim_version}+)" "pass" "found Neovim $nvim_version"
        else
            record_check "nvim_version_policy" "Neovim version meets minimum supported baseline (${minimum_nvim_version}+)" "fail" "found Neovim $nvim_version; requires ${minimum_nvim_version}+ for modern Lua/LSP architecture"
        fi
    else
        record_check "nvim_version_policy" "Neovim version meets minimum supported baseline (${minimum_nvim_version}+)" "fail" "unable to parse Neovim version from: $nvim_version_line"
    fi
else
    record_check "nvim_version_policy" "Neovim version meets minimum supported baseline (${minimum_nvim_version}+)" "warn" "nvim binary not found on PATH; skipped version gate"
fi

required_apply_binaries=(zsh starship tmux nvim stow rg fd)
missing_apply_binaries=()
for binary in "${required_apply_binaries[@]}"; do
    if ! command -v "$binary" >/dev/null 2>&1; then
        missing_apply_binaries+=("$binary")
    fi
done

if (( ${#missing_apply_binaries[@]} == 0 )); then
    record_check "bootstrap_apply_binaries" "bootstrap apply-mode dependencies are present on PATH" "pass" "found: ${required_apply_binaries[*]}"
else
    record_check "bootstrap_apply_binaries" "bootstrap apply-mode dependencies are present on PATH" "fail" "missing: ${missing_apply_binaries[*]} (run ./scripts/bootstrap-dev-env.sh in apply mode)"
fi

if command -v nvim >/dev/null 2>&1; then
    run_check_command "nvim_startup_threshold" "Neovim startup benchmark is within threshold (${benchmark_threshold} ms)" \
        env TINO_NVIM_MAX_STARTUP_MS="$benchmark_threshold" bash "$benchmark_script" || true
else
    record_check "nvim_startup_threshold" "Neovim startup benchmark is within threshold (${benchmark_threshold} ms)" "warn" "nvim binary not found on PATH; skipped startup benchmark"
fi

if [[ -f "$tmux_config_path" ]]; then
    record_check "tmux_config_presence" "dotfiles/tmux/.tmux.conf exists" "pass" "$tmux_config_path"
else
    record_check "tmux_config_presence" "dotfiles/tmux/.tmux.conf exists" "fail" "missing: $tmux_config_path"
fi

if grep -Fq '.tmux/plugins/tpm/tpm' "$tmux_config_path" \
    && grep -Fq 'TPM missing: run ./scripts/install_common.sh' "$tmux_config_path"; then
    record_check "tmux_tpm_guard" "tmux config keeps TPM runtime guard" "pass" "TPM guard stanza present"
else
    record_check "tmux_tpm_guard" "tmux config keeps TPM runtime guard" "fail" "TPM guard stanza missing from tmux config"
fi

if command -v tmux >/dev/null 2>&1; then
    tmux_socket="tino-qa-$$"
    if tmux -f "$tmux_config_path" -L "$tmux_socket" start-server >/tmp/tino-qa-tmux.log 2>&1; then
        tmux -L "$tmux_socket" kill-server >/dev/null 2>&1 || true
        record_check "tmux_runtime_sanity" "tmux can start with managed config" "pass" "tmux started successfully with -f dotfiles/tmux/.tmux.conf"
    else
        details="$(cat /tmp/tino-qa-tmux.log)"
        tmux -L "$tmux_socket" kill-server >/dev/null 2>&1 || true
        record_check "tmux_runtime_sanity" "tmux can start with managed config" "fail" "${details:-tmux failed to start with managed config}"
    fi
else
    record_check "tmux_runtime_sanity" "tmux can start with managed config" "warn" "tmux binary not found on PATH; skipped runtime sanity"
fi


active_host_profile="${TINO_HOST_PROFILE:-}"
if [[ -z "$active_host_profile" ]]; then
    detected_host_for_profile="$(hostname 2>/dev/null || true)"
    active_host_profile="$(resolve_host_overlay "$repo_root/hosts" "$detected_host_for_profile")"
fi

active_provider_default=""
if [[ -f "$terminal_defaults_path" ]]; then
    active_provider_default="$(
        unset TINO_TERMINAL_PROVIDER
        source "$terminal_defaults_path"
        if [[ -n "$active_host_profile" ]]; then
            host_override_path="$repo_root/hosts/$active_host_profile/.config/tino/host-overrides.sh"
            if [[ -f "$host_override_path" ]]; then
                source "$host_override_path"
            fi
        fi
        printf '%s' "${TINO_TERMINAL_PROVIDER:-}"
    )"
fi

canonical_provider=""
if [[ -x "$terminal_profile_script" ]]; then
    canonical_provider="$(bash "$terminal_profile_script" --canonical-provider 2>/dev/null || true)"
fi

if [[ -z "$canonical_provider" ]]; then
    canonical_provider="ghostty"
fi

if [[ -z "$active_provider_default" ]]; then
    record_check "terminal_provider_default_policy" "active host default provider matches canonical provider policy" "warn" "unable to resolve active provider default from terminal defaults/host overrides"
elif [[ "$active_provider_default" == "$canonical_provider" ]]; then
    record_check "terminal_provider_default_policy" "active host default provider matches canonical provider policy" "pass" "active_default=$active_provider_default canonical=$canonical_provider host_profile=${active_host_profile:-none}"
else
    record_check "terminal_provider_default_policy" "active host default provider matches canonical provider policy" "warn" "active_default=$active_provider_default canonical=$canonical_provider host_profile=${active_host_profile:-none}; non-canonical defaults should be treated as compatibility fallback"
fi

if [[ -x "$renderer_contract_script" ]]; then
    run_check_command "renderer_contract" "terminal renderer contract validation passes" \
        bash "$renderer_contract_script" --report-format json --report-file "$renderer_json_report" || true
else
    record_check "renderer_contract" "terminal renderer contract validation passes" "fail" "renderer contract script missing or not executable: $renderer_contract_script"
fi

capture_terminal_runtime_diagnostic \
    "diagnostics_wezterm_runtime" \
    "WezTerm runtime diagnostics (version + renderer hint)" \
    "wezterm" \
    "wezterm --version" \
    "wezterm --help | sed -n '1,120p' | rg -m1 'webgpu|opengl|software' || true" \
    "renderer_hint"

capture_terminal_runtime_diagnostic \
    "diagnostics_ghostty_runtime" \
    "Ghostty runtime diagnostics (version + renderer hint)" \
    "ghostty" \
    "ghostty +version" \
    "ghostty +help | sed -n '1,200p' | rg -m1 'renderer|opengl|metal|vulkan' || true" \
    "renderer_hint"

capture_terminal_runtime_diagnostic \
    "diagnostics_kitty_runtime" \
    "Kitty runtime diagnostics (version + renderer hint)" \
    "kitty" \
    "kitty --version" \
    "kitty --debug-config 2>/dev/null | rg -m1 'renderer|opengl|vulkan|metal' || true" \
    "renderer_hint"

capture_terminal_runtime_diagnostic \
    "diagnostics_alacritty_runtime" \
    "Alacritty runtime diagnostics (version + renderer hint)" \
    "alacritty" \
    "alacritty --version" \
    "alacritty --print-events --config-file /dev/null 2>&1 | rg -m1 'Renderer|GL|Vulkan' || true" \
    "renderer_hint"

pass_count=0
warn_count=0
fail_count=0
for status in "${CHECK_STATUSES[@]}"; do
    case "$status" in
        pass) ((pass_count+=1)) ;;
        warn) ((warn_count+=1)) ;;
        fail) ((fail_count+=1)) ;;
    esac
done

overall_status="pass"
exit_code=0
if (( fail_count > 0 )); then
    overall_status="fail"
    exit_code=1
elif (( warn_count > 0 )); then
    overall_status="warn"
fi

{
    printf 'Terminal modernization QA summary\n'
    printf '================================\n'
    printf 'Overall: %s\n' "$overall_status"
    printf 'Pass: %d  Warn: %d  Fail: %d\n\n' "$pass_count" "$warn_count" "$fail_count"

    for i in "${!CHECK_IDS[@]}"; do
        symbol=""
        case "${CHECK_STATUSES[$i]}" in
            pass) symbol="✅" ;;
            warn) symbol="⚠️" ;;
            fail) symbol="❌" ;;
            *) symbol="❓" ;;
        esac

        printf '%s [%s] %s\n' "$symbol" "${CHECK_IDS[$i]}" "${CHECK_DESCRIPTIONS[$i]}"
        printf '    %s\n' "${CHECK_DETAILS[$i]}"
    done

    printf '\nJSON report: %s\n' "$json_report"
    printf 'Renderer contract JSON report: %s\n' "$renderer_json_report"
}

{
    printf '{\n'
    printf '  "overall_status": "%s",\n' "$(json_escape "$overall_status")"
    printf '  "counts": {"pass": %d, "warn": %d, "fail": %d},\n' "$pass_count" "$warn_count" "$fail_count"
    printf '  "benchmark_threshold_ms": %s,\n' "$(json_escape "$benchmark_threshold")"
    printf '  "zsh_startup_budget_warm_ms": %s,\n' "$(json_escape "$zsh_startup_budget_warm_ms")"
    printf '  "zsh_startup_budget_cold_ms": %s,\n' "$(json_escape "$zsh_startup_budget_cold_ms")"
    printf '  "checks": [\n'

    for i in "${!CHECK_IDS[@]}"; do
        comma=","
        if [[ "$i" -eq "$((${#CHECK_IDS[@]} - 1))" ]]; then
            comma=""
        fi
        printf '    {"id":"%s","description":"%s","status":"%s","details":"%s"}%s\n' \
            "$(json_escape "${CHECK_IDS[$i]}")" \
            "$(json_escape "${CHECK_DESCRIPTIONS[$i]}")" \
            "$(json_escape "${CHECK_STATUSES[$i]}")" \
            "$(json_escape "${CHECK_DETAILS[$i]}")" \
            "$comma"
    done

    printf '  ],\n'
    printf '  "renderer_contract_report": "%s"\n' "$(json_escape "$renderer_json_report")"
    printf '}\n'
} > "$json_report"

exit "$exit_code"

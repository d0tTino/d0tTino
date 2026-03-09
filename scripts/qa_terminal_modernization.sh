#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
report_dir="${TINO_QA_REPORT_DIR:-$repo_root/.cache/tino/qa-terminal-modernization}"
json_report="${TINO_QA_JSON_REPORT:-$report_dir/report.json}"
renderer_json_report="${TINO_QA_RENDERER_JSON_REPORT:-$report_dir/renderer-contract.json}"
benchmark_threshold="${TINO_QA_NVIM_MAX_STARTUP_MS:-${TINO_NVIM_MAX_STARTUP_MS:-250}}"

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

zshrc_path="$repo_root/dotfiles/shell/.zshrc"
starship_config_path="$repo_root/dotfiles/shell/.config/starship.toml"
tmux_config_path="$repo_root/dotfiles/tmux/.tmux.conf"
renderer_contract_script="$repo_root/dotfiles/terminal/.config/tino/validate-renderer-contract.sh"
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

if [[ -x "$renderer_contract_script" ]]; then
    run_check_command "renderer_contract" "terminal renderer contract validation passes" \
        bash "$renderer_contract_script" --report-format json --report-file "$renderer_json_report" || true
else
    record_check "renderer_contract" "terminal renderer contract validation passes" "fail" "renderer contract script missing or not executable: $renderer_contract_script"
fi

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

#!/usr/bin/env bash
set -euo pipefail

legacy_bashrc="${HOME}/.bashrc"

target_dir="${XDG_CONFIG_HOME:-$HOME/.config}/zsh"
env_target="${target_dir}/env.zsh"
aliases_target="${target_dir}/aliases.zsh"
functions_target="${target_dir}/functions.zsh"

force_overwrite=0

usage() {
    cat <<'EOF'
Usage: migrate-shell-config.sh [--force]

Migrates compatible settings from ~/.bashrc into live runtime zsh fragments under
${XDG_CONFIG_HOME:-$HOME/.config}/zsh.

Options:
  -f, --force   overwrite existing target fragment files without prompting
  -h, --help    show this help message
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -f|--force)
            force_overwrite=1
            shift
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

timestamp="$(date +%Y%m%d-%H%M%S)"
backup_dir="${HOME}/.config/tino/shell-migration-backups"
report_dir="${HOME}/.config/tino"
mkdir -p "${backup_dir}" "${report_dir}" "${target_dir}"

existing_targets=()
for target in "${env_target}" "${aliases_target}" "${functions_target}"; do
    if [[ -e "${target}" ]]; then
        existing_targets+=("${target}")
    fi
done

if [[ ${#existing_targets[@]} -gt 0 && ${force_overwrite} -eq 0 ]]; then
    if [[ -t 0 ]]; then
        echo "The following live runtime fragments already exist:" >&2
        for target in "${existing_targets[@]}"; do
            echo "  - ${target}" >&2
        done
        read -r -p "Overwrite them? [y/N] " response
        if [[ ! "${response}" =~ ^[Yy]([Ee][Ss])?$ ]]; then
            echo "Aborting migration to avoid overwriting existing runtime fragments." >&2
            exit 1
        fi
    else
        echo "Refusing to overwrite existing runtime fragments in ${target_dir} without --force." >&2
        exit 1
    fi
fi

if [[ ! -f "${legacy_bashrc}" ]]; then
    echo "No ~/.bashrc found; nothing to migrate."
    exit 0
fi

backup_path="${backup_dir}/bashrc.${timestamp}.bak"
report_path="${report_dir}/shell-migration-report.${timestamp}.txt"
cp "${legacy_bashrc}" "${backup_path}"

echo "# Migrated from ~/.bashrc on ${timestamp}" > "${env_target}"
echo "# Review and customize as needed." >> "${env_target}"
printf '\n' >> "${env_target}"

echo "# Migrated aliases from ~/.bashrc on ${timestamp}" > "${aliases_target}"
echo "# Review and customize as needed." >> "${aliases_target}"
printf '\n' >> "${aliases_target}"

echo "# Migrated functions from ~/.bashrc on ${timestamp}" > "${functions_target}"
echo "# Review and customize as needed." >> "${functions_target}"
printf '\n' >> "${functions_target}"

{
    echo "d0tTino shell migration report"
    echo "Generated: ${timestamp}"
    echo "Source: ${legacy_bashrc}"
    echo "Backup: ${backup_path}"
    echo "Live runtime targets:"
    echo "  - ${env_target}"
    echo "  - ${aliases_target}"
    echo "  - ${functions_target}"
    echo
    echo "Skipped / incompatible lines:"
} > "${report_path}"

env_count=0
alias_count=0
function_count=0
skip_count=0

in_function=0
function_depth=0

count_char() {
    local line="$1"
    local char="$2"
    awk -v line="$line" -v char="$char" 'BEGIN { n = gsub(char, "", line); print n }'
}

while IFS= read -r line || [[ -n "${line}" ]]; do
    line_no=${line_no:-0}
    line_no=$((line_no + 1))
    trimmed="${line#${line%%[![:space:]]*}}"

    if [[ ${in_function} -eq 1 ]]; then
        printf '%s\n' "${line}" >> "${functions_target}"

        opens=$(count_char "${line}" "\\{")
        closes=$(count_char "${line}" "\\}")
        function_depth=$((function_depth + opens - closes))

        if [[ ${function_depth} -le 0 ]]; then
            in_function=0
        fi
        continue
    fi

    if [[ -z "${trimmed}" || "${trimmed}" == \#* ]]; then
        continue
    fi

    if [[ "${trimmed}" =~ ^(function[[:space:]]+)?[A-Za-z_][A-Za-z0-9_]*[[:space:]]*\(\)[[:space:]]*\{[[:space:]]*$ ]]; then
        in_function=1
        function_count=$((function_count + 1))
        printf '%s\n' "${line}" >> "${functions_target}"
        opens=$(count_char "${line}" "\\{")
        closes=$(count_char "${line}" "\\}")
        function_depth=$((opens - closes))
        if [[ ${function_depth} -le 0 ]]; then
            in_function=0
        fi
        continue
    fi

    if [[ "${trimmed}" =~ ^alias[[:space:]]+[A-Za-z0-9_.-]+= ]]; then
        alias_count=$((alias_count + 1))
        printf '%s\n' "${line}" >> "${aliases_target}"
        continue
    fi

    if [[ "${trimmed}" =~ ^(export[[:space:]]+)?[A-Za-z_][A-Za-z0-9_]*= ]] \
        || [[ "${trimmed}" =~ ^(readonly|typeset[[:space:]]+-x|declare[[:space:]]+-x)[[:space:]]+[A-Za-z_][A-Za-z0-9_]*= ]] \
        || [[ "${trimmed}" =~ ^unset[[:space:]]+[A-Za-z_][A-Za-z0-9_]* ]]; then
        env_count=$((env_count + 1))
        printf '%s\n' "${line}" >> "${env_target}"
        continue
    fi

    skip_count=$((skip_count + 1))
    printf 'L%-4s %s\n' "${line_no}" "${line}" >> "${report_path}"
done < "${legacy_bashrc}"

if [[ ${skip_count} -eq 0 ]]; then
    echo "(none)" >> "${report_path}"
fi

{
    echo
    echo "Summary:"
    echo "  env lines: ${env_count}"
    echo "  alias lines: ${alias_count}"
    echo "  function blocks: ${function_count}"
    echo "  skipped lines: ${skip_count}"
} >> "${report_path}"

echo "Backed up ~/.bashrc to ${backup_path}"
echo "Migrated env lines to live runtime path: ${env_count} -> ${env_target}"
echo "Migrated aliases to live runtime path: ${alias_count} -> ${aliases_target}"
echo "Migrated functions to live runtime path: ${function_count} -> ${functions_target}"
echo "Migration report: ${report_path}"

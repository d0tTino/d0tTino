# Bash compatibility shim.
# d0tTino uses zsh as the primary interactive shell configuration.

case $- in
    *i*) ;;
    *) return ;;
esac

migration_script="$HOME/.local/share/d0ttino/scripts/migrate-shell-config.sh"
if [[ ! -x "${migration_script}" ]]; then
    if [[ -n "${D0TTINO_REPO_ROOT:-}" ]]; then
        repo_migration_script="${D0TTINO_REPO_ROOT}/scripts/migrate-shell-config.sh"
        if [[ -x "${repo_migration_script}" ]]; then
            migration_script="${repo_migration_script}"
        else
            migration_script=""
        fi
    else
        migration_script=""
    fi
fi

migration_hint_stamp="${XDG_CACHE_HOME:-$HOME/.cache}/d0ttino/bash-migration-hint-shown"
if [[ ! -f "${migration_hint_stamp}" ]]; then
    mkdir -p "$(dirname "${migration_hint_stamp}")"
    if [[ -n "${migration_script}" ]]; then
        printf 'Hint: migrate your legacy ~/.bashrc settings with %s\n' "${migration_script}" >&2
    else
        printf 'Hint: migration helper is not installed. Run ./scripts/install_common.sh, then rerun this shell to get the migration command.\n' >&2
    fi
    : > "${migration_hint_stamp}"
fi

printf 'This environment is configured for zsh. Run `zsh` or set it as your login shell.\n' >&2

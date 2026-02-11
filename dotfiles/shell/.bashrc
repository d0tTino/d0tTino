# Bash compatibility shim.
# d0tTino uses zsh as the primary interactive shell configuration.

case $- in
    *i*) ;;
    *) return ;;
esac

migration_script="$HOME/.local/share/d0ttino/scripts/migrate-shell-config.sh"
if [[ ! -x "${migration_script}" ]]; then
    migration_script="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/scripts/migrate-shell-config.sh"
fi

migration_hint_stamp="${XDG_CACHE_HOME:-$HOME/.cache}/d0ttino/bash-migration-hint-shown"
if [[ ! -f "${migration_hint_stamp}" ]]; then
    mkdir -p "$(dirname "${migration_hint_stamp}")"
    printf 'Hint: migrate your legacy ~/.bashrc settings with %s\n' "${migration_script}" >&2
    : > "${migration_hint_stamp}"
fi

printf 'This environment is configured for zsh. Run `zsh` or set it as your login shell.\n' >&2

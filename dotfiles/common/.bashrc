# Bash compatibility shim.
# d0tTino uses zsh as the primary interactive shell configuration.

case $- in
    *i*)
        if [ -n "${BASH_VERSION:-}" ]; then
            printf 'This environment is configured for zsh. Run `zsh` or set it as your login shell.\n' >&2
        fi
        ;;
    *)
        return
        ;;
esac

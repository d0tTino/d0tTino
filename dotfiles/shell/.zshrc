if [[ "${TINO_ZSH_PROFILE:-0}" == "1" ]]; then
    zmodload zsh/zprof
fi

source_if_readable() {
    local file_path="$1"
    if [[ -r "${file_path}" ]]; then
        # shellcheck disable=SC1090
        source "${file_path}"
    fi
}

TINO_ZSH_STARTUP_BUDGET_WARM_MS="${TINO_ZSH_STARTUP_BUDGET_WARM_MS:-80}"
TINO_ZSH_STARTUP_BUDGET_COLD_MS="${TINO_ZSH_STARTUP_BUDGET_COLD_MS:-150}"

ZSH_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/zsh"
ZSH_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/zsh"
mkdir -p "$ZSH_CACHE_DIR"

# Faster startup path: use cached completion metadata unless cache is stale.
tino_compinit() {
    autoload -Uz compinit

    local compdump_file="$ZSH_CACHE_DIR/zcompdump"
    local refresh_days="${TINO_ZSH_COMPINIT_REFRESH_DAYS:-7}"
    local refresh_seconds=$(( refresh_days * 86400 ))
    local needs_refresh=0

    if [[ ! -s "$compdump_file" ]]; then
        needs_refresh=1
    else
        zmodload -F zsh/stat b:zstat 2>/dev/null
        if (( $+functions[zstat] )); then
            local -A file_stat
            if zstat -A file_stat +mtime -- "$compdump_file" 2>/dev/null; then
                if (( EPOCHSECONDS - file_stat[mtime] > refresh_seconds )); then
                    needs_refresh=1
                fi
            else
                needs_refresh=1
            fi
        fi
    fi

    if (( needs_refresh )); then
        compinit -d "$compdump_file"
    else
        compinit -C -d "$compdump_file"
    fi

    zstyle ':completion:*' use-cache on
    zstyle ':completion:*' cache-path "$ZSH_CACHE_DIR"
}

tino_compinit

# Optional deferred initializer. Uses zsh-defer when installed, otherwise
# falls back to a lightweight precmd queue.
typeset -ga TINO_DEFER_QUEUE=()
typeset -gi _TINO_DEFER_HOOK_REGISTERED=0

_tino_run_deferred_queue() {
    local deferred_block
    if (( ${#TINO_DEFER_QUEUE[@]} == 0 )); then
        return
    fi

    deferred_block="${TINO_DEFER_QUEUE[1]}"
    TINO_DEFER_QUEUE=("${TINO_DEFER_QUEUE[@]:1}")
    eval "$deferred_block"
}

tino_defer_eval() {
    local deferred_block="$1"

    if [[ -z "$deferred_block" ]]; then
        return
    fi

    if (( $+commands[zsh-defer] )); then
        zsh-defer eval "$deferred_block"
        return
    fi

    TINO_DEFER_QUEUE+=("$deferred_block")
    if (( _TINO_DEFER_HOOK_REGISTERED == 0 )); then
        autoload -Uz add-zsh-hook
        add-zsh-hook precmd _tino_run_deferred_queue
        _TINO_DEFER_HOOK_REGISTERED=1
    fi
}

# Phase 1: prompt-critical startup path.
ZSH_PLUGIN_DIR="${ZSH_PLUGIN_DIR:-$HOME/.local/share/zsh/plugins}"
source_if_readable "$ZSH_CONFIG_DIR/aliases.zsh"
source_if_readable "$ZSH_CONFIG_DIR/functions.zsh"
source_if_readable "$ZSH_PLUGIN_DIR/zsh-autosuggestions/zsh-autosuggestions.zsh"
source_if_readable "$ZSH_PLUGIN_DIR/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"

if command -v starship >/dev/null; then
    eval "$(starship init zsh)"
fi

# Phase 2: deferred non-critical path/env initialization.
if [[ "${TINO_ZSH_DEFER:-1}" == "1" ]]; then
    tino_defer_eval 'source_if_readable "$ZSH_CONFIG_DIR/env.zsh"'
    tino_defer_eval 'source_if_readable "$HOME/.config/tino/terminal-defaults.sh"'
    tino_defer_eval 'source_if_readable "$HOME/.config/tino/host-overrides.sh"'

    if command -v zoxide >/dev/null; then
        tino_defer_eval 'eval "$(zoxide init zsh)"'
    fi
else
    source_if_readable "$ZSH_CONFIG_DIR/env.zsh"
    source_if_readable "$HOME/.config/tino/terminal-defaults.sh"
    source_if_readable "$HOME/.config/tino/host-overrides.sh"

    if command -v zoxide >/dev/null; then
        eval "$(zoxide init zsh)"
    fi
fi

if [[ "${TINO_ZSH_PROFILE:-0}" == "1" ]]; then
    zprof
fi

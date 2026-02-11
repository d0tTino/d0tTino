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

ZSH_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/zsh"
ZSH_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/zsh"
mkdir -p "$ZSH_CACHE_DIR"
autoload -Uz compinit && compinit -d "$ZSH_CACHE_DIR/zcompdump"
zstyle ':completion:*' use-cache on
zstyle ':completion:*' cache-path "$ZSH_CACHE_DIR"

source_if_readable "$ZSH_CONFIG_DIR/env.zsh"
source_if_readable "$HOME/.config/tino/terminal-defaults.sh"
source_if_readable "$HOME/.config/tino/host-overrides.sh"
source_if_readable "$ZSH_CONFIG_DIR/aliases.zsh"
source_if_readable "$ZSH_CONFIG_DIR/functions.zsh"

ZSH_PLUGIN_DIR="${ZSH_PLUGIN_DIR:-$HOME/.local/share/zsh/plugins}"
source_if_readable "$ZSH_PLUGIN_DIR/zsh-autosuggestions/zsh-autosuggestions.zsh"
source_if_readable "$ZSH_PLUGIN_DIR/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"

if command -v starship >/dev/null; then
    eval "$(starship init zsh)"
fi

if command -v zoxide >/dev/null; then
    eval "$(zoxide init zsh)"
fi

if [[ "${TINO_ZSH_PROFILE:-0}" == "1" ]]; then
    zprof
fi

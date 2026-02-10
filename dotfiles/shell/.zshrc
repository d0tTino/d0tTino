if [[ "${TINO_ZSH_PROFILE:-0}" == "1" ]]; then
    zmodload zsh/zprof
fi

autoload -Uz compinit && compinit -d "${XDG_CACHE_HOME:-$HOME/.cache}/zsh/zcompdump"

ZSH_PLUGIN_DIR="${ZSH_PLUGIN_DIR:-$HOME/.local/share/zsh/plugins}"

if [[ -r "$ZSH_PLUGIN_DIR/zsh-autosuggestions/zsh-autosuggestions.zsh" ]]; then
    source "$ZSH_PLUGIN_DIR/zsh-autosuggestions/zsh-autosuggestions.zsh"
fi

if [[ -r "$ZSH_PLUGIN_DIR/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]]; then
    source "$ZSH_PLUGIN_DIR/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
fi


if [[ -r "$HOME/.config/tino/terminal-defaults.sh" ]]; then
    source "$HOME/.config/tino/terminal-defaults.sh"
fi

if [[ -r "$HOME/.config/tino/host-overrides.sh" ]]; then
    source "$HOME/.config/tino/host-overrides.sh"
fi

if command -v starship >/dev/null; then
    eval "$(starship init zsh)"
fi

if command -v zoxide >/dev/null; then
    eval "$(zoxide init zsh)"
fi

if [[ "${TINO_ZSH_PROFILE:-0}" == "1" ]]; then
    zprof
fi

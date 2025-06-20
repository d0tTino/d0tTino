if command -v starship >/dev/null; then
    eval "$(starship init bash)"
fi
starship_config="$(dirname "${BASH_SOURCE[0]}")/../../starship.toml"
if command -v starship >/dev/null; then
    eval "$(starship init bash --config "$starship_config")"
fi
if command -v zoxide >/dev/null; then
    eval "$(zoxide init bash)"
fi

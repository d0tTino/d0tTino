if command -v starship >/dev/null; then
    eval "$(starship init bash)"
fi
if command -v zoxide >/dev/null; then
    eval "$(zoxide init bash)"
fi

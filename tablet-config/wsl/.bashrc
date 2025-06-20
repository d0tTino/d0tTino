theme_file="$(dirname "${BASH_SOURCE[0]}")/../oh-my-posh/custom_tokyo.omp.json"
if command -v oh-my-posh >/dev/null; then
    eval "$(oh-my-posh init bash --config "$theme_file")"
fi
if command -v zoxide >/dev/null; then
    eval "$(zoxide init bash)"
fi

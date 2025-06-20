theme_file="$(dirname "${BASH_SOURCE[0]}")/../oh-my-posh/custom_tokyo.omp.json"
eval "$(oh-my-posh init bash --config \"${theme_file}\")"
eval "$(zoxide init bash)"

#!/usr/bin/env bash
set -euo pipefail

start="# >>> d0tTino zsh plugins >>>"
end="# <<< d0tTino zsh plugins <<<"
zshrc="${HOME}/.zshrc"

if [[ ! -f "$zshrc" ]]; then
    echo "No ~/.zshrc found; nothing to migrate."
    exit 0
fi

if ! grep -Fq "$start" "$zshrc"; then
    echo "No legacy d0tTino plugin block found in ~/.zshrc; nothing to migrate."
    exit 0
fi

timestamp="$(date +%Y%m%d-%H%M%S)"
backup_path="${zshrc}.pre-d0ttino-migration.${timestamp}.bak"
cp "$zshrc" "$backup_path"
echo "Backed up ~/.zshrc to $backup_path"

tmp="$(mktemp)"
awk -v start="$start" -v end="$end" '
    $0 == start {
        in_block = 1
        next
    }
    in_block && $0 == end {
        in_block = 0
        next
    }
    !in_block { print }
' "$zshrc" > "$tmp"

cp "$tmp" "$zshrc"
rm -f "$tmp"

echo "Removed legacy d0tTino plugin block from ~/.zshrc"
echo "Runtime shell config is now controlled by dotfiles/shell/.zshrc via scripts/install_dotfiles.sh"

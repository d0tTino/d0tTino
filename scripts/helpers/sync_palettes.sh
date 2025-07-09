#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
base="https://raw.githubusercontent.com/d0tTino/d0tTino/main/palettes"
mkdir -p "$repo_root/palettes"
for name in blacklight dracula solarized-dark; do
    curl -fsSL "$base/$name.toml" -o "$repo_root/palettes/$name.toml"
done

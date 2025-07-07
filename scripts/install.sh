#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

install_fonts_unix() {
    url="https://github.com/ryanoasis/nerd-fonts/releases/latest/download/CaskaydiaCove.zip"
    tmpdir="$(mktemp -d)"
    curl -fsSL "$url" -o "$tmpdir/font.zip"
    unzip -q "$tmpdir/font.zip" -d "$tmpdir"
    font_dir="$HOME/.local/share/fonts"
    mkdir -p "$font_dir"
    mv "$tmpdir"/*.ttf "$font_dir/"
    fc-cache -f "$font_dir"
    rm -rf "$tmpdir"
}

install_fonts_windows() {
    if command -v winget >/dev/null; then
        winget install --id NerdFonts.CaskaydiaCove -e \
            --accept-source-agreements --accept-package-agreements
    else
        echo "winget is required on Windows" >&2
        exit 1
    fi
}

pull_palettes() {
    base="https://raw.githubusercontent.com/d0tTino/d0tTino/main/palettes"
    mkdir -p "$repo_root/palettes"
    for name in blacklight dracula solarized-dark; do
        curl -fsSL "$base/$name.toml" -o "$repo_root/palettes/$name.toml"
    done
}

case "$(uname -s)" in
    Linux*|Darwin*) install_fonts_unix ;;
    CYGWIN*|MINGW*|MSYS*|Windows_NT) install_fonts_windows ;;
    *) echo "Unsupported OS" >&2; exit 1 ;;
esac

pull_palettes

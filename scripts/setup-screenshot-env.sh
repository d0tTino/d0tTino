#!/usr/bin/env bash
set -euo pipefail

install_debian() {
    sudo apt-get update
    sudo apt-get install -y fastfetch btm nushell wget
    tmpdir="$(mktemp -d)"
    wget -qO "$tmpdir/zed.deb" https://zed.dev/api/releases/zed_latest_amd64.deb
    sudo dpkg -i "$tmpdir/zed.deb"
    rm -rf "$tmpdir"
}

install_pacman() {
    sudo pacman -Sy --noconfirm fastfetch bottom nushell
    echo "Please install Zed manually from https://zed.dev/" >&2
}

install_brew() {
    brew install fastfetch bottom nushell
    brew install --cask zed
}

case "$(uname -s)" in
    Linux)
        if command -v apt-get >/dev/null; then
            install_debian
        elif command -v pacman >/dev/null; then
            install_pacman
        else
            echo "Unsupported Linux distribution" >&2
            exit 1
        fi
        ;;
    Darwin)
        if command -v brew >/dev/null; then
            install_brew
        else
            echo "Homebrew is required on macOS" >&2
            exit 1
        fi
        ;;
    *)
        echo "Unsupported platform" >&2
        exit 1
        ;;
esac

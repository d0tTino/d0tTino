#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

output="${1:-gource.mp4}"

if ! command -v gource >/dev/null 2>&1; then
    echo "Error: gource is required" >&2
    exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "Error: ffmpeg is required" >&2
    exit 1
fi

# Render the repository history using gource and ffmpeg
# Terminalizer can be used to convert the resulting video to a GIF
# if it is available on the system.

gource \
    --seconds-per-day 0.1 \
    --auto-skip-seconds 1 \
    --hide mouse,dirnames,filenames \
    --output-ppm-stream - \
    | ffmpeg -y -r 60 -f image2pipe -vcodec ppm -i - \
        -vcodec libx264 -pix_fmt yuv420p "$output"

if command -v terminalizer >/dev/null 2>&1; then
    gif_output="${output%.*}.gif"
    terminalizer render "$output" -o "$gif_output" || \
        echo "terminalizer failed to create GIF" >&2
fi

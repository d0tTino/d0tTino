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

# Upload to Mattermost if credentials are provided
if [[ -n "${MATTERMOST_URL:-}" && -n "${MATTERMOST_TOKEN:-}" && -n "${MATTERMOST_CHANNEL_ID:-}" ]]; then
    if command -v curl >/dev/null 2>&1; then
        resp=$(curl -s -H "Authorization: Bearer $MATTERMOST_TOKEN" \
            -F files=@"$output" -F channel_id="$MATTERMOST_CHANNEL_ID" \
            "$MATTERMOST_URL/api/v4/files")
        file_id=$(python3 -c 'import sys, json; print(json.load(sys.stdin)["file_infos"][0]["id"])' <<<"$resp" 2>/dev/null)
        if [[ -n "$file_id" ]]; then
            curl -s -H "Authorization: Bearer $MATTERMOST_TOKEN" \
                -H "Content-Type: application/json" \
                -d '{"channel_id":"'$MATTERMOST_CHANNEL_ID'","message":"Gource render","file_ids":["'$file_id'"]}' \
                "$MATTERMOST_URL/api/v4/posts" >/dev/null
        fi
    else
        echo "curl is required to post to Mattermost" >&2
    fi
fi

# Upload to Nextcloud if credentials are provided
if [[ -n "${NEXTCLOUD_URL:-}" && -n "${NEXTCLOUD_USERNAME:-}" && -n "${NEXTCLOUD_PASSWORD:-}" && -n "${NEXTCLOUD_FOLDER:-}" ]]; then
    if command -v curl >/dev/null 2>&1; then
        base="$NEXTCLOUD_URL/remote.php/dav/files/$NEXTCLOUD_USERNAME/$NEXTCLOUD_FOLDER"
        curl -s -u "$NEXTCLOUD_USERNAME:$NEXTCLOUD_PASSWORD" -T "$output" "$base/$(basename "$output")" >/dev/null
        if [[ -n "${gif_output:-}" && -f "$gif_output" ]]; then
            curl -s -u "$NEXTCLOUD_USERNAME:$NEXTCLOUD_PASSWORD" -T "$gif_output" "$base/$(basename "$gif_output")" >/dev/null
        fi
    else
        echo "curl is required to upload to Nextcloud" >&2
    fi
fi

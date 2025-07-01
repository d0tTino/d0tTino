#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

dockerfile="$repo_root/Dockerfile"

if ! command -v docker >/dev/null 2>&1; then
    echo "docker is required but not installed." >&2
    exit 1
fi

if [[ ! -f "$dockerfile" ]]; then
    echo "Error: Dockerfile not found in $repo_root" >&2
    exit 1
fi

image_name="${IMAGE_NAME:-d0ttino:latest}"

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--image)
            image_name=$2
            shift 2
            ;;
        --)
            shift
            break
            ;;
        *)
            break
            ;;
    esac
done

docker build -t "$image_name" "$repo_root"
exec docker run --rm -it -v "$repo_root:$repo_root" -w "$repo_root" "$image_name" "$@"

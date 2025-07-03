#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "${BASH_SOURCE[0]%/*}" && pwd)"
exec /bin/bash "$script_dir/run-service.sh" romm "$@"

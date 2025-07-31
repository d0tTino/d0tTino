#!/usr/bin/env bash
set -euo pipefail

# Start a JetStream-enabled NATS server inside a Docker container.
# The container exposes port 4222 by default. Pass an alternate port as
# the first argument.

port=${1:-4222}

docker run --rm -p "$port:4222" nats:latest -js

# Media Containers

This repository includes optional Docker setups for media-related tools.

## RomM

RomM is a self-hosted game library manager. To launch it:

1. Run the helper script to start the Docker compose service:
   ```bash
   ./scripts/run-romm.sh
   ```
2. Open [http://localhost:8080](http://localhost:8080) and create your user account.
3. Game metadata and configuration are stored under `./romm` in the repository.
4. To stop the service press `Ctrl+C` or run `docker compose down` from another shell.

You can also start RomM directly with `docker compose up romm` if you do not want to use the helper script.

## Neko

Neko provides browser streaming via Docker.

1. Start the service with the helper script:
   ```bash
   ./scripts/run-neko.sh
   ```
2. By default the container exposes port `8081`. Edit `docker-compose.yml` if you need another port mapping.
3. Connect to `http://localhost:8081` and share your browser session.
4. You can also start Neko manually using `docker compose up neko`.

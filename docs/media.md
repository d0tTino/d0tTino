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

```bash
docker compose up neko
```

## Nextcloud

Nextcloud provides file sync and collaboration tools. Start it with:

```bash
./scripts/run-nextcloud.sh
```

It maps port `8082` to container port `80`. Adjust the value in `docker-compose.yml` if needed.

You can also use `docker compose up nextcloud` directly.

## Mattermost

Mattermost is a self-hosted chat server. Run it via:

```bash
./scripts/run-mattermost.sh
```

The service listens on port `8065`. Data is stored under `./mattermost`.
Use `docker compose up mattermost` to start it manually.

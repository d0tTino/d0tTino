# Media Containers

This repository includes optional Docker setups for media-related tools.

## RomM

RomM is a self-hosted game library manager. Start it with the helper script:

```bash
./scripts/run-romm.sh
```

The web interface is available on [localhost:8080](http://localhost:8080). Data is stored under `./romm`.

You can also launch it directly with:

```bash
docker compose up romm
```

## Neko

Neko provides browser streaming via Docker. Launch it with the helper script:

```bash
./scripts/run-neko.sh
```

It listens on port `8081` by default. Adjust the mapping in `docker-compose.yml` if you need a different port.

To start Neko without the script, run:

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

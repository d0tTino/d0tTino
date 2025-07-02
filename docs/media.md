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

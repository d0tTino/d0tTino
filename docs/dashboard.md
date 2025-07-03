# Dashboard Overview

The dashboard is a planned React and Tailwind front end for the Universal Memory Engine (UME). It will visualize memory graphs, display query statistics and provide system health checks.

## API Endpoints

The UME exposes a small set of FastAPI routes that power the dashboard:

- `GET /api/stats` – summary metrics for queries and memory usage
- `GET /api/graph` – the current memory graph as JSON
- `POST /api/palette` – apply a color palette
- `POST /api/prompt` – forward an LLM prompt and return the response
- `GET /api/health` – simple health check

These endpoints will evolve as the project grows but form the foundation for the web UI.

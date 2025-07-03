# Dashboard Overview

The dashboard pairs a FastAPI backend with a React front end built using Next.js.
The backend usually runs on <http://localhost:8000> while the dev server for
the React dashboard listens on <http://localhost:3000>. The same code base can
also be packaged as a Tauri application for a native desktop experience. It will
visualize memory graphs, display query statistics and provide system health
checks for the Universal Memory Engine (UME).

## API Endpoints

The UME exposes a small set of FastAPI routes that power the dashboard:

- `GET /api/stats` – summary metrics for queries and memory usage
- `GET /api/graph` – the current memory graph as JSON
- `POST /api/palette` – apply a color palette
- `POST /api/prompt` – forward an LLM prompt and return the response
- `GET /api/health` – simple health check

These endpoints will evolve as the project grows but form the foundation for the web UI.

## Running the Dashboard

Start the API server:

```bash
uvicorn api:app --reload
```

Then launch the Next.js client:

```bash
cd dashboard
npm install
npm run dev
```

Visit `http://localhost:3000` to view the dashboard.

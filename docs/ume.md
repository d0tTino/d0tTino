# UME Quickstart

The Universal Memory Engine (UME) powers the dashboard backend. Follow these steps to run it locally.

## Clone the Repository

Clone the [UME repository](https://github.com/d0tTino/UME.git) and change into its directory:

```bash
git clone https://github.com/d0tTino/UME.git
cd UME
```

## Install Dependencies

Install the project using [Poetry](https://python-poetry.org/):

```bash
poetry install
```

## Start the Services

Launch the API and supporting services:

```bash
poetry run python ume_cli.py up
```

The API will be available at <http://localhost:8000>. You can set the
`UME_API_URL` environment variable to connect to a remote instance.

## LangGraph Retrieval Demo

Run `examples/langgraph_integration.ipynb` to explore retrieval through LangGraph. Execute the notebook after the services have started.


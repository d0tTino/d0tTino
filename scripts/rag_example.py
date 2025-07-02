#!/usr/bin/env python3
"""Minimal retrieval example using LangGraph."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Optional

from llm import etl


def build_graph(collection: Any):
    """Return a compiled retrieval graph for ``collection``."""
    from langgraph.graph import StateGraph

    g = StateGraph(dict)
    etl.register_retrieval_nodes(g, collection)
    g.set_entry_point("retrieve")
    return g.compile()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--persist",
        type=Path,
        default=Path("chroma_db"),
        help="Chroma persistence directory (default: %(default)s)",
    )
    parser.add_argument(
        "--collection",
        default="documents",
        help="Chroma collection name (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    import chromadb

    client = chromadb.PersistentClient(path=str(args.persist))
    collection = client.get_or_create_collection(args.collection)
    app = build_graph(collection)
    result = app.invoke({"query": args.query})
    print(result["text"])
    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation
    raise SystemExit(main())


"""Utilities for ingesting documents and registering retrieval nodes."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Sequence


__all__ = [
    "partition_document",
    "store_embeddings",
    "register_retrieval_nodes",
]


def partition_document(path: Path) -> List[str]:
    """Return text chunks extracted from ``path`` using ``unstructured``."""
    try:
        from unstructured.partition.auto import partition
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError(
            "The 'unstructured' package is required for document partitioning"
        ) from exc

    elements = partition(filename=str(path))
    chunks = [getattr(el, "text", "") for el in elements if getattr(el, "text", "")]
    return chunks


def store_embeddings(
    chunks: Sequence[str], *, persist_dir: Path, collection_name: str = "documents"
):
    """Store embeddings for ``chunks`` in a ChromaDB collection."""
    try:
        import chromadb
        from chromadb.utils.embedding_functions import (
            SentenceTransformerEmbeddingFunction,
        )
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError(
            "The 'chromadb' package is required for embedding storage"
        ) from exc

    client = chromadb.PersistentClient(path=str(persist_dir))
    embed = SentenceTransformerEmbeddingFunction()
    collection = client.get_or_create_collection(
        collection_name, embedding_function=embed
    )
    ids = [f"doc-{i}" for i in range(len(chunks))]
    collection.add(documents=list(chunks), ids=ids)
    return collection


def register_retrieval_nodes(
    graph: Any,
    collection: Any,
    *,
    node_name: str = "retrieve",
) -> Any:
    """Register retrieval nodes on ``graph`` for ``collection`` using LangGraph."""
    try:
        from langgraph.prebuilt import retrieval
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError(
            "The 'langgraph' package is required for retrieval node registration"
        ) from exc

    retriever = retrieval.ChromaRetriever(collection)
    graph.add_node(node_name, retriever)
    return graph

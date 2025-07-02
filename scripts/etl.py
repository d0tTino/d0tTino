#!/usr/bin/env python3
"""Ingest documents into ChromaDB."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

from llm import etl


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="File or directory to ingest")
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

    files = [args.path]
    if args.path.is_dir():
        files = [p for p in args.path.rglob("*") if p.is_file()]

    chunks: List[str] = []
    for file in files:
        chunks.extend(etl.partition_document(file))

    etl.store_embeddings(
        chunks, persist_dir=args.persist, collection_name=args.collection
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

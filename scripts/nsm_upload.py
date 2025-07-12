#!/usr/bin/env python3
"""Upload aggregated north star metric statistics."""
from __future__ import annotations

import argparse
import os
import sys
from typing import Iterable

import requests

from . import nsm_stats


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "source",
        nargs="?",
        default=os.environ.get("EVENTS_URL"),
        help="EVENTS_URL or path to local file",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    if not args.source:
        parser.error("source or EVENTS_URL required")

    events = list(nsm_stats.iter_events(args.source))
    counts = nsm_stats.aggregate_successful_runs(events)

    url = os.environ.get("EVENTS_URL")
    if not url:
        parser.error("EVENTS_URL required for upload")
    token = os.environ.get("EVENTS_TOKEN")
    headers = {}
    if token:
        headers["apikey"] = token
        headers["Authorization"] = f"Bearer {token}"
    try:
        requests.post(url, headers=headers, json=counts, timeout=10)
    except Exception as exc:
        print(f"failed to post stats: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

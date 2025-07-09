#!/usr/bin/env python3
"""Aggregate ai-do success counts per developer per week."""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable

import requests


Event = Dict[str, object]


def _read_lines(source: str) -> Iterable[str]:
    if source.startswith("http://") or source.startswith("https://"):
        resp = requests.get(source, timeout=10)
        resp.raise_for_status()
        return resp.text.splitlines()
    return Path(source).read_text(encoding="utf-8").splitlines()


def iter_events(source: str) -> Iterable[Event]:
    for line in _read_lines(source):
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def aggregate_successful_runs(events: Iterable[Event]) -> Dict[str, Dict[str, int]]:
    counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for ev in events:
        if ev.get("name") != "ai-do" or ev.get("exit_code") != 0:
            continue
        dev = (
            ev.get("developer")
            or ev.get("user")
            or ev.get("username")
            or "unknown"
        )
        ts = (
            ev.get("end_ts")
            or ev.get("timestamp")
            or ev.get("ts")
            or ev.get("time")
        )
        if ts is None:
            continue
        try:
            ts_f = float(ts)
            dt = datetime.fromtimestamp(ts_f)
        except Exception:
            try:
                dt = datetime.fromisoformat(str(ts))
            except Exception:
                continue
        year, week, _ = dt.isocalendar()
        week_key = f"{year}-W{week:02d}"
        counts[str(dev)][week_key] += 1
    return counts


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
    events = list(iter_events(args.source))
    counts = aggregate_successful_runs(events)
    for dev in sorted(counts):
        for week in sorted(counts[dev]):
            print(f"{dev},{week},{counts[dev][week]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

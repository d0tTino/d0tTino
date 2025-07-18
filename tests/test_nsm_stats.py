from datetime import datetime

import pytest

pytest.importorskip("requests")

from scripts import nsm_stats


def test_aggregate_successful_runs():
    events = [
        {"name": "ai-do", "exit_code": 0, "developer": "alice", "end_ts": 1693516800},
        {"name": "ai-do", "exit_code": 0, "developer": "alice", "end_ts": 1693603200},
        {"name": "ai-do", "exit_code": 1, "developer": "alice", "end_ts": 1693603200},
        {"name": "ai-do", "exit_code": 0, "developer": "bob", "end_ts": 1693785600},
    ]
    counts = nsm_stats.aggregate_successful_runs(events)
    week35 = f"2023-W{datetime.fromtimestamp(1693516800).isocalendar().week:02d}"
    week36 = f"2023-W{datetime.fromtimestamp(1693785600).isocalendar().week:02d}"
    assert counts["alice"][week35] == 2
    assert counts["bob"][week36] == 1


def test_aggregate_successful_runs_ignores_malformed():
    events = [
        {"name": "ai-do", "exit_code": 0, "developer": "alice", "end_ts": "bad"},
        {"name": "ai-do", "exit_code": 0, "developer": "alice"},
        {"name": "ai-do", "exit_code": 0, "developer": "bob", "end_ts": 1693785600},
    ]
    counts = nsm_stats.aggregate_successful_runs(events)
    week36 = f"2023-W{datetime.fromtimestamp(1693785600).isocalendar().week:02d}"
    simplified = {dev: dict(weeks) for dev, weeks in counts.items()}
    assert simplified == {"bob": {week36: 1}}

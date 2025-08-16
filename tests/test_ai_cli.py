import contextlib
import io
import subprocess
import pytest

pytest.importorskip("requests")

from scripts import ai_cli
from scripts import cli_actions
from scripts.cli_common import PlanStep
import telemetry


def test_send_subcommand(monkeypatch):
    def mock_send(prompt, *, local=False, model=ai_cli.router.DEFAULT_MODEL):
        assert prompt == "msg"
        assert local is True
        assert model == "m"
        return "ok"

    monkeypatch.setattr(ai_cli.router, "send_prompt", mock_send)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["send", "--local", "--model", "m", "msg"])
    assert rc == 0
    assert out.getvalue().strip() == "ok"


def test_plan_subcommand(monkeypatch):
    def fake_plan(goal: str, *, config_path=None, analytics=False):
        assert goal == "goal"
        assert config_path == "cfg.json"
        return [PlanStep(1, "one"), PlanStep(2, "two")]

    monkeypatch.setattr(ai_cli.ai_exec, "plan", fake_plan)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["plan", "goal", "--config", "cfg.json"])
    assert rc == 0
    expected_lines = ["1. one", "2. two"]
    assert out.getvalue().splitlines() == expected_lines


def test_do_subcommand(monkeypatch, tmp_path):
    monkeypatch.setattr(ai_cli.ai_exec, "plan", lambda *a, **k: [PlanStep(1, "echo hi")])

    inputs = iter(["y", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    def fake_run(cmd, *, shell, capture_output, text):
        assert cmd == ["echo", "hi"]
        class Result:
            def __init__(self):
                self.stdout = ""
                self.stderr = ""
                self.returncode = 0
        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)

    log = tmp_path / "log.txt"
    rc = ai_cli.main(["do", "goal", "--log", str(log)])
    assert rc == 0
    assert log.exists()


def test_do_creates_log_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(ai_cli.ai_exec, "plan", lambda *a, **k: [PlanStep(1, "echo hi")])
    monkeypatch.setattr("builtins.input", lambda _: "y")

    class Result:
        def __init__(self):
            self.stdout = ""
            self.stderr = ""
            self.returncode = 0

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: Result())

    log = tmp_path / "logs" / "log.txt"
    rc = ai_cli.main(["do", "goal", "--log", str(log)])
    assert rc == 0
    assert log.exists()


def test_plan_requests_clarification(monkeypatch):
    calls = []

    def fake_plan(goal: str, *, config_path=None, analytics=False):
        calls.append(goal)
        return [] if len(calls) == 1 else [PlanStep(1, f"echo {goal}")]

    monkeypatch.setattr(ai_cli.ai_exec, "plan", fake_plan)
    monkeypatch.setattr("builtins.input", lambda _: "more info")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["plan", "goal"])
    assert rc == 0
    assert calls == ["goal", "goal. more info"]
    expected = ["1. echo goal. more info"]
    assert out.getvalue().splitlines() == expected


def test_do_requests_clarification(monkeypatch):
    calls = []

    def fake_plan(goal: str, *, config_path=None, analytics=False):
        calls.append(goal)
        return [] if len(calls) == 1 else [PlanStep(1, f"echo {goal}")]

    monkeypatch.setattr(ai_cli.ai_exec, "plan", fake_plan)
    captured = {}

    def fake_run_steps(name, steps, **kwargs):
        captured["name"] = name
        captured["steps"] = steps
        return 0

    monkeypatch.setattr(cli_actions, "run_steps", fake_run_steps)
    monkeypatch.setattr(ai_cli, "execute_steps", lambda *a, **k: 0)
    monkeypatch.setattr("builtins.input", lambda _: "extra detail")
    rc = ai_cli.main(["do", "goal"])
    assert rc == 0
    assert calls == ["goal", "goal. extra detail"]
    assert captured["steps"] == [PlanStep(1, "echo goal. extra detail")]


def test_clarify_goal_prompts_user(monkeypatch):
    calls = []

    def fake_plan(goal: str, *, config_path=None, analytics=False):
        calls.append(goal)
        return [] if len(calls) == 1 else [PlanStep(1, f"echo {goal}")]

    monkeypatch.setattr(ai_cli.ai_exec, "plan", fake_plan)
    monkeypatch.setattr("builtins.input", lambda _: "details")
    goal, steps = ai_cli._clarify_goal("goal", config=None, analytics=False)
    assert calls == ["goal", "goal. details"]
    assert goal == "goal. details"
    assert steps == [PlanStep(1, "echo goal. details")]


def test_send_records_event(monkeypatch):
    monkeypatch.setattr(ai_cli.router, "send_prompt", lambda *a, **k: "ok")
    recorded = []

    def fake_record(name, payload, *, enabled=False):
        recorded.append((name, payload, enabled))
        return True

    monkeypatch.setattr(cli_actions, "record_event_logged", fake_record)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["send", "msg", "--analytics"])

    assert rc == 0
    assert recorded == [("ai-cli-send", {"exit_code": 0}, True)]


def test_plan_records_event(monkeypatch):
    monkeypatch.setattr(ai_cli.ai_exec, "plan", lambda *a, **k: [PlanStep(1, "one")])
    recorded = []

    def fake_record(name, payload, *, enabled=False):
        recorded.append((name, payload, enabled))
        return True

    monkeypatch.setattr(cli_actions, "record_event_logged", fake_record)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["plan", "goal", "--analytics"])

    assert rc == 0
    name, payload, enabled = recorded[0]
    assert name == "ai-cli-plan"
    assert enabled is True
    assert payload["goal"] == "goal"
    assert payload["step_count"] == 1
    assert "latency_ms" in payload and payload["latency_ms"] >= 0


def test_do_records_event(monkeypatch, tmp_path):
    monkeypatch.setattr(ai_cli.ai_exec, "plan", lambda *a, **k: [PlanStep(1, "echo hi")])
    inputs = iter(["y", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    class Result:
        def __init__(self):
            self.stdout = ""
            self.stderr = ""
            self.returncode = 0

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: Result())

    recorded = []

    def fake_record(name, payload, *, enabled=False):
        recorded.append((name, payload, enabled))
        return True

    monkeypatch.setattr(cli_actions, "record_event_logged", fake_record)
    log = tmp_path / "log.txt"
    rc = ai_cli.main(["do", "goal", "--log", str(log), "--analytics"])

    assert rc == 0
    name, payload, enabled = recorded[0]
    assert name == "ai-cli-do"
    assert enabled is True
    assert payload["goal"] == "goal"
    assert payload["exit_code"] == 0
    assert "latency_ms" in payload and payload["latency_ms"] >= 0


def test_do_records_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(ai_cli.ai_exec, "plan", lambda *a, **k: [PlanStep(1, "bad")])
    inputs = iter(["y", "y"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    class Result:
        def __init__(self):
            self.stdout = ""
            self.stderr = ""
            self.returncode = 1

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: Result())

    recorded = []

    def fake_record(name, payload, *, enabled=False):
        recorded.append((name, payload, enabled))
        return True

    monkeypatch.setattr(cli_actions, "record_event_logged", fake_record)
    log = tmp_path / "log.txt"
    rc = ai_cli.main(["do", "goal", "--log", str(log), "--analytics"])

    assert rc == 1
    name, payload, enabled = recorded[0]
    assert name == "ai-cli-do"
    assert enabled is True
    assert payload["goal"] == "goal"
    assert payload["exit_code"] == 1
    assert "latency_ms" in payload and payload["latency_ms"] >= 0


def test_do_requires_confirm_for_risky_steps(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        ai_cli.ai_exec,
        "plan",
        lambda *a, **k: [PlanStep(1, "rm -rf / [risk:rm]")],
    )
    log = tmp_path / "log.txt"
    rc = ai_cli.main(["do", "goal", "--log", str(log), "--yes"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "Risky commands present" in err

    called = []

    def fake_run(cmd, shell=False, capture_output=False, text=False):
        called.append(cmd)

        class R:
            returncode = 0
            stdout = ""
            stderr = ""

        return R()

    monkeypatch.setattr(subprocess, "run", fake_run)
    rc = ai_cli.main([
        "do",
        "goal",
        "--log",
        str(log),
        "--yes",
        "--confirm",
    ])
    assert rc == 0
    assert called


def test_recipe_subcommand(monkeypatch, tmp_path):
    monkeypatch.setattr(
        ai_cli.recipes,
        "discover_recipes",
        lambda: {"dummy": lambda goal: [f"echo {goal}"]},
    )
    captured = {}

    def fake_run_recipe(
        name,
        goal,
        steps,
        *,
        log_path,
        analytics=False,
        nats_url=None,
        jetstream=False,
        **kwargs,
    ):
        captured["name"] = name
        captured["goal"] = goal
        captured["steps"] = steps
        captured["log"] = log_path
        captured["analytics"] = analytics
        captured["nats_url"] = nats_url
        return 0

    monkeypatch.setattr(cli_actions, "run_recipe", fake_run_recipe)
    log = tmp_path / "log.txt"
    rc = ai_cli.main(["recipe", "dummy", "goal", "--log", str(log)])
    assert rc == 0
    assert captured["name"] == "dummy"
    assert captured["goal"] == "goal"
    assert captured["steps"] == ["echo goal"]
    assert captured["log"] == log
    assert captured["nats_url"] is None


def test_recipe_records_event(monkeypatch, tmp_path):
    monkeypatch.setattr(
        ai_cli.recipes, "discover_recipes", lambda: {"dummy": lambda g: []}
    )
    monkeypatch.setattr(cli_actions, "run_recipe", lambda *a, **k: 0)
    recorded = []

    def fake_record(name, payload, *, enabled=False):
        recorded.append((name, payload, enabled))
        return True

    monkeypatch.setattr(cli_actions, "record_event_logged", fake_record)
    log = tmp_path / "log.txt"
    rc = ai_cli.main([
        "recipe",
        "dummy",
        "goal",
        "--log",
        str(log),
        "--analytics",
    ])

    assert rc == 0
    name, payload, enabled = recorded[0]
    assert name == "ai-cli-recipe"
    assert enabled is True
    assert payload["recipe"] == "dummy"
    assert payload["goal"] == "goal"
    assert payload["exit_code"] == 0
    assert payload["step_count"] == 0
    assert "latency_ms" in payload and payload["latency_ms"] >= 0

def test_recipe_executes_plugin_once_and_logs(monkeypatch, tmp_path):
    count = {'n': 0}
    def plugin(goal: str):
        count['n'] += 1
        return [f"echo {goal}"]

    monkeypatch.setattr(ai_cli.recipes, 'discover_recipes', lambda: {'dummy': plugin})

    inputs = iter(['y', 'y'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    executed = {}
    def fake_run(cmd, *, shell, capture_output, text):
        executed['cmd'] = cmd
        class Res:
            def __init__(self):
                self.stdout = 'out\n'
                self.stderr = ''
                self.returncode = 0
        return Res()

    monkeypatch.setattr(subprocess, 'run', fake_run)

    log = tmp_path / 'log.txt'
    rc = ai_cli.main(['recipe', 'dummy', 'goal', '--log', str(log)])
    assert rc == 0
    assert count['n'] == 1
    assert executed['cmd'] == ['echo', 'goal']
    log_text = log.read_text()
    assert '$ echo goal' in log_text
    assert 'out' in log_text


def test_sources_subcommand(capsys):
    rc = ai_cli.main(["sources", "--tag", "python"])
    output = capsys.readouterr().out
    assert rc == 0
    assert "Python Docs" in output


def test_sources_filter_category(capsys):
    rc = ai_cli.main(["sources", "--category", "DevOps"])
    output = capsys.readouterr().out
    assert rc == 0
    assert "Docker Documentation" in output


def test_sources_name_and_tag_filters(capsys):
    rc = ai_cli.main(["sources", "--name", "fastapi", "--tag", "python"])
    output = capsys.readouterr().out
    assert rc == 0
    assert "FastAPI" in output


def test_sources_no_matches(capsys):
    rc = ai_cli.main(["sources", "--category", "missing"])
    output = capsys.readouterr().out
    assert rc == 1
    assert output == ""


def test_stats_subcommand(monkeypatch):
    events = [
        {"exit_code": 0, "latency_ms": 100},
        {"exit_code": 1, "latency_ms": 200},
        {"exit_code": 0, "latency_ms": 300},
    ]
    monkeypatch.setenv("EVENTS_URL", "https://example.com")
    monkeypatch.setattr(ai_cli.nsm_stats, "iter_events", lambda src: iter(events))
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["stats"])
    assert rc == 0
    text = out.getvalue()
    assert "Total runs: 3" in text
    assert "Success rate: 66.7%" in text
    assert "Average latency" in text


def test_stats_requires_url(monkeypatch):
    monkeypatch.delenv("EVENTS_URL", raising=False)
    monkeypatch.setattr(ai_cli.nsm_stats, "iter_events", lambda src: iter(()))
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        rc = ai_cli.main(["stats"])
    assert rc == 1


def test_plan_posts_event(monkeypatch):
    monkeypatch.setenv("EVENTS_URL", "https://example.com")
    monkeypatch.setenv("EVENTS_TOKEN", "tok")
    monkeypatch.setenv("USER", "alice")
    monkeypatch.setattr(ai_cli.ai_exec, "plan", lambda *a, **k: [PlanStep(1, "one")])
    sent = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        sent["url"] = url
        sent["headers"] = headers
        sent["data"] = json

        class Resp:
            status_code = 200

        return Resp()

    monkeypatch.setattr(telemetry.requests, "post", fake_post)
    rc = ai_cli.main(["plan", "goal", "--analytics"])
    assert rc == 0
    assert sent["url"] == "https://example.com"
    assert sent["headers"]["Authorization"] == "Bearer tok"
    payload = sent["data"]["payload"]
    assert payload["name"] == "ai-cli-plan"
    assert payload["goal"] == "goal"
    assert payload["step_count"] == 1
    assert "latency_ms" in payload


def test_do_posts_event(monkeypatch, tmp_path):
    monkeypatch.setenv("EVENTS_URL", "https://example.com")
    monkeypatch.setenv("EVENTS_TOKEN", "tok")
    monkeypatch.setenv("USER", "alice")
    monkeypatch.setattr(ai_cli.ai_exec, "plan", lambda *a, **k: [PlanStep(1, "echo hi")])
    monkeypatch.setattr("builtins.input", lambda _: "y")

    class Result:
        def __init__(self):
            self.stdout = ""
            self.stderr = ""
            self.returncode = 0

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: Result())
    sent = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        sent["url"] = url
        sent["headers"] = headers
        sent["data"] = json

        class Resp:
            status_code = 200

        return Resp()

    monkeypatch.setattr(telemetry.requests, "post", fake_post)
    log = tmp_path / "log.txt"
    rc = ai_cli.main(["do", "goal", "--log", str(log), "--analytics"])
    assert rc == 0
    payload = sent["data"]["payload"]
    assert payload["name"] == "ai-cli-do"
    assert payload["goal"] == "goal"
    assert payload["exit_code"] == 0
    assert payload["step_count"] == 1
    assert "latency_ms" in payload


def test_plan_nats_publish(monkeypatch):
    monkeypatch.setattr(ai_cli.ai_exec, "plan", lambda *a, **k: [PlanStep(1, "one")])
    published = []

    async def fake_publish(name, payload, *, url):

        published.append((url, name, payload))
        return True

    monkeypatch.setattr(ai_cli.ume_events, "publish_event", fake_publish)
    rc = ai_cli.main([
        "plan",
        "goal",
        "--analytics",
        "--nats-url",
        "nats://example.com",
    ])

    assert rc == 0
    url, name, payload = published[0]
    assert name == "ai-cli-plan"
    assert payload["goal"] == "goal"


def test_stats_fetches_events(monkeypatch):
    ndjson = "{""exit_code"": 0, ""latency_ms"": 100}\n{""exit_code"": 1, ""latency_ms"": 200}\n"
    monkeypatch.setenv("EVENTS_URL", "https://example.com/events")

    called = {}

    def fake_get(url, timeout=None):
        called["url"] = url

        class Resp:
            text = ndjson

            def raise_for_status(self):
                pass

        return Resp()

    monkeypatch.setattr(ai_cli.nsm_stats.requests, "get", fake_get)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["stats"])
    assert rc == 0
    assert called["url"] == "https://example.com/events"


def test_metrics_subcommand(monkeypatch):
    events = [
        {"name": "ai-do", "exit_code": 0, "developer": "alice", "end_ts": 1693516800},
        {"name": "ai-do", "exit_code": 0, "developer": "bob", "end_ts": 1693603200},
    ]
    monkeypatch.setenv("EVENTS_URL", "https://example.com")
    monkeypatch.setattr(ai_cli.nsm_stats, "iter_events", lambda src: iter(events))
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["metrics"])
    assert rc == 0
    expected = ai_cli.nsm_stats.aggregate_successful_runs(events)
    lines = out.getvalue().splitlines()
    exp_lines = []
    for dev in sorted(expected):
        for week in sorted(expected[dev]):
            exp_lines.append(f"{dev},{week},{expected[dev][week]}")
    assert lines == exp_lines


def test_metrics_aggregates_url(monkeypatch):
    monkeypatch.setenv("NSM_URL", "https://example.com/nsm")
    called = {}

    def fake_get(url, timeout=None):
        called["url"] = url

        class Resp:
            def raise_for_status(self):
                pass

            def json(self):
                return {"alice": {"2023-W01": 2}}

        return Resp()

    monkeypatch.setattr(ai_cli.requests, "get", fake_get)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.main(["metrics", "--aggregates-url", "https://example.com/nsm"])
    assert rc == 0
    assert called["url"] == "https://example.com/nsm"
    assert out.getvalue().splitlines() == ["alice,2023-W01,2"]


def test_metrics_requires_url(monkeypatch):
    monkeypatch.delenv("EVENTS_URL", raising=False)
    monkeypatch.setattr(ai_cli.nsm_stats, "iter_events", lambda src: iter(()))
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        rc = ai_cli.main(["metrics"])
    assert rc == 1


def test_metrics_main(monkeypatch):
    events = [
        {"name": "ai-do", "exit_code": 0, "developer": "alice", "end_ts": 1693516800},
        {"name": "ai-do", "exit_code": 0, "developer": "bob", "end_ts": 1693603200},
    ]
    monkeypatch.setenv("EVENTS_URL", "https://example.com")
    monkeypatch.setattr(ai_cli.nsm_stats, "iter_events", lambda src: iter(events))
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = ai_cli.metrics_main([])
    assert rc == 0
    expected = ai_cli.nsm_stats.aggregate_successful_runs(events)
    lines = out.getvalue().splitlines()
    exp_lines = []
    for dev in sorted(expected):
        for week in sorted(expected[dev]):
            exp_lines.append(f"{dev},{week},{expected[dev][week]}")
    assert lines == exp_lines

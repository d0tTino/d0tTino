import socket
import subprocess
import time

from scripts import ai_cli
import shutil
import pytest

import ume.events as events


def _start_nats_server() -> tuple[subprocess.Popen, str]:
    if not shutil.which("nats-server"):
        pytest.skip("nats-server not installed")
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    url = f"nats://127.0.0.1:{port}"
    proc = subprocess.Popen([
        "nats-server",
        "-a",
        "127.0.0.1",
        "-p",
        str(port),
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except OSError:
            time.sleep(0.1)
    else:
        proc.terminate()
        proc.wait()
        raise RuntimeError("failed to start nats-server")
    return proc, url


def test_ai_cli_plan_nats_events(monkeypatch):
    proc, url = _start_nats_server()
    monkeypatch.setattr(ai_cli.ai_exec, "plan", lambda *a, **k: ["echo hi"])

    captured = []

    async def fake_publish_event(url_arg, name_arg, payload_arg):
        captured.append((url_arg, name_arg, payload_arg))
        return True

    monkeypatch.setattr(events, "publish_event", fake_publish_event)
    try:
        rc = ai_cli.main(["plan", "echo", "--analytics", "--nats-url", url])
    finally:
        proc.terminate()
        proc.wait()

    assert rc == 0
    url_arg, name_arg, payload_arg = captured[0]
    assert url_arg == url
    assert name_arg == "ai-cli-plan"
    assert payload_arg["goal"] == "echo"
    assert payload_arg["step_count"] == 1

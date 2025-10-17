"""Primary command handlers executed by the CLI."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict

import requests

import importlib
from dataclasses import asdict

from scripts import recipes
from telemetry import analytics_default, record_event

from .actions import run_action, run_commands, tail_logs
from .env import load_env
from .models import DashboardSummary
from .utils import ensure_cache_dir, telemetry_status

API_URL_ENV = "TINO_API_URL"
DEFAULT_API_URL = "http://127.0.0.1:8000"


class CommandError(RuntimeError):
    """Raised when a CLI command fails."""

    def __init__(self, message: str, *, code: int = 1):
        super().__init__(message)
        self.code = code


def _api_base() -> str:
    load_env()
    return os.environ.get(API_URL_ENV, DEFAULT_API_URL).rstrip("/")


def plan(goal: str) -> dict[str, Any]:
    """Plan steps for ``goal`` via the HTTP API."""

    response = requests.post(
        f"{_api_base()}/api/plan",
        json={"goal": goal},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    steps = data.get("steps") or []

    cache_dir = ensure_cache_dir()
    log_path = cache_dir / "plans.log"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(goal + "\n")

    telemetry = telemetry_status()
    if telemetry.enabled:
        record_event(
            "plan",
            {"goal": goal, "step_count": len(steps), "timestamp": time.time()},
            enabled=True,
        )
    return {"steps": steps, "telemetry": asdict(telemetry)}


def exec(goal: str) -> dict[str, Any]:  # noqa: A003 - align with command name
    """Execute ``goal`` using the HTTP API."""

    response = requests.get(
        f"{_api_base()}/api/exec",
        params={"goal": goal},
        timeout=30,
    )
    response.raise_for_status()
    telemetry = telemetry_status()
    if telemetry.enabled:
        record_event(
            "exec",
            {"goal": goal, "timestamp": time.time()},
            enabled=True,
        )
    return {"output": response.text, "telemetry": asdict(telemetry)}


def list_recipes() -> dict[str, Any]:
    """Return available recipes."""

    importlib.invalidate_caches()
    importlib.reload(recipes)
    discovered = set(recipes.discover_recipes().keys())
    plugin_dir = Path(__file__).resolve().parents[2] / "scripts" / "recipes" / "plugins"
    if plugin_dir.exists():
        for file in plugin_dir.glob("*.py"):
            if file.stem not in {"__init__"}:
                discovered.add(file.stem)
    return {"recipes": sorted(discovered)}


def open_prompt_file(path: str) -> dict[str, Any]:
    """Read a prompt file from disk."""

    content = Path(path).read_text(encoding="utf-8")
    return {"content": content}


def run_recipe(name: str, goal: str) -> dict[str, Any]:
    """Execute a recipe and return its log."""

    importlib.invalidate_caches()
    importlib.reload(recipes)
    mapping = recipes.discover_recipes()
    if name not in mapping:
        raise CommandError(f"Recipe '{name}' not found", code=2)

    cache_dir = ensure_cache_dir()
    log_path = cache_dir / f"recipe-{name}.log"
    commands = list(mapping[name](goal))
    exit_code, _ = run_commands(commands, log_path)
    log_content = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    telemetry = telemetry_status()
    return {
        "log": log_content,
        "exit_code": exit_code,
        "log_path": str(log_path),
        "telemetry": asdict(telemetry),
    }


def record_event_cli(name: str, payload: Dict[str, Any]) -> dict[str, Any]:
    """Record a telemetry event using ``telemetry.record_event``."""

    enabled = analytics_default()
    success = record_event(name, payload, enabled=enabled)
    return {"success": success, "enabled": enabled}


def toggle_plugin(name: str, enable: bool) -> dict[str, Any]:
    """Enable or disable a MCP plugin descriptor."""

    cache_dir = Path.home() / ".config" / "d0tTino"
    cfg_path = cache_dir / "mcp.json"
    cache_dir.mkdir(parents=True, exist_ok=True)

    current: Dict[str, Any] = {}
    if cfg_path.exists():
        try:
            current = json.loads(cfg_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            current = {}

    if enable:
        registry_path = _api_registry_path()
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        descriptor = (
            registry.get("plugins", {})
            .get(name, {})
            .get("mcp", {})
            .get("descriptor")
        )
        if not descriptor:
            raise CommandError("plugin-descriptor-missing", code=3)
        current[name] = descriptor
    else:
        current.pop(name, None)

    cfg_path.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return {"success": True, "path": str(cfg_path)}


def _api_registry_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    return root / "plugin-registry.json"


def dashboard() -> dict[str, Any]:
    """Assemble dashboard summary information."""

    cache_dir = ensure_cache_dir()
    plans_log = cache_dir / "plans.log"
    recent = []
    if plans_log.exists():
        recent = [line.strip() for line in plans_log.read_text(encoding="utf-8").splitlines() if line.strip()][-5:]
        recent.reverse()

    # Budget information stored in llm router budget file
    history: list[int] = []
    budget: int | None = None
    budget_path = os.environ.get("LLM_BUDGET_PATH")
    budget_file: Path | None = None
    if budget_path:
        budget_file = Path(budget_path)
    else:
        try:
            from llm.router import _BUDGET_PATH, get_budget  # type: ignore

            budget, _, _ = get_budget()
            budget_file = Path(_BUDGET_PATH)
        except Exception:  # noqa: BLE001 - optional dependency missing
            budget_file = None

    if budget_file and budget_file.exists():
        try:
            data = json.loads(budget_file.read_text(encoding="utf-8"))
            history = [int(x) for x in data.get("history", [])]
            if budget is None and data.get("budget") is not None:
                budget = int(data["budget"])
        except Exception:  # noqa: BLE001
            history = []

    plugins = []
    cfg_path = Path.home() / ".config" / "d0tTino" / "mcp.json"
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            plugins = [{"name": key, "enabled": True} for key in sorted(cfg.keys())]
        except json.JSONDecodeError:
            plugins = []

    summary = DashboardSummary(
        recent_plans=recent,
        budget=budget,
        budget_history=history,
        plugins=plugins,
    )
    return {"dashboard": asdict(summary)}


def cockpit_action(
    name: str,
    *,
    payload: str | None = None,
    confirm: bool = False,
    job_id: str | None = None,
) -> dict[str, Any]:
    """Execute a named cockpit action."""

    result = run_action(name, payload=payload, confirm=confirm, job_id=job_id)
    return {"result": {
        "message": result.message,
        "telemetry": asdict(result.telemetry) if result.telemetry else None,
        "details": result.details,
    }}


def cockpit_logs(limit: int = 200) -> dict[str, Any]:
    """Return cockpit log entries."""

    return tail_logs(limit)


__all__ = [
    "CommandError",
    "cockpit_action",
    "cockpit_logs",
    "dashboard",
    "exec",
    "list_recipes",
    "open_prompt_file",
    "plan",
    "record_event_cli",
    "run_recipe",
    "toggle_plugin",
]

"""Entry point for the Typer-powered ``tino`` command."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

import typer

from telemetry import analytics_default

from .clients import DocsClient, FinanceClient, StormClient, TaskCascadenceClient, UMEClient
from .config import load_env_defaults
from .executor import execute_command
from .plugin_loader import register_plugin_commands
from .state import CLIState

app = typer.Typer(help="Automation interface for d0tTino tooling.", no_args_is_help=True)


def _set_state(ctx: typer.Context, *, dry_run: bool, confirm: bool) -> CLIState:
    load_env_defaults()
    log_path = Path(os.environ.get("TINO_CLI_LOG", "tino-cli.log"))
    state = CLIState(
        dry_run=dry_run,
        confirm=confirm,
        telemetry_enabled=analytics_default(),
        log_path=log_path,
    )
    ctx.obj = state
    return state


def _get_state(ctx: typer.Context) -> CLIState:
    state = getattr(ctx, "obj", None)
    if isinstance(state, CLIState):
        return state
    raise RuntimeError("CLI state not initialised")


@app.callback()
def main(
    ctx: typer.Context,
    confirm: bool = typer.Option(False, "--confirm", help="Execute actions that change remote state."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview actions without executing them."),
) -> None:
    """Initialise shared CLI state for sub-commands."""

    _set_state(ctx, dry_run=dry_run, confirm=confirm)


# ---------------------------------------------------------------------------
# Bootstrap helpers
# ---------------------------------------------------------------------------
bootstrap_app = typer.Typer(help="Bootstrap local tooling and environments.")


@bootstrap_app.command("init")
def bootstrap_init(ctx: typer.Context, quick: bool = typer.Option(False, "--quick", help="Skip optional setup.")) -> None:
    """Initialise local tooling by delegating to ``install.sh``."""

    state = _get_state(ctx)
    script = Path("scripts") / "install.sh"
    command = ["bash", str(script)]
    if quick:
        command.append("--quick")
    code = execute_command(command, state=state, require_confirm=True)
    raise typer.Exit(code)


@bootstrap_app.command("doctor")
def bootstrap_doctor(ctx: typer.Context) -> None:
    """Run repository health checks."""

    state = _get_state(ctx)
    script = Path("scripts") / "check-hooks.sh"
    code = execute_command(["bash", str(script)], state=state)
    raise typer.Exit(code)


@bootstrap_app.command("whoami")
def bootstrap_whoami(ctx: typer.Context) -> None:
    """Display the CLI execution context."""

    state = _get_state(ctx)
    if state.dry_run:
        typer.echo("[dry-run] Displaying CLI state")
        raise typer.Exit(0)
    typer.echo(json.dumps({
        "confirm": state.confirm,
        "telemetry": state.telemetry_enabled,
        "log_path": str(state.log_path),
    }, indent=2))


app.add_typer(bootstrap_app, name="bootstrap")


# ---------------------------------------------------------------------------
# Stack orchestration (docker-compose)
# ---------------------------------------------------------------------------
stack_app = typer.Typer(help="Orchestrate local docker-compose services.")
COMPOSE_FILE = Path("docker-compose.yml")


def _compose_command(*args: str) -> Tuple[str, ...]:
    return ("docker", "compose", "-f", str(COMPOSE_FILE), *args)


@stack_app.command("up")
def stack_up(ctx: typer.Context, service: Optional[str] = typer.Argument(None)) -> None:
    """Start services defined in docker-compose."""

    state = _get_state(ctx)
    command = list(_compose_command("up", "-d"))
    if service:
        command.append(service)
    code = execute_command(command, state=state, require_confirm=True)
    raise typer.Exit(code)


@stack_app.command("down")
def stack_down(ctx: typer.Context) -> None:
    """Stop services defined in docker-compose."""

    state = _get_state(ctx)
    command = _compose_command("down")
    code = execute_command(command, state=state, require_confirm=True)
    raise typer.Exit(code)


@stack_app.command("logs")
def stack_logs(ctx: typer.Context, service: str = typer.Argument(..., help="Service name.")) -> None:
    """Stream logs for ``service`` via docker-compose."""

    state = _get_state(ctx)
    command = list(_compose_command("logs", "-f", service))
    if state.dry_run:
        typer.echo(f"[dry-run] {' '.join(map(shlex.quote, command))}")
        raise typer.Exit(0)
    if not state.confirm:
        typer.echo("Use --confirm to stream live logs.", err=True)
        raise typer.Exit(1)
    raise typer.Exit(subprocess.call(command))


app.add_typer(stack_app, name="stack")


# ---------------------------------------------------------------------------
# TaskCascadence
# ---------------------------------------------------------------------------
task_app = typer.Typer(help="Interact with TaskCascadence services.")


def _render_response(result) -> None:
    if result is None:
        return
    typer.echo(json.dumps(result.payload, indent=2))


@task_app.command("run")
def task_run(ctx: typer.Context, task: str = typer.Argument(..., help="Task identifier"), payload: Optional[str] = typer.Option(None, "--payload", help="JSON payload.")) -> None:
    state = _get_state(ctx)
    client = TaskCascadenceClient()
    body = json.loads(payload) if payload else None
    result = client.run(state, task, payload=body)
    _render_response(result)


@task_app.command("status")
def task_status(ctx: typer.Context, task_id: str = typer.Argument(...)) -> None:
    state = _get_state(ctx)
    client = TaskCascadenceClient()
    result = client.status(state, task_id)
    _render_response(result)


@task_app.command("signal")
def task_signal(ctx: typer.Context, task_id: str = typer.Argument(...), signal: str = typer.Option(..., "--signal", help="Signal name.")) -> None:
    state = _get_state(ctx)
    if not state.confirm:
        typer.echo("Use --confirm to send signals to remote tasks.", err=True)
        raise typer.Exit(1)
    client = TaskCascadenceClient()
    result = client.signal(state, task_id, signal=signal)
    _render_response(result)


app.add_typer(task_app, name="task")


# ---------------------------------------------------------------------------
# Research helpers
# ---------------------------------------------------------------------------
research_app = typer.Typer(help="Interact with tino-storm research services.")


@research_app.command("ingest")
def research_ingest(ctx: typer.Context, topic: str = typer.Argument(...), source: str = typer.Argument(...)) -> None:
    state = _get_state(ctx)
    client = StormClient()
    result = client.ingest(state, topic=topic, source=source)
    _render_response(result)


@research_app.command("draft")
def research_draft(ctx: typer.Context, topic: str = typer.Argument(...), hint: Optional[str] = typer.Option(None, "--hint", help="JSON object of hints.")) -> None:
    state = _get_state(ctx)
    hints = json.loads(hint) if hint else None
    client = StormClient()
    result = client.draft(state, topic=topic, hints=hints or None)
    _render_response(result)


app.add_typer(research_app, name="research")


# ---------------------------------------------------------------------------
# UME memory helpers
# ---------------------------------------------------------------------------
ume_app = typer.Typer(help="Capture ideas and query UME memories.")


@ume_app.command("idea")
def ume_idea(ctx: typer.Context, text: str = typer.Argument(..., help="Idea text.")) -> None:
    state = _get_state(ctx)
    client = UMEClient()
    result = client.submit_idea(state, text=text)
    _render_response(result)


@ume_app.command("mem")
def ume_memory_query(ctx: typer.Context, query: str = typer.Argument(..., help="Query text."), filters: Optional[str] = typer.Option(None, "--filters", help="JSON filters.")) -> None:
    state = _get_state(ctx)
    client = UMEClient()
    payload = json.loads(filters) if filters else None
    result = client.query(state, query=query, filters=payload)
    _render_response(result)


app.add_typer(ume_app, name="ume")


# ---------------------------------------------------------------------------
# Finance helpers
# ---------------------------------------------------------------------------
finance_app = typer.Typer(help="Finance reporting utilities.")


@finance_app.command("report")
def finance_report(ctx: typer.Context, period: str = typer.Option("monthly", "--period", help="Reporting period.")) -> None:
    state = _get_state(ctx)
    client = FinanceClient()
    result = client.summarize(state, period=period)
    _render_response(result)


@finance_app.command("sync")
def finance_sync(ctx: typer.Context, provider: str = typer.Argument(...)) -> None:
    state = _get_state(ctx)
    if not state.confirm:
        typer.echo("Use --confirm to trigger finance synchronisation.", err=True)
        raise typer.Exit(1)
    client = FinanceClient()
    result = client.sync(state, provider=provider)
    _render_response(result)


app.add_typer(finance_app, name="finance")


# ---------------------------------------------------------------------------
# Wishlist helpers
# ---------------------------------------------------------------------------
wishlist_app = typer.Typer(help="Track wishlist items for the platform.")
WISHLIST_PATH = Path("metadata") / "wishlist.json"


@wishlist_app.command("add")
def wishlist_add(ctx: typer.Context, item: str = typer.Argument(...), link: Optional[str] = typer.Option(None, "--link", help="Optional URL.")) -> None:
    state = _get_state(ctx)
    if state.dry_run:
        typer.echo(f"[dry-run] add wishlist item: {item}")
        raise typer.Exit(0)
    if not WISHLIST_PATH.exists():
        data = []
    else:
        data = json.loads(WISHLIST_PATH.read_text(encoding="utf-8"))
    data.append({"item": item, "link": link})
    WISHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    WISHLIST_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    typer.echo(f"Added wishlist item '{item}'.")


@wishlist_app.command("list")
def wishlist_list(ctx: typer.Context) -> None:
    state = _get_state(ctx)
    if not WISHLIST_PATH.exists():
        typer.echo("Wishlist is empty.")
        return
    typer.echo(WISHLIST_PATH.read_text(encoding="utf-8"))


app.add_typer(wishlist_app, name="wishlist")


# ---------------------------------------------------------------------------
# Documentation publishing
# ---------------------------------------------------------------------------
docs_app = typer.Typer(help="Publish documentation updates.")


@docs_app.command("publish")
def docs_publish(ctx: typer.Context, site: str = typer.Argument(...), version: Optional[str] = typer.Option(None, "--version", help="Version label.")) -> None:
    state = _get_state(ctx)
    client = DocsClient()
    result = client.publish(state, site=site, version=version)
    _render_response(result)


app.add_typer(docs_app, name="docs")


# ---------------------------------------------------------------------------
# Legacy compatibility
# ---------------------------------------------------------------------------
legacy_app = typer.Typer(help="Compatibility shims for legacy CLIs.")


@legacy_app.command("ai")
def legacy_ai(
    ctx: typer.Context,
    args: Optional[List[str]] = typer.Argument(None, help="Arguments forwarded to scripts.ai_cli.", show_default=False),
) -> None:
    state = _get_state(ctx)
    if state.dry_run:
        typer.echo("[dry-run] invoke legacy ai_cli")
        raise typer.Exit(0)
    from scripts import ai_cli

    forwarded = list(args or [])
    code = ai_cli.main(forwarded or None)
    raise typer.Exit(code)


app.add_typer(legacy_app, name="legacy")


# ---------------------------------------------------------------------------
# Plugin commands
# ---------------------------------------------------------------------------
plugins_app = typer.Typer(help="Commands exposed by installed plug-ins.")
register_plugin_commands(plugins_app)
app.add_typer(plugins_app, name="plugins")


def main() -> None:
    """Invoke the Typer application."""

    app()


if __name__ == "__main__":
    main()

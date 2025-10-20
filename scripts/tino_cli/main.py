"""Entry point for the Typer-powered ``tino`` command."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path
from typing import Mapping, Optional, Sequence

import typer

from telemetry import analytics_default

from .clients import (
    DocsClient,
    FinanceClient,
    StormClient,
    TaskCascadenceClient,
    UMEClient,
)
from .config import (
    DOCS,
    FINANCE,
    STORM,
    TASKCASCADENCE,
    UME,
    ServiceConfig,
    load_env_defaults,
)
from .plugin_loader import register_plugin_commands
from .state import CLIState, snapshot_identity, stable_dict

app = typer.Typer(help="Automation interface for d0tTino tooling.", no_args_is_help=True)

COMPOSE_FILE = Path("docker-compose.yml")
WISHLIST_PATH = Path("metadata") / "wishlist.json"


_SERVICE_CONFIGS: tuple[tuple[str, ServiceConfig], ...] = (
    ("docs", DOCS),
    ("finance", FINANCE),
    ("storm", STORM),
    ("taskcascadence", TASKCASCADENCE),
    ("ume", UME),
)


def build_state(*, dry_run: bool, confirm: bool) -> CLIState:
    """Create a :class:`CLIState` populated with environment defaults."""

    load_env_defaults()
    log_path = Path(os.environ.get("TINO_CLI_LOG", "tino-cli.log"))
    identity = snapshot_identity()
    services = stable_dict({name: config.resolve() for name, config in _SERVICE_CONFIGS})
    return CLIState(
        dry_run=dry_run,
        confirm=confirm,
        telemetry_enabled=analytics_default(),
        log_path=log_path,
        identity=identity,
        services=services,
    )


def _set_state(ctx: typer.Context, *, dry_run: bool, confirm: bool) -> CLIState:
    state = build_state(dry_run=dry_run, confirm=confirm)
    ctx.obj = state
    return state


def _get_state(ctx: typer.Context) -> CLIState:
    state = getattr(ctx, "obj", None)
    if isinstance(state, CLIState):
        return state
    raise RuntimeError("CLI state not initialised")


def run_shell_command(
    state: CLIState,
    command: Sequence[str],
    *,
    require_confirm: bool = False,
    confirm_message: str = "Use --confirm to execute this command.",
) -> int:
    """Execute ``command`` respecting ``dry_run`` and ``confirm`` flags."""

    printable = shlex.join(command)
    if state.dry_run:
        typer.echo(f"[dry-run] {printable}")
        return 0
    if require_confirm and not state.confirm:
        typer.echo(confirm_message, err=True)
        return 1
    return subprocess.call(list(command))


def compose_command(*args: str) -> tuple[str, ...]:
    """Return a docker compose command tuple."""

    return ("docker", "compose", "-f", str(COMPOSE_FILE), *args)


def init_tooling(state: CLIState, *, quick: bool = False) -> int:
    script = Path("scripts") / "install.sh"
    command = ["bash", str(script)]
    if quick:
        command.append("--quick")
    return run_shell_command(state, command, require_confirm=True)


def run_doctor(state: CLIState) -> int:
    script = Path("scripts") / "check-hooks.sh"
    return run_shell_command(state, ["bash", str(script)])


def show_whoami(state: CLIState) -> dict[str, object]:
    identity = stable_dict(dict(state.identity))
    services = stable_dict(dict(state.services))
    payload = {
        "confirm": state.confirm,
        "telemetry": state.telemetry_enabled,
        "log_path": str(state.log_path),
        "identity": identity,
        "services": services,
    }
    return stable_dict(payload)


def start_services(state: CLIState, service: str | None = None) -> int:
    command: list[str] = list(compose_command("up", "-d"))
    if service:
        command.append(service)
    return run_shell_command(state, command, require_confirm=True)


def stop_services(state: CLIState) -> int:
    command = compose_command("down")
    return run_shell_command(state, command, require_confirm=True)


def stream_logs(state: CLIState, service: str) -> int:
    command = compose_command("logs", "-f", service)
    return run_shell_command(
        state,
        command,
        require_confirm=True,
        confirm_message="Use --confirm to stream live logs.",
    )


def task_run_operation(
    state: CLIState,
    task: str,
    *,
    payload: Mapping[str, object] | None = None,
):
    client = TaskCascadenceClient()
    return client.run(state, task, payload=payload)


def task_status_operation(state: CLIState, task_id: str):
    client = TaskCascadenceClient()
    return client.status(state, task_id)


def task_signal_operation(
    state: CLIState,
    task_id: str,
    *,
    signal: str,
    link: str | None = None,
    note: str | None = None,
):
    client = TaskCascadenceClient()
    return client.signal(state, task_id, signal=signal, link=link, note=note)


def research_ingest_operation(
    state: CLIState,
    *,
    topic: str | None = None,
    source: str,
):
    client = StormClient()
    return client.ingest(state, topic=topic, source=source)


def research_draft_operation(
    state: CLIState,
    *,
    topic: str | None = None,
    hints: Mapping[str, object] | None = None,
    doc: str | None = None,
    anchor: str | None = None,
    prompt: str | None = None,
):
    client = StormClient()
    return client.draft(state, topic=topic, hints=hints or None, doc=doc, anchor=anchor, prompt=prompt)


def idea_submit_operation(state: CLIState, *, text: str):
    client = UMEClient()
    return client.submit_idea(state, text=text)


def mem_query_operation(
    state: CLIState,
    *,
    query: str,
    filters: Mapping[str, object] | None = None,
):
    client = UMEClient()
    return client.query(state, query=query, filters=filters)


def finance_snapshot_operation(
    state: CLIState, *, period: str, month: Optional[str] = None
):
    client = FinanceClient()
    return client.snapshot(state, period=period, month=month)


def finance_sync_operation(state: CLIState, *, provider: str):
    client = FinanceClient()
    return client.sync(state, provider=provider)


def wishlist_add_operation(state: CLIState, *, url: str, tags: Sequence[str] | None = None) -> dict[str, object]:
    entry: dict[str, object] = {"url": url}
    if tags:
        entry["tags"] = list(tags)
    if state.dry_run:
        return {"entry": entry, "path": str(WISHLIST_PATH)}
    try:
        if WISHLIST_PATH.exists():
            data = json.loads(WISHLIST_PATH.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                data = []
        else:
            data = []
    except json.JSONDecodeError:
        data = []
    data.append(entry)
    WISHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    WISHLIST_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return {"entry": entry, "path": str(WISHLIST_PATH)}


def docs_publish_operation(
    state: CLIState,
    *,
    target: str,
    site: str | None = None,
    version: str | None = None,
):
    client = DocsClient()
    return client.publish(state, target=target, site=site, version=version)


def _render_response(result) -> None:
    if result is None:
        return
    payload = getattr(result, "payload", result)
    typer.echo(json.dumps(payload, indent=2))


@app.callback()
def _configure_app(
    ctx: typer.Context,
    confirm: bool = typer.Option(False, "--confirm", help="Execute actions that change remote state."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview actions without executing them."),
) -> None:
    """Initialise shared CLI state for sub-commands."""

    _set_state(ctx, dry_run=dry_run, confirm=confirm)


@app.command("init")
def cli_init(ctx: typer.Context, quick: bool = typer.Option(False, "--quick", help="Skip optional setup.")) -> None:
    state = _get_state(ctx)
    code = init_tooling(state, quick=quick)
    raise typer.Exit(code)


@app.command("doctor")
def cli_doctor(ctx: typer.Context) -> None:
    state = _get_state(ctx)
    code = run_doctor(state)
    raise typer.Exit(code)


@app.command("whoami")
def cli_whoami(ctx: typer.Context) -> None:
    state = _get_state(ctx)
    if state.dry_run:
        typer.echo("[dry-run] Displaying CLI state")
        raise typer.Exit(0)
    typer.echo(json.dumps(show_whoami(state), indent=2))


@app.command("up")
def cli_up(ctx: typer.Context, service: str = typer.Argument(None, help="Optional service name.")) -> None:
    state = _get_state(ctx)
    code = start_services(state, service or None)
    raise typer.Exit(code)


@app.command("down")
def cli_down(ctx: typer.Context) -> None:
    state = _get_state(ctx)
    code = stop_services(state)
    raise typer.Exit(code)


@app.command("logs")
def cli_logs(ctx: typer.Context, service: str = typer.Argument(..., help="Service name.")) -> None:
    state = _get_state(ctx)
    code = stream_logs(state, service)
    raise typer.Exit(code)


task_app = typer.Typer(help="Interact with TaskCascadence services.")


@task_app.command("run")
def task_run(
    ctx: typer.Context,
    task: str = typer.Argument(..., help="Task identifier"),
    payload: str = typer.Option(None, "--payload", "--json", help="JSON payload."),
) -> None:
    state = _get_state(ctx)
    body = json.loads(payload) if payload else None
    result = task_run_operation(state, task, payload=body)
    _render_response(result)


@task_app.command("status")
def task_status(ctx: typer.Context, task_id: str = typer.Argument(...)) -> None:
    state = _get_state(ctx)
    result = task_status_operation(state, task_id)
    _render_response(result)


@task_app.command("signal")
def task_signal(
    ctx: typer.Context,
    task_id: str = typer.Argument(...),
    signal: Optional[str] = typer.Option(
        None,
        "--signal",
        help="Signal name. Defaults to link, note, or link_and_note based on payload.",
    ),
    link: str = typer.Option(None, "--link", help="Optional link payload."),
    note: str = typer.Option(None, "--note", help="Optional note payload."),
) -> None:
    state = _get_state(ctx)
    if not state.confirm:
        typer.echo("Use --confirm to send signals to remote tasks.", err=True)
        raise typer.Exit(1)
    resolved_link = link or None
    resolved_note = note or None
    resolved_signal = signal or None
    if resolved_signal is None:
        payload_hints: list[str] = []
        if resolved_link:
            payload_hints.append("link")
        if resolved_note:
            payload_hints.append("note")
        if not payload_hints:
            typer.echo("Provide --signal or include --link/--note payload.", err=True)
            raise typer.Exit(1)
        resolved_signal = "_and_".join(payload_hints)
    result = task_signal_operation(
        state,
        task_id,
        signal=resolved_signal,
        link=resolved_link,
        note=resolved_note,
    )
    _render_response(result)


app.add_typer(task_app, name="task")


research_app = typer.Typer(help="Interact with tino-storm research services.")


@research_app.command("ingest")
def research_ingest(
    ctx: typer.Context,
    source: str = typer.Argument(..., help="Source URL or path."),
    topic: str = typer.Option(None, "--topic", help="Optional research topic."),
) -> None:
    state = _get_state(ctx)
    result = research_ingest_operation(state, source=source, topic=topic or None)
    _render_response(result)


@research_app.command("draft")
def research_draft(
    ctx: typer.Context,
    topic: str = typer.Option(None, "--topic", help="Optional research topic."),
    hint: str = typer.Option(None, "--hint", help="JSON object of hints."),
    doc: str = typer.Option(None, "--doc", help="Document identifier or path."),
    anchor: str = typer.Option(None, "--anchor", help="Anchor identifier."),
    prompt: str = typer.Option(None, "--prompt", help="Prompt override."),
) -> None:
    state = _get_state(ctx)
    hints = json.loads(hint) if hint else None
    result = research_draft_operation(
        state,
        topic=topic or None,
        hints=hints,
        doc=doc or None,
        anchor=anchor or None,
        prompt=prompt or None,
    )
    _render_response(result)


app.add_typer(research_app, name="research")


@app.command("idea")
def ume_idea(ctx: typer.Context, text: str = typer.Argument(..., help="Idea text.")) -> None:
    state = _get_state(ctx)
    result = idea_submit_operation(state, text=text)
    _render_response(result)


mem_app = typer.Typer(help="Query stored UME memories.")


@mem_app.command("query")
def ume_memory_query(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Query text."),
    filters: str = typer.Option(None, "--filters", help="JSON filters."),
) -> None:
    state = _get_state(ctx)
    payload = json.loads(filters) if filters else None
    result = mem_query_operation(state, query=query, filters=payload)
    _render_response(result)


app.add_typer(mem_app, name="mem")


finance_app = typer.Typer(help="Finance reporting utilities.")


@finance_app.command("snapshot")
def finance_snapshot(
    ctx: typer.Context,
    period: str = typer.Option("monthly", "--period", help="Reporting period."),
    month: Optional[str] = typer.Option(None, "--month", help="Specific month (YYYY-MM)."),
) -> None:
    state = _get_state(ctx)
    result = finance_snapshot_operation(state, period=period, month=month or None)
    _render_response(result)


@finance_app.command("sync")
def finance_sync(ctx: typer.Context, provider: str = typer.Argument(...)) -> None:
    state = _get_state(ctx)
    if not state.confirm:
        typer.echo("Use --confirm to trigger finance synchronisation.", err=True)
        raise typer.Exit(1)
    result = finance_sync_operation(state, provider=provider)
    _render_response(result)


app.add_typer(finance_app, name="finance")


wishlist_app = typer.Typer(help="Track wishlist items for the platform.")


@wishlist_app.command("add")
def wishlist_add(
    ctx: typer.Context,
    url: str = typer.Argument(..., help="Item URL."),
    tags: str = typer.Option(None, "--tags", help="Comma separated tags."),
) -> None:
    state = _get_state(ctx)
    parsed_tags = [tag.strip() for tag in (tags.split(",") if tags else []) if tag.strip()]
    result = wishlist_add_operation(state, url=url, tags=parsed_tags)
    if state.dry_run:
        typer.echo(f"[dry-run] add wishlist item: {json.dumps(result['entry'])}")
        return
    typer.echo(f"Added wishlist item '{url}'.")


@wishlist_app.command("list")
def wishlist_list(ctx: typer.Context) -> None:
    _get_state(ctx)
    if not WISHLIST_PATH.exists():
        typer.echo("Wishlist is empty.")
        return
    typer.echo(WISHLIST_PATH.read_text(encoding="utf-8"))


app.add_typer(wishlist_app, name="wishlist")


docs_app = typer.Typer(help="Publish documentation updates.")


@docs_app.command("publish")
def docs_publish(
    ctx: typer.Context,
    target: str = typer.Argument(..., help="Document path or identifier."),
    site: str = typer.Option(None, "--site", help="Documentation site."),
    version: str = typer.Option(None, "--version", help="Version label."),
) -> None:
    state = _get_state(ctx)
    result = docs_publish_operation(state, target=target, site=site or None, version=version or None)
    _render_response(result)


app.add_typer(docs_app, name="docs")


# Compatibility shims -------------------------------------------------------

bootstrap_app = typer.Typer(help="Bootstrap local tooling and environments.", hidden=True)


@bootstrap_app.command("init")
def bootstrap_init(ctx: typer.Context, quick: bool = typer.Option(False, "--quick")) -> None:
    state = _get_state(ctx)
    code = init_tooling(state, quick=quick)
    raise typer.Exit(code)


@bootstrap_app.command("doctor")
def bootstrap_doctor(ctx: typer.Context) -> None:
    state = _get_state(ctx)
    code = run_doctor(state)
    raise typer.Exit(code)


@bootstrap_app.command("whoami")
def bootstrap_whoami(ctx: typer.Context) -> None:
    cli_whoami(ctx)


app.add_typer(bootstrap_app, name="bootstrap")


stack_app = typer.Typer(help="Legacy stack orchestration commands.", hidden=True)


@stack_app.command("up")
def stack_up(ctx: typer.Context, service: str = typer.Argument(None)) -> None:
    cli_up(ctx, service or None)


@stack_app.command("down")
def stack_down(ctx: typer.Context) -> None:
    cli_down(ctx)


@stack_app.command("logs")
def stack_logs(ctx: typer.Context, service: str = typer.Argument(...)) -> None:
    cli_logs(ctx, service)


app.add_typer(stack_app, name="stack")


# Legacy compatibility ------------------------------------------------------

legacy_app = typer.Typer(help="Compatibility shims for legacy CLIs.")


@legacy_app.command("ai")
def legacy_ai(
    ctx: typer.Context,
    args: list[str] = typer.Argument(None, help="Arguments forwarded to scripts.ai_cli.", show_default=False),
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


# Plug-in commands ----------------------------------------------------------

plugins_app = typer.Typer(help="Commands exposed by installed plug-ins.")
register_plugin_commands(plugins_app)
app.add_typer(plugins_app, name="plugins")


def main() -> None:
    """Invoke the Typer application."""

    app()


if __name__ == "__main__":
    main()

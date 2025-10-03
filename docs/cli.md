# CLI Scenarios

The Typer-powered ``tino`` command consolidates automation helpers, docker
stack management, TaskCascadence orchestration and the plug-in runtime. The
examples below highlight practical combinations of the refactored
subcommands.

## Switching workstation state

The ``--dry-run`` and ``--confirm`` flags give you guardrails when bootstrapping
a fresh workstation. Start by inspecting what would run:

```bash
tino --dry-run init
```

When the preview looks correct, rerun with confirmation to execute the
installer and docker bootstrap:

```bash
tino --confirm init
tino --confirm up
```

Use ``tino whoami`` at any point to verify the active flags and telemetry
status. ``TINO_CLI_LOG`` controls where transcripts are written when
``--confirm`` actions run.

## Task lifecycle with confirmations

TaskCascadence helpers live under ``tino task``. Run a task and monitor its
status:

```bash
tino task run weekly-report --payload '{"period": "last-week"}'
tino task status 01HRZ73CJT37P9QZD7XQ3E5A4V
```

Signals modify remote state and therefore require explicit confirmation:

```bash
tino --confirm task signal 01HRZ73CJT37P9QZD7XQ3E5A4V --signal retry
```

## Research and memory coordination

Capture research inputs from the CLI and reference them in UME memories:

```bash
tino research ingest productivity https://example.com/outline.pdf
tino research draft productivity --hint '{"tone": "concise"}'
tino idea "Capture follow-up questions for tomorrow's sync"
tino mem query "follow-up questions" --filters '{"tag": "sync"}'
```

The ``tino docs publish`` command accepts ``--confirm`` when used in production
pipelines and respects ``TINO_DOC_TARGET`` to select the default publish slot.

## Plug-ins and dynamic commands

Plug-in packages from ``plugin-registry.json`` register additional commands. To
discover them, inspect the group help:

```bash
tino plugins --help
```

Run a plug-in provided command by name. Any command marked as
``confirm_required`` in the registry will refuse to execute without the flag:

```bash
tino --confirm plugins aiga deploy --env staging
```

If a plug-in is missing locally the CLI prints installation hints based on the
registry metadata.

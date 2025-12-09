# Constellation Technical Requirements

This contract distils the Constellation brief into a single checklist for
contributors. It covers the canonical CLI surface, safety rails, service
endpoints, plug-in validation rules, and GUI coupling. See the [README](README.md)
for the broader product overview.

## CLI contract

The Typer-powered `tino` entrypoint must provide the following subcommands and
behaviours:

- `tino init` bootstraps local tooling via `install.sh` and **only** runs when
  `--confirm` is supplied.
- `tino doctor` runs environment checks and Git hook validation.
- `tino whoami` reports the current CLI state, including telemetry and active
  safety flags such as `--dry-run`.
- `tino up` / `tino down` manage the `docker-compose` stack (optionally for a
  single service). Both refuse to mutate services without `--confirm`.
- `tino logs` streams `docker-compose` logs and requires `--confirm` before
  entering the interactive stream.
- `tino task run <task_name> [--json payload]` executes TaskCascadence tasks;
  `task status` remains available, and `task signal` always requires
  `--confirm` (signal type is inferred from `--link` or `--note`).
- `tino task schedule list` exposes current automation windows and honours
  `--dry-run`; `task schedule update` only proceeds with both a valid `--json`
  payload and `--confirm`.
- `tino research …` surfaces `ingest` and `draft` helpers for research work.
- `tino idea` captures a quick note or event and forwards it to UME memory.
- `tino mem …` queries UME memory with structured filters.
- `tino finance …` supports `snapshot --month YYYY-MM` (or `--period`) and a
  `sync` path that refuses to run without `--confirm`.
- `tino wishlist …` appends or lists entries from `metadata/wishlist.json`.
- `tino docs publish` publishes generated documentation and respects
  `TINO_DOC_TARGET` when the target is omitted; production usage expects
  `--confirm`.
- `tino plugins …` dynamically loads plug-in supplied commands from the registry
  and renders any tags or examples in Typer help.
- `tino legacy ai` provides a shim for `scripts/ai_cli.py` for backwards
  compatibility.

### Safety flags and environment settings

- `--dry-run` prints the command transcript without executing changes.
- `--confirm` is required for any command that mutates remote or stateful
  services (for example, `init`, `up`, `down`, `task signal`, `task schedule update`,
  `finance sync`, and `docs publish`).
- Telemetry and transcript destinations honour environment variables such as
  `TINO_CLI_LOG` (log destination) and `TINO_DOC_TARGET` (default doc publish
  target).

## Service endpoints

The FastAPI backend driving the Constellation dashboard and cockpit MUST expose
at least the following routes (default host: `http://localhost:8000`):

- `GET /api/stats` – summary metrics for queries and memory usage.
- `GET /api/graph` – the current memory graph as JSON.
- `POST /api/palette` – apply a colour palette.
- `POST /api/prompt` – forward an LLM prompt and return the response.
- `GET /api/health` – health check.
- `POST /api/plan` – generate shell steps for a goal.
- `GET /api/exec?goal=` – execute planned steps and stream logs as SSE.

## Plug-in registry expectations

- Registry payloads **must** validate against
  [`plugin-registry.schema.json`](plugin-registry.schema.json). Required
  top-level fields: `name`, `version`, `commands`, and `taskTemplates`.
- Command descriptors require `name`, `help`, and either an `exec` string or a
  Python `callable`; optional `tags` and `examples` appear in Typer help.
- Task templates require `id`, `name`, `description`, and `prompt`, with
  optional `variables` metadata describing substitutions.
- Package metadata under `plugins` can declare MCP descriptors and optional
  plug-in scoped CLI commands via `cli.commands`.

## GUI coupling

- The Tauri cockpit mirrors the CLI: every button routes through the
  `scripts.tino_cli` bridge, appending `--confirm` when the GUI confirmation
  toggle is enabled.
- `TINO_API_URL` controls the backend target for both the cockpit and CLI helpers
  such as `tino research`.
- Button mapping includes: **Plan** → `python -m scripts.tino_cli plan <goal>`;
  **Run** → `python -m scripts.tino_cli exec <goal>`; **Cockpit Up/Down** →
  `tino --confirm up/down`; **New Task** → `tino task run <task_name> [--json]`;
  **Inject Context** → `tino idea <payload>`; **Research Ingest** →
  `tino research ingest <topic> <source>`; **Wishlist Add** → `tino wishlist add <url>`;
  **Publish Docs** → `tino --confirm docs publish <target>`; **Cockpit Logs** →
  `python -m scripts.tino_cli cockpit-logs --limit <n>`.
- Dashboard panels surface backend context such as recent plans, LLM budget, and
  MCP plug-in toggles.

## Compliance

Changes to CLI commands, service endpoints, or plug-in registry contracts should
be validated against this document and the JSON schema before merging. When in
doubt, defer to the canonical descriptions in the [README](README.md).

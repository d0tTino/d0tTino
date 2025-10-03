# Desktop GUI

The Tauri cockpit mirrors the ``tino`` CLI: every button calls into
``scripts.tino_cli`` via the Rust bridge so both shells and the desktop
experience stay in sync. Use the GUI when you prefer buttons and toast
notifications but still want the safety rails provided by the refactored CLI.

## Usage

1. Start the API backend the cockpit talks to:
   ```bash
   uvicorn api:app --reload
   ```
   Override the default endpoint by setting ``TINO_API_URL`` before launching
   the GUI. The same environment variable is honoured by ``tino research`` and
   other CLI helpers.
2. Launch the desktop cockpit:
   ```bash
   cargo tauri dev
   ```
3. Type a prompt or drag a text file onto the window to load it automatically.
   Dropped files trigger the ``open-prompt-file`` bridge command, echoing the
   behaviour of ``tino plugins`` file helpers.

## Cockpit ↔ CLI mapping

The cockpit buttons are thin wrappers over canonical ``tino`` commands:

| Button | CLI bridge | Notes |
| --- | --- | --- |
| **Plan** | ``python -m scripts.tino_cli plan <goal>`` | Streams planner output; downstream ``tino task`` commands use the same plan log.
| **Run** | ``python -m scripts.tino_cli exec <goal>`` | Executes shell steps captured during planning. Logs land beside the CLI transcripts (`TINO_CLI_LOG`).
| **Recipes ▸ Run** | ``python -m scripts.tino_cli run-recipe <name> <goal>`` | Mirrors the Typer recipe helpers and records telemetry if enabled.
| **Cockpit ▸ Up** | ``tino --confirm up`` | Requires confirmation inside the GUI before issuing ``docker compose up -d``. Windows hosts use ``cmd /C`` while Bash shells use ``/bin/sh -c``; the bridge handles both.
| **Cockpit ▸ Down** | ``tino --confirm down`` | Stops the compose stack and is gated behind the confirmation toggle.
| **New Task** | ``tino task run <payload>`` | The dialog payload becomes the ``task`` argument.
| **Inject Context** | ``tino idea <payload>`` | Stores quick notes via the UME bridge.
| **Research Ingest** | ``tino research ingest <topic> <source>`` | The GUI accepts ``topic::source`` or a raw URL and forwards the parsed values to the CLI.
| **Wishlist Add** | ``tino wishlist add <url>`` | Adds entries to ``metadata/wishlist.json`` just like the CLI.
| **Publish Docs** | ``tino --confirm docs publish <target>`` | Requires the confirmation toggle. Defaults to ``TINO_DOC_TARGET`` when no target is provided.
| **Cockpit Logs** | ``python -m scripts.tino_cli cockpit-logs --limit <n>`` | Displays the audit trail produced when cockpit actions run.

Confirmation-sensitive buttons (Up, Down, Publish Docs) mirror the
``--confirm`` guard in the CLI. Toggle the GUI confirmation switch to append
``--confirm`` to the underlying call; without it the command aborts with a
permission error. The same confirmation state applies on Windows and Bash
thanks to the abstraction in ``scripts/tino_cli/actions.py``.

## Dashboard panels

The cockpit also surfaces additional context from the backend:

* **Recent Plans** – the last five planning requests are listed for quick reference.
* **Budget Meter** – remaining LLM budget is visualised with a progress bar and accompanying history.
* **Plug-in Toggles** – checkboxes enable or disable MCP tools, updating `~/.config/d0tTino/mcp.json`.

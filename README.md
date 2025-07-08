# d0tTino Configuration

This repository contains example dotfiles and configuration snippets for various tools.

Key directories:

- `dotfiles/` – shell and environment settings
- `powershell/` – PowerShell profile scripts
- `windows-terminal/` – starter Windows Terminal settings
- `tablet-config/` – full example configuration for a tablet, including Windows Terminal
- `starship.toml` – example Starship prompt configuration
- `vscode/` – VS Code user settings
- `llm/` – prompts and other LLM-related files. The optional `llm/llm_config.json` file stores preferred model names used by `llm.ai_router`. Set the `LLM_CONFIG_PATH` environment variable to override the location. Configure it with Claude model names when using the `superclaude` backend.
- `scripts/thm.py` – Terminal Harmony Manager for palette and profile sync (installs as `thm` when using `pip install -e .[cli]`)

## Quickstart

Install the required Python packages (including test utilities such as
`pytest` and `json5`). Optional dependencies enable additional backends.
Install `dspy` via `pip install dspy-ai` for DSPy wrappers.
Use `pip install lmql` or `pip install guidance` to enable the LMQL and
Guidance backends. Tests that rely on these packages will be skipped if
they are missing:

```bash
pip install -e .[cli] -r requirements.txt
```

Run `ruff` to lint the Python code:

```bash
ruff check .
```

Run `mypy` to verify type hints:

```bash
mypy --install-types --non-interactive
```

The installation also provides an `ai` command for routing prompts to your chosen
model:

```bash
# Send the prompt to the remote provider
ai "Write a Python script"

# Force evaluation with your local model
ai --local "Translate text"

# Generate a step-by-step plan
ai-plan "Refactor the codebase"

# Execute the plan interactively
ai-do "Refactor the codebase"

# Or use the consolidated interface
ai-cli send "Hello"
ai-cli plan "Refactor the codebase"
ai-cli do "Refactor the codebase"

Legacy commands `ai`, `ai-plan`, and `ai-do` now invoke these subcommands
behind the scenes.

```
Set `LLM_ROUTING_MODE` to `remote` or `local` to override the automatic
selection logic, or adjust `LLM_COMPLEXITY_THRESHOLD` to change when the prompt
is considered complex.

`ai-do` exits with the code of the first failing command, making it suitable for
automation scripts.

Next, install the Git hooks so `pre-commit` runs automatically:

```bash
./install.sh
# or on Windows
./bootstrap.ps1
```

`install.sh` sets up the hooks for you. It detects your platform and calls
`scripts/setup-hooks.ps1` on Windows or `scripts/setup-hooks.sh` elsewhere so
`pre-commit` runs on each commit.

You can then run the test suite to verify the configuration:

```bash
pytest
```

Finally, run the smoke test to verify the basic commands:

```bash
npm run smoke
```


See the [installation guide](docs/installation.md) for setup instructions.
After cloning the repository, run `./install.sh` (or `./bootstrap.ps1` from an
elevated PowerShell window). Running it with elevation allows
`scripts/fix-path.ps1` to modify your user PATH and enables the local Git
hooks automatically. On Windows the script calls `scripts/setup-hooks.ps1`
while on other platforms it invokes `scripts/setup-hooks.sh`.
To enable and set up WSL in one step, pass `--install-wsl --setup-wsl` to
`install.sh` or `-InstallWSL -SetupWSL` with `bootstrap.ps1`; see the
[installation guide](docs/installation.md#WSL) for more details.

After running the script, reload your profile with `. $PROFILE` or restart the terminal to pick up the new configuration. The profile defines an `ai` helper that forwards prompts to `python -m ai_router`.

For a more detailed overview, see [docs/terminal.md](docs/terminal.md).
For THM usage instructions, see [docs/thm.md](docs/thm.md). The tool ships with
`blacklight`, `dracula` and `solarized-dark` palettes and can update your
configuration via `thm apply <name>`.
For details on fastfetch, btm and Nushell/Starship setup, see the [Terminal Tools section](docs/terminal.md#terminal-tools-fastfetch-btm--nushellstarship).
For the **One Half Dark** and **Campbell** palettes and the `Alt+M` metrics pane binding used in the screenshots, see [Replicating the Screenshot Environment](docs/terminal.md#replicating-the-screenshot-environment). For a brief overview of the unified palette and pane shortcuts, check [Blacklight Palette & Shortcuts](docs/terminal.md#blacklight-palette--shortcuts).


Additional guides:

- [Desktop configuration](docs/desktop.md)
- [Media containers](docs/media.md)
- [Repository navigation](docs/navigation.md)
- [AI automation tooling](docs/ai-automation.md)
- [Dashboard overview](docs/dashboard.md)
- [UME Quickstart](docs/ume.md)
- [Backend plug-in guide](docs/plugins.md)

## Git hooks

Run `scripts/setup-hooks.sh` to enable the local hooks automatically
(equivalent to running `git config core.hooksPath .githooks`). `install.sh`
and `bootstrap.ps1` call the appropriate script for you (`scripts/setup-hooks.ps1`
on Windows and `scripts/setup-hooks.sh` elsewhere), so you usually don't need to
run it manually:

```bash
./scripts/setup-hooks.sh
```

Once enabled, the `pre-commit` hook first runs `winget upgrade --all` and then
automatically exports your current `winget` package list to
`winget-packages.json` whenever you commit on Windows. Be sure to commit the
updated file so your package list stays in sync. On Linux or WSL the export is
skipped unless `winget` is available.

If the hook is disabled, run the following commands manually to upgrade and
export your package list:

```powershell
winget upgrade --all
pwsh -File scripts/export-winget.ps1
```


## Testing

Before running the Python tests locally, install this repository in editable
mode first and then install the rest of the dependencies:

```bash
pip install -e .[cli]
pip install -r requirements.txt
# Optional: install `dspy` to run the complete suite
pip install dspy-ai
# Optional: enable the LMQL backend
pip install lmql
# Optional: enable the Guidance backend
pip install guidance
```

Then invoke `pytest`:

```bash
pytest
```

## Contributing

Run `ruff` and `mypy` before committing to ensure the code is lint and type
error free:

```bash
ruff check .
mypy --install-types --non-interactive
```

After fixing any errors, rerun the commands and verify they report zero issues.
The `pre-commit` hook runs the same checks automatically.

## Telemetry and Metrics

When invoked with the [`--analytics`](scripts/ai_do.py#L20-L24) flag, `ai-do`
sends a small JSON payload to the URL specified by `EVENTS_URL`. If
`EVENTS_TOKEN` is set, its value is included as both an `apikey` and
`Authorization: Bearer` header. These events record whether a command sequence
completed successfully and can be aggregated per user. Summing successful
executions for each developer over a calendar week yields the
“successful automated tasks per active developer per week” metric. This telemetry
helps track how effectively the automation tooling is being adopted and
highlights trends in task reliability.

## Privacy

`ai-do` and the `ai-cli` subcommands (`send`, `plan`, `do`) can send anonymous
completion events when invoked with `--analytics`. The data is posted to the URL
specified in the `EVENTS_URL` environment variable with optional authorization
via `EVENTS_TOKEN`. No information is sent unless the flag is provided.

Licensed under the [Apache 2.0](LICENSE) license.

## North Star Metric

The project tracks “successful automated tasks per active developer per week” as
its north star metric. Every time a command completes successfully with the
[--analytics](scripts/ai_do.py#L20-L24) flag enabled, an event is posted to
`EVENTS_URL` and counted toward the developer's weekly total. Aggregating these
numbers highlights adoption trends and guides future automation work.

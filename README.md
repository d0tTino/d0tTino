# d0tTino Configuration

This repository contains example dotfiles and configuration snippets for various tools.

Key directories:

- `dotfiles/` – shell and environment settings
- `powershell/` – PowerShell profile scripts
- `windows-terminal/` – starter Windows Terminal settings
- `tablet-config/` – full example configuration for a tablet, including Windows Terminal
- `starship.toml` – example Starship prompt configuration
- `vscode/` – VS Code user settings
- `llm/` – prompts and other LLM-related files. The optional `llm/llm_config.json` file stores preferred model names used by `llm.ai_router`. Set the `LLM_CONFIG_PATH` environment variable to override the location.
- `scripts/thm.py` – Terminal Harmony Manager for palette and profile sync (installs as `thm` when using `pip install -e .[cli]`)

## Quickstart

Install the required Python packages (including test utilities such as
`pytest` and `json5`). The optional `dspy` dependency (install via
`pip install dspy-ai`) enables the full test suite and is required for
`llm.LoggedFewShotWrapper`. Tests that rely on it will be skipped if the
package is missing:

```bash
pip install -e .[cli] -r requirements.txt
```

Run `ruff` to lint the Python code:

```bash
ruff check .
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

```
Set `LLM_ROUTING_MODE` to `remote` or `local` to override the automatic
selection logic, or adjust `LLM_COMPLEXITY_THRESHOLD` to change when the prompt
is considered complex.

`ai-do` exits with the code of the first failing command, making it suitable for
automation scripts.

Next, install the Git hooks so `pre-commit` runs automatically:

```powershell
./bootstrap.ps1
```

`bootstrap.ps1` sets up the hooks for you. It runs
`scripts/setup-hooks.ps1` on Windows and `scripts/setup-hooks.sh` on other
platforms so `pre-commit` runs on each commit.

You can then run the test suite to verify the configuration:

```bash
pytest
```

Finally, run the smoke test to verify the basic commands:

```bash
npm run smoke
```


See the [installation guide](docs/installation.md) for setup instructions.
After cloning the repository, run `./bootstrap.ps1` from an elevated
PowerShell window. Running it with elevation allows
`scripts/fix-path.ps1` to modify your user PATH and enables the local Git
hooks automatically. On Windows it invokes `scripts/setup-hooks.ps1` while on
other platforms it runs `scripts/setup-hooks.sh`.
To enable and set up WSL in one step, pass `-InstallWSL -SetupWSL` to
`bootstrap.ps1`; see the [installation guide](docs/installation.md#WSL) for
more details.

After running the script, reload your profile with `. $PROFILE` or restart the terminal to pick up the new configuration. The profile defines an `ai` helper that forwards prompts to `python -m ai_router`.

For a more detailed overview, see [docs/terminal.md](docs/terminal.md).
For THM usage instructions, see [docs/thm.md](docs/thm.md). The tool ships with
`blacklight`, `dracula` and `solarized-dark` palettes and can update your
configuration via `thm apply <name>`.
For details on fastfetch, btm and Nushell/Starship setup, see the [Terminal Tools section](docs/terminal.md#terminal-tools-fastfetch-btm--nushellstarship).
For the **One Half Dark** and **Campbell** palettes and the `Alt+M` metrics pane binding used in the screenshots, see [Replicating the Screenshot Environment](docs/terminal.md#replicating-the-screenshot-environment). For a brief overview of the unified palette and pane shortcuts, check [Blacklight Palette & Shortcuts](docs/terminal.md#blacklight-palette--shortcuts).


## Git hooks

Run `scripts/setup-hooks.sh` to enable the local hooks automatically
(equivalent to running `git config core.hooksPath .githooks`). `bootstrap.ps1`
invokes the appropriate script for you (`scripts/setup-hooks.ps1` on Windows and
`scripts/setup-hooks.sh` elsewhere), so you usually don't need to run it
manually:

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
```

Then invoke `pytest`:

```bash
pytest
```

## Contributing

Run `ruff` before committing to ensure the Python code is lint-free:

```bash
ruff check .
```

After fixing any lint errors, rerun the command and verify that it reports zero
issues. The `pre-commit` hook runs the same command automatically.

Licensed under the [Apache 2.0](LICENSE) license.

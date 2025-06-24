# d0tTino Configuration

This repository contains example dotfiles and configuration snippets for various tools.

Key directories:

- `dotfiles/` – shell and environment settings
- `powershell/` – PowerShell profile scripts
- `windows-terminal/` – starter Windows Terminal settings
- `tablet-config/` – full example configuration for a tablet, including Windows Terminal
- `starship.toml` – example Starship prompt configuration
- `vscode/` – VS Code user settings
- `llm/` – prompts and other LLM-related files

## Quickstart

Install the required Python packages (including test utilities such as
`pytest` and `json5`):

```bash
pip install -e . -r requirements.txt
```

Next, install the Git hooks so `pre-commit` runs automatically:

```bash
./scripts/setup-hooks.sh
```

You can then run the test suite to verify the configuration:

```bash
pytest
```

Finally, run the smoke test script to verify the basic commands:

```bash
pwsh -File scripts/smoke_test.ps1
```


See the [installation guide](docs/installation.md) for setup instructions.
After cloning the repository, run `./scripts/setup-hooks.sh` to enable the
local Git hooks.  Then execute `scripts/fix-path.ps1` from an elevated
PowerShell prompt to ensure your PATH is configured correctly.
For a more detailed overview, see [docs/terminal.md](docs/terminal.md).
For details on fastfetch, btm and Nushell/Starship setup, see the [Terminal Tools section](docs/terminal.md#terminal-tools-fastfetch-btm--nushellstarship).


## Git hooks

Run `scripts/setup-hooks.sh` to enable the local hooks automatically
(equivalent to running `git config core.hooksPath .githooks`):

```bash
./scripts/setup-hooks.sh
```

Once enabled, the `pre-commit` hook automatically exports your current
`winget` package list to `winget-packages.json` whenever you commit on
Windows. Be sure to commit the updated file so your package list stays
in sync. On Linux or WSL the export is skipped unless `winget` is
available.

## Testing

Before running the Python tests locally, install the required packages:

```bash
pip install -r requirements.txt
```

Then invoke `pytest`:

```bash
pytest
```

Licensed under the [Apache 2.0](LICENSE) license.

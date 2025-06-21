# d0tTino Configuration

This repository contains example dotfiles and configuration snippets for various tools.

Key directories:

- `dotfiles/` – shell and environment settings
- `powershell/` – PowerShell profile scripts
- `windows-terminal/` – starter Windows Terminal settings
- `tablet-config/` – full example configuration for a tablet, including Windows Terminal
- `starship.toml` – minimal Starship prompt configuration
- `vscode/` – VS Code user settings
- `llm/` – prompts and other LLM-related files

See the [installation guide](docs/installation.md) for setup instructions.
If your PATH isn't updating correctly on Windows, run
`scripts/fix-path.ps1` from an elevated PowerShell prompt.
For a more detailed overview, see [docs/terminal.md](docs/terminal.md).

## Git hooks

Run the following to enable the local hooks:

```bash
git config core.hooksPath .githooks
```

Once enabled, the `pre-commit` hook automatically exports your current
`winget` package list when commits run on Windows. On Linux or WSL the
export is skipped unless `winget` is available.

Licensed under the [Apache 2.0](LICENSE) license.

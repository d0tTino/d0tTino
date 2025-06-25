# Installation

Follow these steps to set up the configuration files on a new system.

## Node.js

The repository's lint script requires Node.js. You can install it with [nvm](https://github.com/nvm-sh/nvm):

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
nvm install --lts
```

Alternatively, download the official installer from [nodejs.org](https://nodejs.org).

## Python linting

Install the Python development tools including `ruff`:

```bash
pip install -e . -r requirements.txt
```

Run `ruff` to check the code style:

```bash
ruff check .
```

## Windows

1. Install packages using `winget`. You can either import the full package list
   or run the provided helper script for the essentials:
   ```powershell
   winget import winget-packages.json
   # Or install just the core tools
   ./scripts/setup-winget.ps1
   ```
2. Copy or symlink the files from this repository to your profile directory.
3. From an elevated PowerShell prompt, run `bootstrap.ps1` to set up your PATH.
   Pass `-InstallWinget` to install the core tools automatically. You can also
   add `-InstallWindowsTerminal` to copy the default Windows Terminal settings
   and `-InstallWSL` to enable WSL:
   ```powershell
   ./bootstrap.ps1 -InstallWinget -InstallWindowsTerminal -InstallWSL
   ```
   The script calls `scripts/fix-path.ps1` to clean up duplicate entries and ensure your `bin` directory is included.
   If `$Env:USERPROFILE` isn't defined (e.g. on Linux), it falls back to `$HOME`.
4. Restart the terminal to load the new settings.

## WSL

Before installing packages in Ubuntu, enable the required Windows features and
install WSL:

```powershell
./scripts/install-wsl.ps1
```

You can also pass `-InstallWSL` to `bootstrap.ps1` to run the same command.

Run the provided script from the repository root to install the basic tools on
a fresh Ubuntu/WSL instance. The script uses `apt-get` and may prompt for your
password. You can call it directly or pass `-SetupWSL` to `bootstrap.ps1`:

```bash
sudo bash scripts/setup-wsl.sh
```

```powershell
./bootstrap.ps1 -SetupWSL
```

## Linux / macOS

1. Clone the repository:
   ```bash
   git clone https://github.com/d0tTino/d0tTino.git
   ```
2. Use `stow` or your preferred method to symlink the dotfiles into place.
3. Run `bootstrap.ps1` to clean up your PATH:
   ```powershell
   ./bootstrap.ps1
   ```
4. Launch a new shell to pick up the configuration.

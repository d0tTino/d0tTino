# Installation

Follow these steps to set up the configuration files on a new system.

## Windows

1. Install packages using `winget`:
   ```powershell
   winget import winget-packages.json
   ```
2. Copy or symlink the files from this repository to your profile directory.
3. Restart the terminal to load the new settings.
4. After installing everything, or whenever you notice duplicate or missing entries in your PATH, run the following from an elevated PowerShell prompt:
   ```powershell
   scripts/fix-path.ps1
   ```
   The script cleans up duplicate entries and ensures your `bin` directory is included.
   If `$Env:USERPROFILE` isn't defined (e.g. on Linux), it falls back to `$HOME`.

## WSL

Run the provided script from the repository root to install the basic tools on
a fresh Ubuntu/WSL instance. The script uses `apt-get` and may prompt for your
password:

```bash
sudo bash scripts/setup-wsl.sh
```

## Linux / macOS

1. Clone the repository:
   ```bash
   git clone https://github.com/d0tTino/d0tTino.git
   ```
2. Use `stow` or your preferred method to symlink the dotfiles into place.
3. Launch a new shell to pick up the configuration.

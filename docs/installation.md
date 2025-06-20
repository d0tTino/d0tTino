# Installation

Follow these steps to set up the configuration files on a new system.

## Windows

1. Install packages using `winget`:
   ```powershell
   winget import winget-packages.json
   ```
2. Copy or symlink the files from this repository to your profile directory.
3. Restart the terminal to load the new settings.

## WSL

Run the provided script to install the basic tools on a fresh Ubuntu/WSL
instance:

```bash
bash scripts/setup-wsl.sh
```

## Linux / macOS

1. Clone the repository:
   ```bash
   git clone https://github.com/d0tTino/d0tTino.git
   ```
2. Use `stow` or your preferred method to symlink the dotfiles into place.
3. Launch a new shell to pick up the configuration.

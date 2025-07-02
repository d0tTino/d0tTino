# Installation

Follow these steps to set up the configuration files on a new system.

## Node.js

The repository's lint script (`npx eslint`) requires Node.js. You can install it with [nvm](https://github.com/nvm-sh/nvm):

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

If you want to try the Textual-based UI prototype, install the
optional dependency:

```bash
pip install textual
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
3. From an elevated PowerShell window, run `bootstrap.ps1` to set up your PATH.
   You must run the script from an **elevated** window so that
   `scripts/fix-path.ps1` can modify the user PATH.
   Pass `-InstallWinget` to install the core tools automatically. You can also
   add `-InstallWindowsTerminal` to copy the default Windows Terminal settings,
   `-InstallWSL` to enable WSL, and `-SetupWSL` to configure the Ubuntu instance:
   ```powershell
   ./bootstrap.ps1 -InstallWinget -InstallWindowsTerminal -InstallWSL -SetupWSL
   ```
   The script calls `scripts/fix-path.ps1` to clean up duplicate entries and ensure your `bin` directory is included.
   If `$Env:USERPROFILE` isn't defined (e.g. on Linux), it falls back to `$HOME`.
4. Restart the terminal or run `. $PROFILE` to reload the profile and load the new settings.

## WSL

Before installing packages in Ubuntu, enable the required Windows features and
install WSL:

```powershell
./scripts/install-wsl.ps1
```

You can also pass `-InstallWSL` to `bootstrap.ps1` to run the same command.

Run the provided script from the repository root to install the basic tools on
a fresh Ubuntu/WSL instance. The script uses `apt-get` and may prompt for your
password. Invoke it directly inside WSL or pass `-SetupWSL` to `bootstrap.ps1`
from Windows to run it via `wsl.exe`:

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

## Local LLM tools

Install the Gemini CLI and pull the default Ollama model:

```powershell
./scripts/install-llm-tools.ps1
```

## Docker environment

The repository includes helper scripts to build a Docker image and start an
interactive shell inside it. Ensure a `Dockerfile` exists in the project root
and run:

```bash
bash scripts/setup-docker.sh
```

Set a custom image name using `--image` or the `IMAGE_NAME` environment variable:

```bash
bash scripts/setup-docker.sh --image myimage
# or
IMAGE_NAME=myimage bash scripts/setup-docker.sh
```

On Windows you can call the PowerShell wrapper or use `bootstrap.ps1` with the
`-SetupDocker` switch:

```powershell
./scripts/setup-docker.ps1
# or specify an image name
./scripts/setup-docker.ps1 -ImageName myimage
# or
./bootstrap.ps1 -SetupDocker
# with image name forwarding
./bootstrap.ps1 -SetupDocker -DockerImageName myimage
```

## Ghostty terminal

[Ghostty](https://github.com/mitchellh/ghostty) is a GPU-accelerated terminal emulator. To try it out:

1. Install the Rust toolchain if you do not already have it:
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```
2. Use `cargo` to install Ghostty:
   ```bash
   cargo install ghostty
   ```
3. Create the configuration directory and a basic config file at `~/.config/ghostty/ghostty.toml`:
   ```toml
   use_ligatures = true
   window_title = "Ghostty"
   ```
4. Launch `ghostty` from your shell. The terminal picks up changes to the config file on restart.

## Nextcloud server

[Nextcloud](https://nextcloud.com/) provides private file sync and collaborative
editing. Launch it using the included helper script:

```bash
./scripts/run-nextcloud.sh
```

The compose file maps port `8082` to the container's port `80`. Visit
`http://localhost:8082` to finish the setup. Customize trusted domains with the
`NEXTCLOUD_TRUSTED_DOMAINS` environment variable if you expose it to the
network.

## Mattermost chat

Run an open-source team chat server using the Mattermost service defined in the
compose file:

```bash
./scripts/run-mattermost.sh
```

The initial configuration is stored under `./mattermost`. Edit `config.json` to
set the site URL and enable integrations. The server listens on port `8065` by
default.


## Hyper-V support

On Windows Pro editions you can enable Microsoft's virtualization stack:

```powershell
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
```

Create virtual machines via the **Quick Create** wizard or `New-VM` in PowerShell. Hyper-V is useful for testing scripts in clean environments.

## ETL automation with n8n

[n8n](https://n8n.io/) is a workflow automation tool suited for lightweight ETL tasks.

1. Start the container interactively on port `5678`:
   ```bash
   docker run -it --name n8n -p 5678:5678 n8nio/n8n
   ```
2. Navigate to `http://localhost:5678` and create your first workflow.
3. Mount a local directory to `/home/node/.n8n` to persist workflows between runs.
4. A simple test flow watches a folder and sends new files to Nextcloud using the built-in nodes.


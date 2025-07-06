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

[Ghostty](https://github.com/mitchellh/ghostty) is a GPU-accelerated terminal emulator. Use the helper script to install it and copy the default configuration:

```bash
./scripts/setup-ghostty.sh
# Alternatively install manually
cargo install ghostty
```

Configuration lives in `~/.config/ghostty/ghostty.toml`. A minimal example enables ligatures and sets the window title:

```toml
use_ligatures = true
window_title = "Ghostty"
```

Launch `ghostty` instead of your default terminal to try it out.


## Nextcloud server

[Nextcloud](https://nextcloud.com/) provides private file sync and collaborative
editing.

1. Start the container with the helper script:
   ```bash
   ./scripts/run-nextcloud.sh
   ```
2. Open <http://localhost:8082> to complete the installation wizard.
3. Data lives under `./nextcloud`. Set the `NEXTCLOUD_TRUSTED_DOMAINS`
   environment variable when exposing the service to the network.
4. Stop the container with `Ctrl+C` or run `docker compose down` from another
   shell.

## Mattermost chat

Run an open-source team chat server with Mattermost.

1. Launch the service using the helper script:
   ```bash
   ./scripts/run-mattermost.sh
   ```
2. Visit <http://localhost:8065> and create the admin account.
3. Configuration is stored under `./mattermost`. Edit `config.json` to set the
   site URL and enable integrations.
4. Stop the container with `Ctrl+C` or use `docker compose down`.

## RomM game library

RomM manages your local game collection.

1. Start the container:
   ```bash
   ./scripts/run-romm.sh
   ```
2. Open <http://localhost:8080> and create your user account.
3. Game data is stored under `./romm` in the repository.
4. To stop the service press `Ctrl+C` or run `docker compose down`.

## Browser streaming with Neko

Use Neko to stream a browser session.

1. Start the container:
   ```bash
   ./scripts/run-neko.sh
   ```
2. The script maps port `8081` to container port `8080`.
3. Open <http://localhost:8081> to connect.
4. Stop the service with `Ctrl+C` or `docker compose down`.


## Hyper-V support

On Windows Pro editions you can enable Microsoft's virtualization stack:

```powershell
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
```

Create virtual machines via the **Quick Create** wizard or `New-VM` in PowerShell. Use the provided helper script for a quick setup:

```powershell
./scripts/create-hyperv-vm.ps1 -Name TestVM
```

Specify an ISO download URL and optional Cloud-Init ISO for unattended
installation:

```powershell
./scripts/create-hyperv-vm.ps1 -Name DevVM -IsoUrl https://example.com/os.iso -CloudInit ./seed.iso
```

You can also provision a VM or WSL distribution using the Python helper. Pass
`--notify` to post a message via `ntfy` when provisioning completes:

```powershell
python scripts/provision_vm.py hyperv --name DevVM --iso-url https://example.com/os.iso --cloud-init ./seed.iso --notify
python scripts/provision_vm.py wsl --name DevDistro --rootfs ubuntu.tar --target C:\\VMs\\DevDistro --notify
```

Hyper-V is useful for testing scripts in clean environments.

## ETL automation with n8n

[n8n](https://n8n.io/) is a workflow automation tool suited for lightweight ETL tasks.

1. Start the container interactively on port `5678`:
   ```bash
   docker run -it --name n8n -p 5678:5678 n8nio/n8n
   ```
2. Navigate to `http://localhost:5678` and create your first workflow.
3. Mount a local directory to `/home/node/.n8n` to persist workflows between runs.
4. A simple test flow watches a folder and sends new files to Nextcloud using the built-in nodes.

## API service

The compose file includes a FastAPI backend used by the upcoming dashboard.

1. Start the API service:
   ```bash
   docker compose up api
   ```
2. The server listens on <http://localhost:8000>.
3. Stop the service with `Ctrl+C` or `docker compose down`.

## Enabling the dashboard

When the new dashboard implementation lands:

1. Ensure the API service is running as described above.
2. Start the Next.js client:
   ```bash
   cd dashboard
   npm install
   npm run dev
   ```
3. Browse to <http://localhost:3000> to open the dashboard.
4. See [the dashboard guide](dashboard.md) for development tips.


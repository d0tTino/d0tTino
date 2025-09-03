# Windows Development Recipes

The recipe plug-ins under `scripts/recipes/plugins/` provide reusable command
sequences for setting up a Windows development environment. Each recipe returns
a list of shell commands that can be executed on a Windows host. Many recipes
use [winget configuration](https://learn.microsoft.com/windows/package-manager/configuration/) files located in `scripts/recipes/config/` to install
packages in a declarative manner.

## wsl
- **Usage:** Installs WSL and sets version 2 as the default.
- **Config:** `scripts/recipes/config/wsl.yaml`
- **Prerequisites:** Requires Windows 10 or later with virtualization enabled.

## docker_desktop
- **Usage:** Installs Docker Desktop and configures WSL 2 as the container backend.
- **Config:** `scripts/recipes/config/docker_desktop.yaml`
- **Prerequisites:** Requires WSL 2 and a 64‑bit system.

## vscode
- **Usage:** Installs Visual Studio Code and recommended Python and Jupyter extensions.
- **Config:** `scripts/recipes/config/vscode.yaml`
- **Prerequisites:** None.

## gpu_drivers
- **Usage:** Installs NVIDIA display drivers and the CUDA toolkit.
- **Config:** `scripts/recipes/config/gpu_drivers.yaml`
- **Prerequisites:** NVIDIA GPU hardware.

## windows_terminal
- **Usage:** Installs Windows Terminal from the Microsoft Store using `winget`.
- **Config:** `scripts/recipes/config/windows_terminal.yaml`
- **Prerequisites:** None.

## powershell
- **Usage:** Installs the latest PowerShell.
- **Config:** `scripts/recipes/config/powershell.yaml`
- **Prerequisites:** None.

## nodejs
- **Usage:** Installs the LTS version of Node.js.
- **Config:** `scripts/recipes/config/nodejs.yaml`
- **Prerequisites:** None.

## git
- **Usage:** Installs Git for Windows.
- **Config:** `scripts/recipes/config/git.yaml`
- **Prerequisites:** None.

## starship
- **Usage:** Installs the Starship prompt.
- **Config:** `scripts/recipes/config/starship.yaml`
- **Prerequisites:** None.

## fastfetch
- **Usage:** Installs Fastfetch for quick system information.
- **Config:** `scripts/recipes/config/fastfetch.yaml`
- **Prerequisites:** None.

# Windows Development Recipes

The recipe plug-ins under `scripts/recipes/plugins/` provide reusable command
sequences for setting up a Windows development environment. Each recipe returns
a list of shell commands that can be executed on a Windows host.

## wsl
- **Usage:** Enables required optional features, installs WSL, and sets version 2 as the default.
- **Prerequisites:** Requires Windows 10 or later with virtualization enabled.

## docker_desktop
- **Usage:** Installs Docker Desktop and configures WSL 2 as the container backend.
- **Prerequisites:** Requires WSL 2 and a 64‑bit system.

## vscode
- **Usage:** Installs Visual Studio Code and recommended Python and Jupyter extensions.
- **Prerequisites:** None.

## gpu_drivers
- **Usage:** Installs NVIDIA display drivers and the CUDA toolkit.
- **Prerequisites:** NVIDIA GPU hardware.

## windows_terminal
- **Usage:** Installs Windows Terminal from the Microsoft Store using `winget`.
- **Prerequisites:** None.

## powershell
- **Usage:** Installs the latest PowerShell.
- **Prerequisites:** None.

## nodejs
- **Usage:** Installs the LTS version of Node.js.
- **Prerequisites:** None.

## git
- **Usage:** Installs Git for Windows.
- **Prerequisites:** None.

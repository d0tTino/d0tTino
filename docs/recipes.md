# Windows Development Recipes

The recipe plug-ins under `scripts/recipes/plugins/` provide reusable command
sequences for setting up a Windows development environment. Each recipe returns
a list of shell commands that can be executed on a Windows host.

## wsl
- **Usage:** Enables and installs the Windows Subsystem for Linux.
- **Prerequisites:** Requires Windows 10 or later with virtualization enabled.

## docker_desktop
- **Usage:** Installs Docker Desktop via `winget`.
- **Prerequisites:** Requires WSL 2 and a 64‑bit system.

## vscode
- **Usage:** Installs Visual Studio Code using `winget`.
- **Prerequisites:** None.

## gpu_drivers
- **Usage:** Installs NVIDIA GPU drivers through `winget`.
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

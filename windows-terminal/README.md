This folder contains a minimal starter `settings.json` for Windows Terminal.
Common profile defaults now live in `common-profiles.json` and are merged into
the final configuration using `generate_settings.py`. If you want a complete
example configuration, see
[`../tablet-config/windows-terminal/settings.json`](../tablet-config/windows-terminal/settings.json).

To install these settings automatically, run
`scripts/install-windows-terminal.ps1` from the repository root. The script
creates `%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState`
if needed and copies `settings.json` there.

The settings define `Alt+V` to split the active pane vertically and `Alt+H` to
split it horizontally.

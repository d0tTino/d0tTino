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
split it horizontally. Press `Alt+M` to launch
[btm](https://github.com/ClementTsang/bottom) in a new tab.

## Acrylic behavior in generated overrides

`dotfiles/terminal/.config/tino/renderers/windows-terminal.sh` now emits
deterministic acrylic settings in `profiles.defaults`:

- If `TINO_TERMINAL_OPACITY` is below `1.0` **and** terminal effects are
  enabled, generated overrides set `"useAcrylic": true` and preserve the
  requested `acrylicOpacity`.
- If opacity is `1.0` (or effects are disabled), generated overrides keep an
  opaque background by setting `"useAcrylic": false` and `"acrylicOpacity": 1.0`.
- For hosts where acrylic is unsupported, set
  `TINO_WINDOWS_TERMINAL_ACRYLIC_SUPPORTED=false` to force the same opaque
  fallback (`useAcrylic=false`, `acrylicOpacity=1.0`).

### Expected Windows support

Acrylic requires a recent Windows build and a Windows Terminal version that
supports profile-level acrylic settings (Windows 10 1903+ / Windows 11 with
modern Windows Terminal releases). On older or restricted environments, use the
fallback toggle above to avoid inconsistent rendering behavior.


This folder contains the canonical Windows Terminal configuration.
Common profile defaults live in `common-profiles.json` and are merged into the
committed `settings.json` using `generate_settings.py`.

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


## Rendering engine preference and schema fallback

The generated settings prefer the Windows Terminal automatic rendering engine
via `"rendering.graphicsAPI": "automatic"` in both `settings.base.json` and
`terminal-profile-overrides.json`.

When `generate_settings.py` merges overrides:

- If the base file uses the Windows Terminal profiles schema (or already
  contains `rendering.graphicsAPI`), the override is applied.
- If the base file appears to target a different/older schema, the merge script
  skips this key and prints a warning to stderr rather than emitting a possibly
  invalid setting.

This keeps generated output compatible across schema and version mismatches
while still preferring the automatic renderer when supported.

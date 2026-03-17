# Windows Terminal tablet snapshot / host override notes

`windows-terminal/` is the only canonical source for Windows Terminal
configuration.

This `tablet-config/windows-terminal/` directory is **not** a second authority;
it is reserved for tablet-specific notes, snapshots, or host override examples.

Canonical generation path:

- Base: `windows-terminal/settings.base.json`
- Generator: `windows-terminal/generate_settings.py`
- Generated output: `windows-terminal/settings.json`

If you need tablet-specific behavior, keep it as an explicit host override layer
that is applied after canonical generation, rather than duplicating canonical
JSON files here.

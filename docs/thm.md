# Terminal Harmony Manager (THM)

The Terminal Harmony Manager provides a unified interface to apply color palettes
and manage terminal profiles across tools like Starship and Windows Terminal.

```
usage: thm [-h] {apply,list-palettes} ...
```

- `apply <name>` – install the given palette into your configuration files.
- `list-palettes` – show all palettes available under the `palettes/` directory.

Running `apply` now updates both `starship.toml` and
`windows-terminal/settings.json` so the prompt and terminal share the same
colors. Palettes are defined under `palettes/` – besides the default
`blacklight` scheme, example palettes such as `dracula` and
`solarized-dark` are provided.

Set the `THM_REPO_ROOT` environment variable if you want to apply a palette to
a different repository location. Install the CLI with `pip install -e .[cli]`
so the `thm` command works properly.

# Terminal Harmony Manager (THM)

The Terminal Harmony Manager provides a unified interface to apply color palettes
and manage terminal profiles across tools like Starship and Windows Terminal.

```
usage: thm.py [-h] {apply,list-palettes} ...
```

- `apply <name>` – install the given palette into your configuration files.
- `list-palettes` – show all palettes available under the `palettes/` directory.

The current implementation prints which palette would be applied. Future
versions will update `starship.toml` and `windows-terminal/settings.json`.

# Desktop Configuration

Desktop-specific settings are modeled as a host overlay in `hosts/desktop`.
The current desktop flow matches the shared dotfiles architecture described in
`README.md`, the terminal operations reference, and the install/bootstrap
scripts.

## Architecture

The desktop setup is applied in two layers:

1. **Core dotfile packages** from `dotfiles/`
   - `shell`
   - `nvim`
   - `tmux`
   - `terminal`
2. **Host overlay** from `hosts/desktop`

This is the same package set used by `scripts/install_dotfiles.sh` when no
custom `--packages` list is provided, and the same overlay ordering used by
`scripts/bootstrap-dev-env.sh` when it passes `--host desktop`.

Configuration precedence is:

1. `dotfiles/terminal/.config/tino/terminal-defaults.sh`
2. `hosts/desktop/.config/tino/host-overrides.sh`
3. Explicit CLI provider overrides such as `--provider kitty`

Because the managed `dotfiles/shell/.zshrc` already loads both
`~/.config/tino/terminal-defaults.sh` and `~/.config/tino/host-overrides.sh`,
you do **not** need to manually source the host override file when you are using
this repository's managed shell profile.

## Recommended setup

### Option 1: Use the declarative bootstrap flow

From the repository root:

```bash
./scripts/bootstrap-dev-env.sh --host desktop
```

This is the primary workflow. It runs the dependency/bootstrap stages in order:

1. `scripts/install_common.sh` (internal dependency/setup stage)
2. `scripts/install_dotfiles.sh --host desktop`
3. `scripts/setup-nvim.sh`
4. `scripts/setup-terminal-provider.sh <resolved-provider>`
5. terminal renderer contract validation

Use `--provider <name>` if you want to override the canonical WezTerm provider selected from the base defaults plus the desktop overlay.

### Option 2: Apply the layers directly with Stow

If you only want the dotfiles/overlay layout without the full bootstrap flow,
apply the same package order manually:

```bash
# Core defaults first
stow --target="$HOME" --dir=dotfiles shell nvim tmux terminal

# Desktop host overlay second
stow --target="$HOME" --dir=hosts desktop
```

This mirrors the current `scripts/install_dotfiles.sh` behavior:
core packages first, then the host overlay.

## Expected behavior on desktop hosts

- Shared terminal defaults come from `~/.config/tino/terminal-defaults.sh`.
- Desktop-only overrides live in `~/.config/tino/host-overrides.sh`.
- When both files define the same variable, the desktop overlay wins.
- The desktop overlay inherits the canonical WezTerm provider; set `TINO_TERMINAL_PROVIDER` only when this host intentionally deviates, and CLI flags still take final precedence.
- Managed `.zshrc` loads the defaults first and the desktop overlay second, so
  shell startup sees the same precedence as the install/bootstrap scripts.

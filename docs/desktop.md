# Desktop Configuration

Desktop-specific overrides now live in host overlays under `hosts/desktop`.

## Usage

1. Clone the repository.
2. Apply the shared dotfile packages you need, for example:
   ```bash
   stow --target="$HOME" dotfiles/shell dotfiles/tmux
   ```
3. Apply the desktop host overlay:
   ```bash
   stow --target="$HOME" hosts/desktop
   ```
4. Source `~/.config/tino/host-overrides.sh` from your shell startup file if you use host environment variables.

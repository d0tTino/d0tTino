# Installation

Follow these steps to set up the dotfiles on a new machine.

1. **Clone as a bare repository** so your `$HOME` stays clean:

   ```bash
   git clone --bare https://github.com/d0tTino/d0tTino.git "$HOME/.dots"
   alias dot='git --git-dir=$HOME/.dots/ --work-tree=$HOME'
   ```

2. **Symlink configs using GNU Stow**:

   ```bash
   cd ~/d0tTino
   stow powertoys
   stow windows-terminal
   ```

   Stow cleanly manages symlinks, letting you enable or disable packages with `stow -D <name>`.


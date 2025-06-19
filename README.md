# d0tTino Dotfiles

Personal configuration files for shell, file navigation tools, desktop theming and automation scripts.

## Quickstart

Clone the repository as a bare repo and stow the desired packages:

```bash
git clone --bare https://github.com/d0tTino/d0tTino.git "$HOME/.dots"
alias dot='git --git-dir=$HOME/.dots/ --work-tree=$HOME'
cd ~/d0tTino
stow windows-terminal
stow powertoys
```

See [docs/installation](docs/installation.md) for full setup details.

## Documentation

- [Installation](docs/installation.md)
- [Terminal Setup](docs/terminal.md)
- [Navigation](docs/navigation.md)
- [Desktop Environment](docs/desktop.md)
- [AI Automation](docs/ai-automation.md)

## License

This project is licensed under the [MIT License](LICENSE).

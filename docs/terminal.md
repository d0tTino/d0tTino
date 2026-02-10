## About Me

I’m a one-person powerhouse in AI and simulation engineering—think of me as a code-fueled brain factory where creativity and rigor collide. I obsess over multi-agent systems, emergent behaviors, and getting the absolute most out of every CPU cycle. Outside the matrix, I’m equally fascinated by aerospace, hard sci-fi futurism (Isaac Arthur is my spirit animal), and a dash of digital art for good measure.

Whether it’s spinning up a new LLM pipeline at dawn or fine-tuning memory graphs past midnight, my toolbox is always humming.

---

## Core Interests & Skills

### 🔬 Artificial Intelligence & Simulation

* **Multi-Agent Ecosystems**: Designing digital societies where autonomous agents evolve, collaborate, and surprise you with unexpected cultural quirks.
* **Cognitive Architectures**: Building layers of memory, sentiment, and intent so agents actually remember, care, and make decisions that feel alive.
* **Resource-Efficient LLMs**: Mastery of quantization (QLoRA, bitsandbytes), adaptive code generation, and local LLM orchestration with Ollama.
* **Event-Driven Dataflows**: Architecting pipelines with NATS/JetStream and DSPy to turbocharge prompting, summarization, and retrieval.
* **Knowledge Graphs & RAG**: Seamless integration of ChromaDB, Memgraph (and friends) for semantic search, RAG, and emergent memory pruning.

### 🛠 Software Engineering

* **Language of Choice**: Python 3.10+ (typed to the hilt with Pydantic, MyPy, Ruff).
* **DevOps Savvy**: CI/CD via GitHub Actions, Docker orchestration, and automated testing (pytest, pytest-asyncio).
* **Modular Design**: Clean separation of concerns—from core simulation loops to API layers and optional frontends.

---

## Spotlight: Public Projects

### 🚀 Culture: An AI Genesis Engine

*A platform to witness digital societies take shape under your very eyes.*

* **Dynamic Agents**: Mood-driven personalities that shift roles—Innovator, Analyst, Diplomat—on the fly.
* **Hierarchical Memory**: Short-term L1 and long-term L2 summaries, memory-utility scoring, and vector search via ChromaDB + Sentence Transformers.
* **Intent-Based RAG**: DSPy-powered pipelines for context enrichment, decision-making, and emergent communication protocols.
* **Resource Economy**: Influence Points (IP) & Data Units (DU) fuel every action, ensuring scarcity and tradeoffs.
* **Current Status**: Actively evolving—every commit pushes the boundaries of what “digital culture” can mean.

### 🧬 GeneCoder: DNA Data Storage Playground

*A toolkit that turns bits into base-pairs and back again, with error-correction flair.*

* **CLI & Algorithms**: Robust encoding/decoding workflows, FEC support, and batch processing via Click.
* **Research-Grade FEC**: Experiment with Reed–Solomon, LDPC, and custom parity schemes.
* **Future GUI**: Dreaming of an animated double-helix interface that visualizes your bytes spinning into DNA.
* **Current Status**: Stable CLI, with unit tests covering core algorithms and an active roadmap for GUI prototyping.

### 🧠 UME: Universal Memory Engine

*Your go-to long-term memory bus for any AI ecosystem.*

* **Event-Sourced Core**: Append-only logs feeding Redis or Neo4j backends, with OpenAPI-driven FastAPI endpoints.
* **Privacy & Opt-In**: Built-in consent flows, data retention policies, and granular access controls.
* **Dashboard in the Works**: Plans for a sleek React/Tailwind UI to visualize memory graphs, query stats, and system health.
* **Current Status**: Production-ready API, with load benchmarks and growing test coverage.

---

## Backstage Pass: Private & Shelved Experiments

*(Because no résumé is complete without a few mysterious footnotes.)*

* **Autonomous NEET Bux Agents**: Early-stage experiments in AI microtask pipelines.
* **SocialInsightAI & Prism**: Discord-based sentiment maps that once tracked server dynamics—now on ice.
* **Browser-Based Puppetry**: A Node/React orchestration platform for headless Chromium fleets.

---

## Development Philosophy

1. **Push the Limits**

   * I thrive on “What if?”—what if agents could hallucinate art, or self-organize economies under scarcity?
2. **Open-Source Heart**

   * I build in the open, remixing the best of the community and giving back when I can.
3. **Complexity by Emergence**

   * Simple rules + iterative feedback = mind-blowing behaviors. That’s where the magic lives.

---

## Dotfiles & Configuration

This repository includes example setups for various tools:

- `dotfiles/shell` – `.zshrc`, `.bashrc`, and `~/.config/starship.toml`.
- `dotfiles/nvim` – Neovim package (`~/.config/nvim/...`).
- `dotfiles/tmux` – `.tmux.conf`.
- `dotfiles/terminal/.config/tino/terminal-defaults.sh` – stowed into `~/.config/tino/terminal-defaults.sh` as the shared terminal defaults consumed by Ghostty setup.
- `dotfiles/terminal/.config/tino/ghostty.toml.tmpl` – stowed into `~/.config/tino/ghostty.toml.tmpl`; used as the canonical Ghostty template source by `scripts/setup-ghostty.sh`.
- `scripts/install_common.sh` – standard bootstrap entrypoint; installs `curl`, `unzip`, `git` everywhere, then on macOS/Linux installs dependencies (`zsh`, `starship`, `tmux`, `neovim`, `cargo`) and runs `scripts/setup-ghostty.sh` for Ghostty. Ghostty install precedence is: keep preinstalled binary if present, try native package manager (`brew`/`apt-get`/`dnf`/`pacman`) next, then fall back to `cargo install --locked ghostty`. It installs zsh plugins into `~/.local/share/zsh/plugins` but does not edit user rc files. On Windows it runs PowerShell setup and does not attempt Ghostty install.
- `scripts/install_dotfiles.sh` – deploys dotfiles that control shell runtime behavior; `dotfiles/shell/.zshrc` is the source of truth for plugin sourcing and Starship init.
- `scripts/migrate-shell-config.sh` – optional one-time manual migration for removing the legacy d0tTino marker block from `~/.zshrc` after writing a backup.
- `scripts/setup-wsl.sh` – WSL bootstrap helper; installs the same base stack and then runs `scripts/setup-ghostty.sh` so WSL follows the same managed Ghostty profile (Blacklight theme + Nerd Font defaults).
- `hosts/desktop` and `hosts/work_laptop` – host overlays for machine-specific tweaks.
- `windows-terminal` – minimal starter `settings.json` for Windows Terminal. The
  file is built from `common-profiles.json` using `generate_settings.py`.
- `tablet-config/windows-terminal` – full example configuration for a tablet.
- `vscode` – basic VS Code user settings.

### Linking on macOS/Linux

```bash
# inside your home directory
ln -s /path/to/repo/dotfiles/shell/.bashrc ~/.bashrc
ln -s /path/to/repo/vscode/settings.json ~/.config/Code/User/settings.json
ln -s /path/to/repo/dotfiles/shell/.config/starship.toml ~/.config/starship.toml
```

### Linking on Windows (PowerShell)

```powershell
New-Item -ItemType SymbolicLink -Path $Env:USERPROFILE\\.config\\starship.toml \
  -Target C:\\path\\to\\repo\\dotfiles\\shell\\.config\\starship.toml
New-Item -ItemType SymbolicLink -Path $Env:USERPROFILE\\AppData\\Local\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json \
  -Target C:\\path\\to\\repo\\windows-terminal\\settings.json
```

These examples assume the repository is cloned in a convenient location. Adjust the paths to match your setup.

## Standard bootstrap command

From the repository root run:

```bash
./scripts/install_common.sh
```

Platform behavior is explicit:

- **Linux/macOS/WSL**: installs shell/editor/multiplexer dependencies (`zsh`, `starship`, `tmux`, `neovim`, `cargo`), clones zsh plugins locally, and then installs/configures **Ghostty** via `scripts/setup-ghostty.sh` for a single canonical terminal path and shared theme behavior. Runtime shell setup comes from deployed dotfiles, not bootstrap-time rc edits.
- **Windows**: runs the PowerShell bootstrap path and optional Windows Terminal/WSL setup flags; native Ghostty install is intentionally skipped on Windows itself.

For Ghostty, `scripts/setup-ghostty.sh` first checks for an existing `ghostty` binary, then attempts native package manager installation on macOS/Linux (`brew`/`apt-get`/`dnf`/`pacman`), and only falls back to Cargo if needed. It renders the stowed template at `~/.config/tino/ghostty.toml.tmpl` (from `dotfiles/terminal/.config/tino/ghostty.toml.tmpl`) into generated runtime config `~/.config/ghostty/ghostty.toml`. Template values are driven by stowed terminal defaults from `~/.config/tino/terminal-defaults.sh` and optional host-specific overrides from `~/.config/tino/host-overrides.sh` using canonical `TINO_TERMINAL_OPACITY`, `TINO_TERMINAL_FPS`, and `TINO_TERMINAL_EFFECTS` variables.

Optional alternative: use Windows Terminal as your host terminal app while running Ghostty inside WSL for the managed Linux profile, or keep Windows Terminal-only settings for native PowerShell workflows.


Stow vs generated terminal files:

- Symlinked by `scripts/install_dotfiles.sh` package `terminal`:
  - `dotfiles/terminal/.config/tino/terminal-defaults.sh` -> `~/.config/tino/terminal-defaults.sh`
  - `dotfiles/terminal/.config/tino/ghostty.toml.tmpl` -> `~/.config/tino/ghostty.toml.tmpl`
- Generated by `scripts/setup-ghostty.sh`:
  - `~/.config/ghostty/ghostty.toml`

If you previously used older bootstrap behavior that injected a `d0tTino zsh plugins` marker block into `~/.zshrc`, run:

```bash
./scripts/migrate-shell-config.sh
```

The migration is intentionally manual and creates a timestamped backup before any changes.


## Neovim first run and startup profiling

The `dotfiles/nvim` package uses `lazy.nvim` for plugin management and bootstraps itself on first launch.
Minimum CLI toolchain for Neovim integrations: `rg` (ripgrep) and `fd` (or `fdfind` on Debian/Ubuntu).

1. Start Neovim normally (`nvim`).
2. Wait for `lazy.nvim` to clone and install plugins.
3. Run `:Lazy sync` if you want to force a full sync/update pass.

To inspect startup performance:

```bash
nvim --startuptime /tmp/nvim-startup.log +qa
```

Then open the log and review the slowest entries.

## Terminal Tools: fastfetch, btm & Nushell/Starship

## tmux baseline config and TPM plugins

The repository includes a baseline tmux configuration at [`dotfiles/tmux/.tmux.conf`](../dotfiles/tmux/.tmux.conf) with:

- Mouse mode enabled and larger scrollback history.
- Truecolor-capable terminal settings (`tmux-256color` + RGB terminal features).
- A status line styled to match the Blacklight palette.
- Ergonomic pane/window navigation and a `prefix + r` config reload binding.

TPM is bootstrapped automatically (cloned on first startup if missing) with:

- `tmux-plugins/tpm`
- `tmux-plugins/tmux-resurrect`
- `tmux-plugins/tmux-continuum`

Useful TPM shortcuts after launching tmux:

- `prefix + I` – install plugins.
- `prefix + U` – update plugins.
- `prefix + Alt + u` – remove plugins not currently listed.

### fastfetch
Display system information each time a shell starts.

Install on Debian/Ubuntu:
```bash
sudo apt install fastfetch
```
macOS via Homebrew:
```bash
brew install fastfetch
```
Add `fastfetch` to your shell's startup file or `~/.config/nushell/config.nu` if you use Nushell.

Example configuration:
```bash
# ~/.config/fastfetch/config.conf
ascii_logo = "ubuntu"
show_battery = true
```

### btm (bottom)
A terminal-based resource monitor.

Install with Cargo:
```bash
cargo install bottom --locked
```
Configuration file `~/.config/bottom/bottom.toml`:
```toml
update_rate = 1000
mem_as_value = true
```

### Nushell & Starship
Install Nushell and the Starship prompt for structured commands and a colorful prompt.

```bash
cargo install nu        # or brew install nushell
curl -sS https://starship.rs/install.sh | sh -s -- -y
```
Add to `~/.config/nushell/config.nu`:
```nu
$env.STARSHIP_CONFIG = '~/.config/starship.toml'
mkdir ~/.cache/starship
starship init nu | save --force ~/.cache/starship/init.nu
source ~/.cache/starship/init.nu
```
Customize the prompt by editing [`dotfiles/shell/.config/starship.toml`](../dotfiles/shell/.config/starship.toml) in this repository.

## Blacklight Palette & Shortcuts

The repository ships a unified **Blacklight** color scheme used by Windows Terminal and the Starship prompt. Run [`install-windows-terminal.ps1`](../scripts/install-windows-terminal.ps1) to copy `windows-terminal/settings.json` into the Windows Terminal *LocalState* folder. Then place [`dotfiles/shell/.config/starship.toml`](../dotfiles/shell/.config/starship.toml) in `~/.config/starship.toml` (or `%USERPROFILE%\.config\starship.toml` on Windows) so both tools share the same colors.

After applying the palette, Windows Terminal defines these shortcuts:

- `Alt+V` – split the current pane vertically.
- `Alt+H` – split the current pane horizontally.
- `Alt+M` – open a metrics pane running [`btm`](https://github.com/ClementTsang/bottom).

Use [`setup-screenshot-env.sh`](../scripts/setup-screenshot-env.sh) (or its PowerShell equivalent) to install the helper tools automatically.


## LLM Assets

The `llm` directory collects prompts and other files related to language models.
Place custom prompts under `llm/prompts/` and organize subfolders as needed.

## Textual UI Prototype

A lightweight interface using [Textual](https://textual.textualize.io/) lives
under `ui/textual_app.py`. Launch it with:

```bash
python -m ui.textual_app
```

Use **Send** to route prompts via `ai_router.send_prompt` and **Apply** to call
`thm.apply_palette`. Palette names are loaded from the `palettes/` directory and
responses or status messages show directly in the terminal window.
Press **Ctrl+P** to search available scripts and n8n flows via the LLM; a list of
matches appears and the chosen entry runs after confirming the plan. The
traditional command palette is available with **Ctrl+Shift+P**.
---

## Cloning & Managing Dotfiles

1. **Clone as a bare repository** so your `$HOME` stays clean:

   ```bash
   git clone --bare https://github.com/d0tTino/d0tTino.git "$HOME/.dots"
   alias dot='git --git-dir=$HOME/.dots/ --work-tree=$HOME'
   ```

2. **Symlink configs using GNU Stow**:

   ```bash
   cd ~/d0tTino
   stow dotfiles/shell
   stow dotfiles/nvim
   stow dotfiles/tmux
   ./scripts/install_common.sh
   ```

   Stow cleanly manages symlinks, letting you enable or disable packages with `stow -D <name>`.

3. **Host-specific overrides** live under `hosts/<hostname>` and can be applied with:

   ```bash
   stow --target="$HOME" hosts/$(hostname)
   ```

   This keeps machine-specific settings separate while sharing a common core.

---

## Replicating the Screenshot Environment

The screenshots in this repository showcase a terminal running
[fastfetch](https://github.com/fastfetch-cli/fastfetch),
[bottom](https://github.com/ClementTsang/bottom) (the `btm` command),
[Nushell](https://www.nushell.sh/), and the [Zed editor](https://zed.dev/).
To set up a similar environment:

### Install the tools

Run the helper script from the repository root. On Windows use the PowerShell
version, while Linux and macOS users can run the shell script. The script
detects Debian/Ubuntu, Arch and macOS automatically:

```powershell
./scripts/setup-screenshot-env.ps1
```

```bash
./scripts/setup-screenshot-env.sh
```

#### Step-by-step

1. **Install Fastfetch and Bottom** using the script above. It also installs
   Nushell and the Zed editor.
2. **Link the Starship configuration** so the prompt uses this repository's
   theme:
   ```bash
   ln -sf $(pwd)/dotfiles/shell/.config/starship.toml ~/.config/starship.toml
   ```
   ```powershell
   New-Item -ItemType SymbolicLink -Path $Env:USERPROFILE\.config\starship.toml `
     -Target (Join-Path $PWD 'dotfiles/shell/.config/starship.toml')
   ```

### Example profile entries

Add the following to your PowerShell profile
`$PROFILE` so the tools launch automatically in a new session:

```powershell
fastfetch
btm
```

For Nushell, place similar commands in `~/.config/nushell/env.nu`:

```nu
fastfetch
btm
```

### Apply the theme

Copy the sample configs from this repository to match the palette shown in the
screenshot:

```bash
mkdir -p ~/.config/fastfetch ~/.config/bottom
cp dotfiles/fastfetch/config.conf ~/.config/fastfetch/
cp dotfiles/btm/config.toml ~/.config/bottom/bottom.toml
ln -sf $(pwd)/dotfiles/shell/.config/starship.toml ~/.config/starship.toml
```

Zed's preferences include several built-in color themes. Select the dark theme
that most closely matches the screenshot from **Settings → Appearance**.

### Color scheme installation & Starship setup

1. **Install the Windows Terminal settings** to apply the `One Half Dark` and
   `Campbell` palettes:
   ```powershell
   ./scripts/install-windows-terminal.ps1
   ```
   The script copies the preconfigured `settings.json` containing both palettes
   into the Windows Terminal LocalState folder.
2. **Link the Starship configuration** so the prompt matches the screenshot:
   ```bash
   ln -sf $(pwd)/dotfiles/shell/.config/starship.toml ~/.config/starship.toml
   ```
   Make sure `~/.config/nushell/config.nu` sets `\$env.STARSHIP_CONFIG` to this
   path so Starship loads the file automatically.

### Metrics pane binding

Add the following key binding to your Windows Terminal `settings.json` to toggle
a vertical metrics pane running `btm` with `Alt+M`:

```json
{
  "command": { "action": "splitPane", "split": "vertical", "commandline": "btm" },
  "keys": "alt+m"
}
```

Now pressing `Alt+M` opens bottom in a split so you can monitor system metrics
beside your shell.

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).

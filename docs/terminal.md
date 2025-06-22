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

- `dotfiles/common` – shell settings shared across machines.
- `dotfiles/desktop` – configs unique to a desktop environment.
- `dotfiles/work_laptop` – configs for a work laptop.
- `windows-terminal` – minimal starter `settings.json` for Windows Terminal.
- `tablet-config/windows-terminal` – full example configuration for a tablet.
- `starship.toml` – example Starship prompt configuration.
- `vscode` – basic VS Code user settings.

### Linking on macOS/Linux

```bash
# inside your home directory
ln -s /path/to/repo/dotfiles/common/.bashrc ~/.bashrc
ln -s /path/to/repo/vscode/settings.json ~/.config/Code/User/settings.json
ln -s /path/to/repo/starship.toml ~/.config/starship.toml
```

### Linking on Windows (PowerShell)

```powershell
New-Item -ItemType SymbolicLink -Path $Env:USERPROFILE\\.config\\starship.toml \
  -Target C:\\path\\to\\repo\\starship.toml
New-Item -ItemType SymbolicLink -Path $Env:USERPROFILE\\AppData\\Local\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState\\settings.json \
  -Target C:\\path\\to\\repo\\windows-terminal\\settings.json
```

These examples assume the repository is cloned in a convenient location. Adjust the paths to match your setup.


## LLM Assets

The `llm` directory collects prompts and other files related to language models.
Place custom prompts under `llm/prompts/` and organize subfolders as needed.
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
   stow shell
   stow vim
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

On Debian-based systems:

```bash
sudo apt install fastfetch btm nushell
wget https://zed.dev/api/releases/zed_latest_amd64.deb
sudo dpkg -i zed_latest_amd64.deb
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

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).

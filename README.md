# Hi, I’m Tino
[![winget](https://github.com/d0tTino/d0tTino/actions/workflows/winget.yml/badge.svg)](https://github.com/d0tTino/d0tTino/actions/workflows/winget.yml)

I build local‑first automation, agentic systems and tooling that’s easy to run on your own hardware. My work spans persistent memory engines, emergent AI sandboxes and practical task orchestration.

### What I’m building now

- **Shared memory bus** – an event‑sourced knowledge graph so agents share durable, queryable context without depending on the cloud.
- **Emergent AI worlds** – a sandbox where autonomous agents develop personalities, roles, memory and shared culture.
- **Task orchestrators** – frameworks for chaining research → plan → execution → verification with audit trails and plug‑in schedulers.
- **DNA data storage** – an educational toolkit that encodes and decodes files into simulated DNA sequences with CLI and GUI.

---

## Featured projects

### Culture — AI social sandbox  
A platform to develop and study autonomous AI agents and emergent behaviour.

- **Implemented:** modular agents using LangGraph; hierarchical memory persisted to Chroma; shared knowledge board; resource economy (influence points and data units); Discord output; DSPy integration and local Ollama workflows; metrics and observability.  
- **Planned:** richer visualisation and interactive Discord loop; advanced memory management and governance mechanics.  
- **Status:** Active – development happens on the `dev` branch.

### UME — Universal Memory Engine  
An event‑sourced memory bus that turns streams of events into a knowledge graph for agents and automations.

- **Implemented:** ingestion API with schema validation; privacy agent to redact PII; FastAPI/GraphQL service with RBAC; adapters for SQLite, Postgres, Redis, Neo4j and Arango; vector‑store interface; CLI for maintenance and graph replay; projection engine that consumes events and builds the graph.  
- **Planned:** production‑ready back‑end with high‑availability and a web dashboard.  
- **Status:** Active – the `dev` branch is ahead of `main`.

### TaskCascadence — practical task orchestration  
A Python framework for defining multi‑stage tasks with clear audit trails.

- **Implemented:** graph‑based pipelines with `intake → research → plan → run → verify` stages; plugin architecture; synchronous and async execution; Temporal.io integration; built‑in monitoring; CLI and REST API; scheduler and plugin watcher; metrics endpoint.  
- **Planned:** additional scheduler back‑ends and richer DAG tooling.  
- **Status:** Active – work happens on `main`.

### GeneCoder — simulated DNA data storage  
An educational toolkit exploring simple encoding and decoding of data as DNA sequences.

 - **Implemented:** CLI for encoding/decoding small data sets using base‑4 and GC‑balanced conversions; simple error correction (triple‑repeat, Hamming(7,4)); an early Flet GUI with basic analysis plots. Some advanced FEC (Reed‑Solomon, LDPC, Fountain) and AI‑assisted decoding exist as prototypes but may not be fully runnable.  
 - **Planned:** broaden error correction support (Reed‑Solomon, LDPC and others), add streaming for large files and improve simulation fidelity.  
 - **Status:** Prototype – experimental and may require manual setup.

### DeepThought‑ReThought — experimental EDA AI  
An event‑driven AI stack exploring extreme efficiency and modular architecture.

- **Implemented:** core event‑driven framework using NATS/JetStream; publishers and subscribers with structured event definitions; CLI for fine‑tuning small open‑source LLMs via PEFT (QLoRA) and VRAM estimation; packaging for separate `dtrt` and `dtrt‑finetune` commands; examples for memory services, reward manager and neuromorphic stubs.  
- **Planned:** complete hierarchical memory service combining vector and graph memories; reinforcement and reward loops; adaptive code generation and neuromorphic experiments.  
- **Status:** Prototype – active research on `dev`.

### tino‑storm — local‑first research wrapper  
An experimental wrapper around the open‑source STORM knowledge curation engine with local storage defaults.

- **Implemented:** command‑line interface and FastAPI service for research, outlining and drafting; ingestion watcher for dropping URLs/files into vaults; support for Discord, Twitter, Reddit and ArXiv scraping; pluggable search providers and Prometheus metrics.  
- **Status:** Experimental – the dev branch is under active iteration and features are still maturing.

---

## Other projects and tools

I maintain a collection of other repos that support my workflow:

 - **DeepThought (Discord bot)** – a legacy Discord bot that previously experimented with memory relevance scoring, LLM response caching, Redis optimisation and Prometheus metrics. It is no longer maintained and has been superseded by DeepThought‑ReThought.  
- **Constellation Agents** – a suite of micro‑agents (CalendarNLPAgent, ExplainabilityAgent, PlaidSyncAgent, FinRL Strategist) built on top of UME for scheduling events, explaining analyses and syncing financial transactions.  
- **Constellation Dashboard** – a Next.js dashboard that dynamically loads panels exposed by various services.  
- **Docs Hub and dotfiles** – centralised documentation and configuration for my environment and development tools.  
- **TBDSpaceRPG, finance‑engine and other prototypes** – early experiments and learning projects; these are either inactive or in very early stages.

For private and ongoing work (such as **Aiga** and other closed repos), I focus on local‑first automation, privacy‑preserving audit trails, encrypted vaults and home‑lab scheduling. Details are intentionally abstract to protect sensitive information.

---

# d0tTino Configuration

## Quickstart

Install with your preferred Windows package manager:

```powershell
winget install --id Tino.d0tTino -e
```

### The `tino` command-line interface

The consolidated Typer-based CLI entrypoint is ``tino``. Use
``tino --help`` to view the canonical subcommands that ship with the
refactored surface:

| Command | Description |
| --- | --- |
| ``tino init`` | Bootstrap local tooling via ``install.sh`` (requires ``--confirm`` to run installers). |
| ``tino doctor`` | Run environment checks and Git hook validation. |
| ``tino whoami`` | Print the current CLI state, including ``--dry-run`` and telemetry settings. |
| ``tino up`` / ``tino down`` | Manage the docker-compose stack, optionally targeting a single service. Both respect ``--confirm`` before mutating services. |
| ``tino logs`` | Stream docker-compose logs; use ``--confirm`` to acknowledge the interactive stream. |
| ``tino task run <task_name> [--json payload]`` | Execute TaskCascadence tasks; ``status`` and ``signal`` remain available (``signal`` always requires ``--confirm``). |
| ``tino task schedule list`` | Inspect the TaskCascadence schedule without mutating it (respects ``--dry-run`` for previews). |
| ``tino task schedule update --json '{...}'`` | Patch the schedule using a JSON payload; always refuses to run without ``--confirm``. |
| ``tino research …`` | Access tino-storm research helpers (``ingest``, ``draft``). |
| ``tino idea`` | Submit a quick idea/event to UME memory without opening the group commands. |
| ``tino mem …`` | Query UME memories with structured filters. |
| ``tino finance …`` | Snapshot or synchronise finance data; use ``snapshot --month YYYY-MM`` (or ``--period``) to target a window, and ``sync`` refuses to run without ``--confirm``. |
| ``tino wishlist …`` | Append or list wishlist items tracked in ``metadata/wishlist.json``. |
| ``tino docs publish`` | Publish generated documentation, honouring ``TINO_DOC_TARGET`` when the target is omitted. |
| ``tino plugins …`` | Run plug-in supplied commands that are loaded dynamically from ``plugin-registry.json``. |
| ``tino legacy ai`` | Shim for ``scripts/ai_cli.py`` for backwards compatibility. |

Global flags provide safety rails: ``--dry-run`` prints commands without
execution, and ``--confirm`` is required for actions that change remote or
stateful services. The CLI also honours new environment variables introduced
in the refactor, such as ``TINO_CLI_LOG`` (log destination for command
transcripts) and ``TINO_DOC_TARGET`` (default documentation publish target).

Signals now infer the type based on the provided payload. Use ``--link`` for
URL-based updates and ``--note`` for inline messages; the CLI chooses the
appropriate signal shape automatically. For example:

```shell
tino task signal my-task-id --link https://status.example.com/incident/123 --confirm
```

The above emits a ``link`` signal without needing ``--type link``. Swap in
``--note`` for free-form text updates when sharing progress notes or status
summaries.

#### Task schedule helpers

Schedule visibility now lives alongside other ``tino task`` helpers. ``tino task
schedule list`` shows the current automation windows without requiring
confirmation so you can diff changes in ``--dry-run`` mode. ``tino task schedule
update`` expects a JSON body that mirrors the TaskCascadence schedule schema
and refuses to run unless you supply both a valid ``--json`` payload and
``--confirm``. For example:

```shell
tino --confirm task schedule update --json '{"cron": "0 12 * * *", "task": "midday-report"}'
```

This pattern ensures you preview the structure of the new schedule before it is
persisted, and you can pipe JSON in from a file or ``jq`` when drafting more
complex updates.

Or use Scoop in a single line:

```powershell
scoop bucket add tino https://github.com/d0tTino/tino-bucket; scoop install tino
```

For advanced bootstrap options, see
[docs/installation.md](docs/installation.md).
Detailed Winget instructions are available in
[docs/install-winget.md](docs/install-winget.md).
Explore curated setup commands in
[docs/recipes.md](docs/recipes.md).

### Plug-in registry format

The plug-in registry (`plugin-registry.json`) now ships curated CLI commands and
task templates alongside package metadata. Each registry payload includes the
following top-level fields:

* `name` and `version` identify the bundle that was loaded.
* `commands` is an array of executable command descriptors containing a
  `name`, `help`, and shell `exec` string (with optional `tags` and `examples`).
  These entries surface under the `tino plugins` namespace. Each command can
  expose extra tags or examples that are rendered when running
  `tino plugins --help` or `tino plugins <plugin> --help`.
* `taskTemplates` provides reusable task scaffolds. Each template defines an
  `id`, human-readable `name`, `description`, `prompt`, and optional
  `variables` metadata that describes the available substitutions.
* `plugins`, `recipes`, and `recipe_configs` remain available for package
  management and continue to work with existing CLI workflows.

---


## Dotfiles layout

Dotfiles are organized into explicit stow-style packages under `dotfiles/` with optional host overlays in `hosts/`:

- `dotfiles/shell` → `.zshrc`, `.bashrc`, and `~/.config/starship.toml`
- `dotfiles/nvim` → `~/.config/nvim/...`
- `dotfiles/tmux` → `.tmux.conf`
- `dotfiles/terminal` → shared terminal defaults in `~/.config/tino/terminal-defaults.sh`
- `dotfiles/terminal/.config/wezterm/wezterm.lua` → optional GPU-accelerated WezTerm profile aligned with shell/tmux colors
- `dotfiles/terminal/.config/tino/ghostty.toml.tmpl` → authored Ghostty template (renderer input)
- `dotfiles/terminal/.config/tino/renderers/*.sh` → provider renderers that generate concrete config files from the terminal profile contract
- `scripts/install_common.sh` → standard bootstrap script; on macOS/Linux it installs dependencies (`zsh`, `starship`, `tmux`, `neovim`, `cargo`), runs `scripts/setup-nvim.sh` to provision Neovim plugin + Mason LSP assets (headless), runs `scripts/setup-ghostty.sh` to install Ghostty and trigger profile rendering, and then calls `scripts/install_dotfiles.sh` so managed rc files/symlinks are deployed to the target user home. Ghostty install precedence is: keep preinstalled binary if present, try native package manager (`brew`/`apt-get`/`dnf`/`pacman`) next, then fall back to `cargo install --locked ghostty`. It installs zsh plugins under `~/.local/share/zsh/plugins` and does not directly edit ad-hoc rc content (Windows skips Ghostty and keeps Windows Terminal flow).
- `scripts/setup-terminal-provider.sh <provider>` → entry point for provider-specific setup/rendering (`ghostty|wezterm|kitty|alacritty|windows-terminal`) via `~/.config/tino/terminal-profile.sh`
- `scripts/install_dotfiles.sh` → deploys managed dotfiles into the user target (for example `$HOME`) by writing tracked rc files/symlinks; `dotfiles/shell/.zshrc` is the source of truth for plugin sourcing and `starship init`.
- `scripts/migrate-shell-config.sh` → optional one-time manual migration that imports compatible legacy `~/.bashrc` exports/aliases/functions into runtime fragments at `~/.config/zsh/{env,aliases,functions}.zsh` (or `$XDG_CONFIG_HOME/zsh/...`) after creating a timestamped backup; it does not edit tracked repository dotfiles and is not required for bootstrap.
- `hosts/desktop` and `hosts/work_laptop` → machine-specific overrides
  - `hosts/desktop/.config/tino/host-overrides.sh` favors richer visuals/high refresh
  - `hosts/work_laptop/.config/tino/host-overrides.sh` keeps effects balanced for battery life

Example:

```bash
# Core defaults first (includes terminal defaults)
stow --target="$HOME" --dir=dotfiles shell nvim tmux terminal

# Host overlay second (desktop OR work_laptop)
stow --target="$HOME" --dir=hosts desktop
# stow --target="$HOME" --dir=hosts work_laptop
```

Expected behavior:

- `dotfiles/terminal` provides shared defaults in `~/.config/tino/terminal-defaults.sh`.
- Host overlay packages only contain diffs in `~/.config/tino/host-overrides.sh`.
- On shell startup, `.zshrc` loads defaults first and then host overrides, so host values win when both define the same variable.
- `scripts/install_dotfiles.sh --host <name>` follows the same order: core packages, then host overlay (`<name>` is `desktop` or `work_laptop` in this repo).

### What changes in `$HOME`

| Flow | Purpose | Writes/symlinks in user target (`$HOME`/XDG paths) |
| --- | --- | --- |
| `./scripts/install_common.sh` | Bootstrap dependencies + deploy managed dotfiles | Installs tools/assets (e.g. zsh plugins, Neovim/Ghostty assets) and invokes `scripts/install_dotfiles.sh` to create/update managed rc file symlinks. |
| `./scripts/install_dotfiles.sh [--host ...]` | Dotfile deployment only | Creates/updates tracked rc/config symlinks from `dotfiles/` (and optional `hosts/`) into the user target. |
| `./scripts/migrate-shell-config.sh [--force]` | Optional legacy import | Writes `~/.config/zsh/{env,aliases,functions}.zsh` fragments from legacy bash content + backup; does not manage tracked dotfile symlinks. |

### Terminal profile value flow

Terminal profile values flow through one path:

1. `~/.config/tino/terminal-defaults.sh` provides shared defaults.
2. `~/.config/tino/host-overrides.sh` applies host-specific overrides.
3. `~/.config/tino/terminal-profile.sh` loads both files and runs a renderer from `~/.config/tino/renderers/*.sh`.
4. The renderer writes provider output files (for Ghostty: `~/.config/ghostty/ghostty.toml`).

`~/.config/ghostty/ghostty.toml` is generated output and should not be treated as an authored source file.

Standard bootstrap command (repo root):

Neovim plugin revisions are pinned in `dotfiles/nvim/.config/nvim/lazy-lock.json`; provisioning is handled by `./scripts/setup-nvim.sh` (headless `Lazy! sync` + explicit Mason LSP installs, requires Neovim >= 0.8) so first interactive startup is deterministic. Runtime self-healing is opt-in with `TINO_NVIM_AUTO_BOOTSTRAP=1` (default is disabled/offline-friendly), and `TINO_NVIM_OFFLINE=1` forces warning-only startup behavior.


```bash
./scripts/install_common.sh
```

## Changelog (auto‑updated)

- **2025‑08‑09** — Refreshed featured projects; clarified implemented vs planned features; added privacy language; added auto‑update changelog; reclassified DeepThought as legacy and marked tino‑storm as experimental.
<!-- AGENT: Add new entries above this line. Keep the last 10. -->

---

# d0tTino Configuration

Refer to the docs for environment variables and other options.

I prefer local‑first defaults with optional cloud. You’ll find me under **Tino** or **T** across platforms.

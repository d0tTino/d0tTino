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
   # Windows examples
   stow windows-terminal
   stow powertoys
   ```

   Stow cleanly manages symlinks, letting you enable or disable packages with `stow -D <name>`.

   Example Windows configurations live under `windows-terminal/` and `powertoys/`. Use Stow to symlink these files into `%USERPROFILE%` when working on Windows.

3. **Host-specific overrides** live under `hosts/<hostname>` and can be applied with:

   ```bash
   stow --target="$HOME" hosts/$(hostname)
   ```

   This keeps machine-specific settings separate while sharing a common core.
   
---

## License

This project is licensed under the [MIT License](LICENSE).

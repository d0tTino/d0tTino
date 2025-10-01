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

The repository now exposes a consolidated Typer-based CLI entrypoint named
``tino``. It wraps workstation bootstrap automation, docker-compose stack
helpers, TaskCascadence orchestration, tino-storm research utilities, UME
memory helpers, finance synchronisation, wishlist tracking and docs
publishing. Legacy ``scripts/ai_cli.py`` commands remain available through
``tino legacy ai`` while emitting a deprecation warning to encourage the
transition.

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

---

## Changelog (auto‑updated)

- **2025‑08‑09** — Refreshed featured projects; clarified implemented vs planned features; added privacy language; added auto‑update changelog; reclassified DeepThought as legacy and marked tino‑storm as experimental.
<!-- AGENT: Add new entries above this line. Keep the last 10. -->

---

# d0tTino Configuration

Refer to the docs for environment variables and other options.

I prefer local‑first defaults with optional cloud. You’ll find me under **Tino** or **T** across platforms.

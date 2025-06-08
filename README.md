# About Me

Hello! I'm a solo software developer with a deep passion for Artificial 
Intelligence, aerospace, and game development. I thrive on exploring complex 
systems, emergent behavior, and pushing the boundaries of what's possible with 
code, particularly in resource-constrained environments. My work is driven by a 
fascination with hard sci-fi, futurism (I'm a fan of Isaac Arthur!), realistic 
space travel, history, politics, and science. I also have a creative side, 
enjoying digital art with tools like PaintToolSai. 🎨

I'm at home constantly learning and experimenting. 💡

You can find my work on GitHub under the handle 
[d0tTino](https://github.com/d0tTino).

---

## Core Interests & Skills

My interests lie at the intersection of AI, simulation, and interactive 
experiences.

* **Artificial Intelligence Development:**
    * **Focus Areas:** Multi-agent systems, emergent AI evolution, cognitive 
architectures, resource-efficient LLMs, Knowledge Graphs, and Event-Driven 
Architectures (EDA).
    * **Technologies:** Python, LangChain/LangGraph, DSPy, Ollama, 
NATS/JetStream, PyTorch, Hugging Face Ecosystem (Transformers, PEFT, TRL, 
Datasets, Accelerate), bitsandbytes, ChromaDB, Sentence Transformers, Pydantic, 
and open-source graph databases (e.g., Memgraph, ArangoDB, Neo4j).
    * **Techniques:** QLoRA, quantization, adaptive code generation 
(exploratory), and developing sophisticated memory systems for AI agents.

* **Game Development:**
    * **Passion:** Hard science fiction simulation games, focusing on realistic 
space travel, complex management systems, and narratives that span generations, 
allowing players to shape humanity's future.
    * **Experience:** While primarily using Python for AI and tooling, I apply 
game design principles and simulation logic across my projects. My dedication 
to this genre is evidenced by thousands of hours in titles like Factorio, 
Kerbal Space Program, Elite Dangerous, Rimworld, and Crusader Kings 3.

* **Software Engineering:**
    * **Primary Language:** Python.
    * **Approach:** Solo development of projects ranging from Discord bots and 
browser automation platforms to sophisticated AI frameworks.
    * **Practices:** Strong emphasis on modular design, version control 
(Git/GitHub), comprehensive testing (pytest, pytest-asyncio), and detailed 
documentation.

---

## Current Projects

### 🚩 Primary Focus: Culture: An AI Genesis Engine 🧬

* **Concept:** `Culture` is a cutting-edge simulation platform I'm developing 
to explore the fascinating emergence and evolution of AI societies. Think of it 
as a digital crucible where autonomous AI agents, powered by Large Language 
Models (LLMs), can develop distinct personalities, dynamically adopt roles, 
create complex communication patterns, exhibit creative capabilities, and form 
intricate social structures. 🤖💬🌍
* **Goals:** To serve as an advanced environment for AI development, keen 
observation, and the in-depth study of emergent intelligence and behavior. I'm 
particularly interested in how "culture" itself might arise from agent 
interactions and learning.
* **Key Features (Implemented & In Progress):**
    * 🧠 **Dynamic Agent States:** Agents possess evolving mood states that 
influence their behavior and have foundational attributes for personality 
development.
    * 🎭 **Dynamic Role Allocation:** Agents can take on roles like 
"Innovator," "Analyzer," or "Facilitator," with mechanisms to guide 
role-consistent behavior and allow for role changes.
    * 🗣️ **Intent-Based Actions & Communication:** Agents communicate and 
act based on structured "intents," laying the groundwork for more complex and 
potentially emergent communication protocols.
    * 💾 **Hierarchical Memory System:** A sophisticated, multi-layered 
memory architecture enabling agents to learn and recall effectively:
        * Utilizes **ChromaDB** for efficient vector-based semantic search and 
retrieval of memories, powered by **Sentence Transformers** for embeddings.
        * Generates **L1 Summaries** (session-level, short-term insights) and 
**L2 Summaries** (chapter-level, consolidated knowledge) using LLMs.
        * Features a **Memory Utility Score (MUS)** system for intelligent 
memory pruning, balancing factors like recency, frequency, and significance.
    * ❤️ **Sentiment Analysis:** Interactions are processed for sentiment, 
influencing agent moods and interpersonal relationship scores.
    * 🤝 **Agent Collaboration & Knowledge Sharing:** Agents can collaborate 
on defined "projects" and share information, ideas, and findings via a communal 
"Knowledge Board."
    * 📈 **Resource Economy:** Agents operate within an economy using 
"Influence Points" (IP) and "Data Units" (DU), earned and spent through various 
actions.
    * 🔄 **LangGraph-Powered Agent Architecture:** Core agent decision-making 
and turn logic are orchestrated using LangGraph for stateful, cyclical 
reasoning.
    * 🛠️ **DSPy Integration:** Leveraging the **DSPy** framework for 
optimized and structured prompting for tasks like summary generation, RAG 
context synthesis, and action selection. Compiled DSPy programs are used for 
efficiency.
    * ⚙️ **Customizable Simulation Engine:** The underlying simulation 
environment supports scenario definitions and manages agent interactions.
    * 💻 **Discord Integration:** A basic interface for observing the 
simulation, with plans for more interactive capabilities.
* **Tech Stack:** Python 3.10+, LangGraph, DSPy, Ollama (for local LLM 
experimentation), ChromaDB, Sentence Transformers, Pydantic, Pytest, and 
various other libraries from the Python AI/ML ecosystem.
* **Status:** Actively under development and my primary focus. Continuously 
iterating and adding new layers of complexity! 🚀

### 🚀 Ongoing R&D: DeepThought-ReThought
* **Concept:** An experimental AI project dedicated to exploring the frontiers 
of computational efficiency and capability, particularly under extreme resource 
constraints—a "zero-budget" AI philosophy.
* **Goals:** To develop highly optimized AI components by leveraging 
open-source tools, innovative architectural patterns (like EDA with 
NATS/JetStream), and aggressive optimization techniques. This project serves as 
a testbed for advanced concepts that can be integrated into other AI endeavors.
* **Current Work:** Fine-tuning smaller, open-source LLMs (e.g., 
Llama-3.2-3B-Instruct) using Parameter-Efficient Fine-Tuning (PEFT) techniques 
like QLoRA and post-training quantization. Also planning integration of 
Knowledge Graph memory.
* **Tech Stack:** Python, NATS/JetStream (nats-py), PyTorch, Hugging Face 
Ecosystem (Transformers, PEFT, TRL, Datasets, Accelerate), bitsandbytes.
* **Status:** Actively under development, currently focused on LLM fine-tuning.

### 🌌 On the Backburner: Untitled Sci-Fi Simulation Game
* **Concept:** An ambitious hard science fiction simulation game where players 
take on the role of a spacecraft captain. The gameplay revolves around managing 
a diverse crew, navigating the challenges of interplanetary travel, and making 
critical decisions that shape humanity's future across multiple generations in 
a dynamic space race.
* **Themes:** Realistic space travel mechanics, complex resource and crew 
management, deep simulation of societal and technological progression, and 
emergent narratives.
* **Status:** This passion project is currently on the backburner while 
"Culture: An AI Genesis Engine" is the primary development effort. However, it 
remains a significant long-term goal.

---

## Past Explorations (Currently Inactive)

I have a history of developing various AI-driven tools and platforms. While 
these projects are not currently under active development, they represent 
valuable experience and stepping stones:

* **SocialInsightAI (PulseCheck):** A social media sentiment analysis platform 
for Discord, Bluesky, and X, featuring data collection, PostgreSQL storage, 
Hugging Face-based sentiment analysis, and automated reporting/posting.
* **Prism (DeepThought - Relationship Tracker):** A Discord bot designed to 
track and visualize interactions and relationships between users using Redis 
and (optionally) Neo4j, incorporating sentiment analysis. (Shelved due to 
social considerations).
* **OWL-Agent (Orchestrated Workflow Liaison Agent):** An advanced automation 
system to bridge GitHub, Discord, and various AI models for streamlining 
software development tasks, including browser automation components.
* **DeepThought (Edgy Discord Bot):** An LLM-powered Discord bot with features 
like tone detection and customizable personality, built with a focus on 
engaging and unique interactions.
* **Puppetry:** An intelligent browser automation platform using Puppeteer 
(Node.js backend, React frontend) to orchestrate multiple headless Chromium 
instances with AI-driven agents, a visual workflow builder, and monitoring.

---

## Development Philosophy

* **Pushing Boundaries:** I'm driven to explore what's next, especially in 
creating more intelligent, autonomous, and emergent AI systems and deeply 
simulated game worlds.
* **Open Source Advocate:** I heavily utilize open-source technologies and 
believe in their power to democratize development.
* **Complex Systems & Emergence:** I am fascinated by how simple rules and 
interactions can lead to complex, unpredictable, and life-like behaviors.
* **Solo Developer, Tool-Assisted:** I typically work solo on my projects, 
leveraging modern development tools and coding assistants to enhance 
productivity and explore new ideas.
* **Lifelong Learner:** The Dev space is constantly evolving, and I am 
committed to continuous learning and adaptation.

---

Thank you for your interest!


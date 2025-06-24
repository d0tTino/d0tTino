# AI Automation

This document outlines how the repository manages tasks related to local AI workflows.

## Overview

- **Local LLM orchestration** – scripts under `llm/` control local models with minimal dependencies.
- **Task automation** – shell and PowerShell scripts handle linting, testing, and deployment.
- **Extensibility** – additional prompts and workflows can be added under `llm/prompts`.

## Installation

1. Ensure Python 3.10 or higher is installed.
2. Install the required Python packages:

   ```bash
   pip install -e . -r requirements.txt
   ```

Lint the codebase with `ruff`:

```bash
ruff check .
```

`dspy` powers the local LLM wrapper found in `llm/`, while `pytest` runs the test suite.

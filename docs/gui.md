# Desktop GUI

The Tauri application offers a minimal interface for sending prompts, reviewing planned tasks and running recipes.

## Usage

1. Start the backend with `uvicorn api:app --reload`.
2. Launch the desktop app with `cargo tauri dev`.
3. Type a prompt or drag a text file onto the window to load it automatically.
4. Click **Plan** to list the shell commands for your goal.
5. Hit **Run** to execute the steps or choose a recipe from the drop-down and run it.

Dropped files trigger the `prompt-file` event and populate the prompt field. The loaded file path is shown below the drop zone so you can confirm which prompt was imported.

The dashboard also surfaces additional context from the backend:

* **Recent Plans** – the last five planning requests are listed for quick reference.
* **Budget Meter** – remaining LLM budget is visualised with a progress bar and accompanying history.
* **Plug-in Toggles** – checkboxes enable or disable MCP tools, updating `~/.config/d0tTino/mcp.json`.

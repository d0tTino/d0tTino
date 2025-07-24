# Desktop GUI

The Tauri application offers a minimal interface for sending prompts, reviewing planned tasks and running recipes.

## Usage

1. Start the backend with `uvicorn api:app --reload`.
2. Launch the desktop app with `cargo tauri dev`.
3. Type a prompt or drag a text file onto the window to load it automatically.
4. Click **Plan** to list the shell commands for your goal.
5. Hit **Run** to execute the steps or choose a recipe from the drop-down and run it.

Dropped files trigger the `prompt-file` event and populate the prompt field. The loaded file path is shown below the drop zone so you can confirm which prompt was imported.

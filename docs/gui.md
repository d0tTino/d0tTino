# Desktop GUI

The Tauri application offers a minimal interface for sending prompts and running recipes.

## Usage

1. Start the backend with `uvicorn api:app --reload`.
2. Launch the desktop app with `cargo tauri dev`.
3. Type a prompt or drag a text file onto the window to load it automatically.
4. Choose a recipe from the list and execute it.

Dropped files trigger the `prompt-file` event and populate the prompt field.

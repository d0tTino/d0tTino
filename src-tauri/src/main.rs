#[cfg(feature = "gui")]
use std::fs;
#[cfg(feature = "gui")]
use tauri::{FileDropEvent, Manager, RunEvent, WindowEvent};

#[cfg(feature = "gui")]
#[tauri::command]
async fn plan(goal: String) -> Result<Vec<String>, String> {
    ume_tauri::commands::plan(goal).await
}

#[cfg(feature = "gui")]
#[tauri::command]
async fn exec(goal: String) -> Result<String, String> {
    ume_tauri::commands::exec(goal).await
}

#[cfg(feature = "gui")]
#[tauri::command]
async fn list_recipes() -> Result<Vec<String>, String> {
    ume_tauri::commands::list_recipes().await
}

#[cfg(feature = "gui")]
#[tauri::command]
async fn open_prompt_file(path: String) -> Result<String, String> {
    ume_tauri::commands::open_prompt_file(path).await
}

#[cfg(feature = "gui")]
fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            plan,
            exec,
            list_recipes,
            open_prompt_file,
        ])
        .build(tauri::generate_context!())
        .expect("error while running tauri application")
        .run(|app_handle, event| match event {
            RunEvent::WindowEvent { label, event, .. } => {
                if let WindowEvent::FileDrop(FileDropEvent::Dropped(paths)) = event {
                    if let Some(path) = paths.get(0) {
                        if let Ok(content) = fs::read_to_string(path) {
                            if let Some(window) = app_handle.get_window(&label) {
                                let _ = window.emit("prompt-file", content);
                            }
                        }
                    }
                }
            }
            _ => {}
        });
}

#[cfg(not(feature = "gui"))]
fn main() {}

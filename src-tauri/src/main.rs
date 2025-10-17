#[cfg(feature = "gui")]
use std::fs;
#[cfg(feature = "gui")]
use tauri::{FileDropEvent, Manager, RunEvent, WindowEvent};
#[cfg(feature = "gui")]
use ume_tauri::commands::{ActionDetails, CockpitLogs, Dashboard};

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
#[tauri::command]
async fn run_recipe(name: String, goal: String) -> Result<String, String> {
    ume_tauri::commands::run_recipe(name, goal).await
}

#[cfg(feature = "gui")]
#[tauri::command]
async fn dashboard() -> Result<Dashboard, String> {
    ume_tauri::commands::dashboard().await
}

#[cfg(feature = "gui")]
#[tauri::command]
async fn record_event(name: String, payload: serde_json::Value) -> Result<bool, String> {
    ume_tauri::commands::record_event(name, payload).await
}

#[cfg(feature = "gui")]
#[tauri::command]
async fn toggle_plugin(name: String, enable: bool) -> Result<bool, String> {
    ume_tauri::commands::toggle_plugin(name, enable).await
}

#[cfg(feature = "gui")]
#[tauri::command]
async fn cockpit_up() -> Result<ActionDetails, String> {
    ume_tauri::commands::cockpit_up().await
}

#[cfg(feature = "gui")]
#[tauri::command]
async fn cockpit_down(confirm: bool) -> Result<ActionDetails, String> {
    ume_tauri::commands::cockpit_down(confirm).await
}

#[cfg(feature = "gui")]
#[tauri::command]
async fn cockpit_new_task(task: String) -> Result<ActionDetails, String> {
    ume_tauri::commands::cockpit_new_task(task).await
}

#[cfg(feature = "gui")]
#[tauri::command]
#[allow(non_snake_case)]
async fn cockpit_inject_context(jobId: String, context: String) -> Result<ActionDetails, String> {
    ume_tauri::commands::cockpit_inject_context(jobId, context).await
}

#[cfg(feature = "gui")]
#[tauri::command]
async fn cockpit_research_ingest(path: String) -> Result<ActionDetails, String> {
    ume_tauri::commands::cockpit_research_ingest(path).await
}

#[cfg(feature = "gui")]
#[tauri::command]
async fn cockpit_wishlist_add(item: String) -> Result<ActionDetails, String> {
    ume_tauri::commands::cockpit_wishlist_add(item).await
}

#[cfg(feature = "gui")]
#[tauri::command]
async fn cockpit_publish_docs(confirm: bool) -> Result<ActionDetails, String> {
    ume_tauri::commands::cockpit_publish_docs(confirm).await
}

#[cfg(feature = "gui")]
#[tauri::command]
async fn cockpit_log_snapshot(limit: Option<usize>) -> Result<CockpitLogs, String> {
    ume_tauri::commands::cockpit_logs(limit).await
}

#[cfg(feature = "gui")]
fn main() {
    let _ = dotenvy::dotenv();
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            plan,
            exec,
            list_recipes,
            open_prompt_file,
            run_recipe,
            dashboard,
            record_event,
            toggle_plugin,
            cockpit_up,
            cockpit_down,
            cockpit_new_task,
            cockpit_inject_context,
            cockpit_research_ingest,
            cockpit_wishlist_add,
            cockpit_publish_docs,
            cockpit_log_snapshot,
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
                                let _ = window
                                    .emit("prompt-file-path", path.to_string_lossy().to_string());
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

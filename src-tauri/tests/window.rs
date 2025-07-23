#[cfg(feature = "gui")]
use tauri::Manager;

#[cfg(feature = "gui")]
#[tauri::test]
async fn main_window_title() {
    let context = tauri::generate_context!();
    let app = tauri::Builder::default()
        .build(context)
        .expect("failed to build app");
    let window = app.get_window("main").expect("missing main window");
    assert_eq!(window.title().unwrap(), "UME Dashboard");
}

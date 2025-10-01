use std::sync::Mutex;
use ume_tauri::commands::dashboard;

static TEST_MUTEX: Mutex<()> = Mutex::new(());

#[tokio::test]
async fn dashboard_returns_recent_plans_budget_and_plugins() {
    let _guard = TEST_MUTEX.lock().unwrap();
    use std::fs;
    let tmp = tempfile::TempDir::new().unwrap();
    let home = tmp.path();
    std::env::set_var("HOME", home);

    let cache = home.join(".cache/d0ttino");
    fs::create_dir_all(&cache).unwrap();
    fs::write(cache.join("plans.log"), "one\ntwo\n").unwrap();

    let config = home.join(".config/d0tTino");
    fs::create_dir_all(&config).unwrap();
    fs::write(
        config.join("mcp.json"),
        r#"{ "sample": { "server_url": "u", "capabilities": [] } }"#,
    )
    .unwrap();

    let budget_file = tmp.path().join("budget.json");
    fs::write(&budget_file, r#"{ "budget": 5, "history": [1,2,3] }"#).unwrap();
    std::env::set_var("LLM_BUDGET_PATH", &budget_file);

    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("..");
    std::env::set_var("PYTHONPATH", root);
    let dash = dashboard().await.expect("dashboard");
    assert_eq!(dash.budget, Some(5));
    assert_eq!(dash.budget_history, vec![1, 2, 3]);
    assert_eq!(
        dash.recent_plans,
        vec!["two".to_string(), "one".to_string()]
    );
    let sample = dash.plugins.iter().find(|p| p.name == "sample").unwrap();
    assert!(sample.enabled);
}

#[tokio::test]
async fn dashboard_handles_missing_budget_file() {
    let _guard = TEST_MUTEX.lock().unwrap();
    let tmp = tempfile::TempDir::new().unwrap();
    std::env::set_var("HOME", tmp.path());
    let budget_file = tmp.path().join("budget.json");
    std::env::set_var("LLM_BUDGET_PATH", &budget_file);
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("..");
    std::env::set_var("PYTHONPATH", root);

    let dash = dashboard().await.expect("dashboard");
    assert_eq!(dash.budget, None);
    assert!(dash.budget_history.is_empty());
}

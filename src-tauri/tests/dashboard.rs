use ume_tauri::commands::dashboard;

#[tokio::test]
async fn dashboard_returns_recent_plans_and_plugins() {
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

    std::env::set_var("LLM_ROUTER_BUDGET", "5");

    let dash = dashboard().await.expect("dashboard");
    assert_eq!(dash.budget, Some(5));
    assert_eq!(dash.recent_plans, vec!["two".to_string(), "one".to_string()]);
    let sample = dash.plugins.iter().find(|p| p.name == "sample").unwrap();
    assert!(sample.enabled);
}

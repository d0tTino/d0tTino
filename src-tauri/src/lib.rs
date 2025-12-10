pub mod commands {
    use serde::{Deserialize, Serialize};
    use serde_json::Value;
    use tino_cli_bridge::{
        self, CockpitLogs as BridgeLogs, CockpitResult as BridgeCockpitResult, DashboardEnvelope,
        ExecResult, PlanResult, RecipeList, RecipeRun, TelemetryInfo,
    };

    #[derive(Debug, Serialize, Deserialize, Clone)]
    pub struct PluginInfo {
        pub name: String,
        pub enabled: bool,
    }

    #[derive(Debug, Serialize, Deserialize, Clone)]
    pub struct Dashboard {
        pub recent_plans: Vec<String>,
        pub budget: Option<i64>,
        pub budget_history: Vec<i64>,
        pub plugins: Vec<PluginInfo>,
    }

    #[derive(Debug, Serialize, Deserialize, Clone)]
    pub struct TelemetryStatus {
        pub enabled: bool,
        pub endpoint: Option<String>,
    }

    #[derive(Debug, Serialize, Deserialize, Clone)]
    pub struct ActionDetails {
        pub message: String,
        pub telemetry: Option<TelemetryStatus>,
        pub details: Option<Value>,
    }

    #[derive(Debug, Serialize, Deserialize, Clone)]
    pub struct CockpitLogs {
        pub entries: Vec<CockpitLogEntry>,
        pub path: String,
    }

    #[derive(Debug, Serialize, Deserialize, Clone)]
    pub struct CockpitLogEntry {
        pub timestamp: f64,
        pub action: String,
        pub payload: Option<String>,
        pub exit_code: i32,
    }

    fn map_telemetry(info: Option<TelemetryInfo>) -> Option<TelemetryStatus> {
        info.map(|value| TelemetryStatus {
            enabled: value.enabled,
            endpoint: value.endpoint,
        })
    }

    fn map_action(result: BridgeCockpitResult) -> ActionDetails {
        ActionDetails {
            message: result.result.message,
            telemetry: map_telemetry(result.result.telemetry),
            details: result.result.details.map(Value::Object),
        }
    }

    fn map_logs(logs: BridgeLogs) -> CockpitLogs {
        CockpitLogs {
            entries: logs
                .entries
                .into_iter()
                .map(|entry| CockpitLogEntry {
                    timestamp: entry.timestamp,
                    action: entry.action,
                    payload: entry.payload,
                    exit_code: entry.exit_code,
                })
                .collect(),
            path: logs.path,
        }
    }

    fn convert_dashboard(envelope: DashboardEnvelope) -> Dashboard {
        Dashboard {
            recent_plans: envelope.dashboard.recent_plans,
            budget: envelope.dashboard.budget,
            budget_history: envelope.dashboard.budget_history,
            plugins: envelope
                .dashboard
                .plugins
                .into_iter()
                .map(|p| PluginInfo {
                    name: p.name,
                    enabled: p.enabled,
                })
                .collect(),
        }
    }

    pub async fn plan(goal: String) -> Result<Vec<String>, String> {
        let PlanResult { steps, .. } = tino_cli_bridge::plan(&goal)
            .await
            .map_err(|err| err.to_string())?;
        Ok(steps)
    }

    pub async fn exec(goal: String) -> Result<String, String> {
        let ExecResult { output, .. } = tino_cli_bridge::exec(&goal)
            .await
            .map_err(|err| err.to_string())?;
        Ok(output)
    }

    pub async fn list_recipes() -> Result<Vec<String>, String> {
        let RecipeList { recipes } = tino_cli_bridge::list_recipes()
            .await
            .map_err(|err| err.to_string())?;
        Ok(recipes)
    }

    pub async fn open_prompt_file(path: String) -> Result<String, String> {
        let prompt = tino_cli_bridge::open_prompt_file(&path)
            .await
            .map_err(|err| err.to_string())?;
        Ok(prompt.content)
    }

    pub async fn run_recipe(name: String, goal: String) -> Result<String, String> {
        let RecipeRun { log, .. } = tino_cli_bridge::run_recipe(&name, &goal)
            .await
            .map_err(|err| err.to_string())?;
        Ok(log)
    }

    pub async fn record_event(name: String, payload: Value) -> Result<bool, String> {
        let result = tino_cli_bridge::record_event(&name, &payload)
            .await
            .map_err(|err| err.to_string())?;
        Ok(result.success)
    }

    pub async fn toggle_plugin(name: String, enable: bool) -> Result<bool, String> {
        let result = tino_cli_bridge::toggle_plugin(&name, enable)
            .await
            .map_err(|err| err.to_string())?;
        Ok(result.success)
    }

    pub async fn dashboard() -> Result<Dashboard, String> {
        let envelope = tino_cli_bridge::dashboard()
            .await
            .map_err(|err| err.to_string())?;
        Ok(convert_dashboard(envelope))
    }

    pub async fn cockpit_up() -> Result<ActionDetails, String> {
        tino_cli_bridge::cockpit_action("cockpit-up", None, false, None)
            .await
            .map(map_action)
            .map_err(|err| err.to_string())
    }

    pub async fn cockpit_down(confirm: bool) -> Result<ActionDetails, String> {
        tino_cli_bridge::cockpit_action("cockpit-down", None, confirm, None)
            .await
            .map(map_action)
            .map_err(|err| err.to_string())
    }

    pub async fn cockpit_new_task(task: String) -> Result<ActionDetails, String> {
        tino_cli_bridge::cockpit_action("cockpit-new-task", Some(&task), false, None)
            .await
            .map(map_action)
            .map_err(|err| err.to_string())
    }

    pub async fn cockpit_inject_context(
        job_id: String,
        context: String,
    ) -> Result<ActionDetails, String> {
        tino_cli_bridge::cockpit_action(
            "cockpit-inject-context",
            Some(&context),
            false,
            Some(&job_id),
        )
        .await
        .map(map_action)
        .map_err(|err| err.to_string())
    }

    pub async fn cockpit_research_ingest(path: String) -> Result<ActionDetails, String> {
        tino_cli_bridge::cockpit_action("cockpit-research-ingest", Some(&path), false, None)
            .await
            .map(map_action)
            .map_err(|err| err.to_string())
    }

    pub async fn cockpit_wishlist_add(item: String) -> Result<ActionDetails, String> {
        tino_cli_bridge::cockpit_action("cockpit-wishlist-add", Some(&item), false, None)
            .await
            .map(map_action)
            .map_err(|err| err.to_string())
    }

    pub async fn cockpit_publish_docs(confirm: bool) -> Result<ActionDetails, String> {
        tino_cli_bridge::cockpit_action("cockpit-publish-docs", None, confirm, None)
            .await
            .map(map_action)
            .map_err(|err| err.to_string())
    }

    pub async fn cockpit_logs(limit: Option<usize>) -> Result<CockpitLogs, String> {
        tino_cli_bridge::cockpit_logs(limit)
            .await
            .map(map_logs)
            .map_err(|err| err.to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::commands;
    use serde_json::Value;
    use std::fs;
    use std::io::Write;
    use std::path::{Path, PathBuf};
    use std::sync::{Mutex, OnceLock};
    use tempfile::TempDir;

    static GUARD: OnceLock<Mutex<()>> = OnceLock::new();

    struct EnvGuard {
        pythonpath: Option<String>,
        record: Option<String>,
    }

    impl EnvGuard {
        fn install(stub_root: &Path, record_file: &Path) -> Self {
            let original = std::env::var("PYTHONPATH").ok();
            let record_original = std::env::var("TINO_BRIDGE_RECORD").ok();
            let separator = if cfg!(windows) { ";" } else { ":" };
            let stub_path = stub_root.to_string_lossy();
            let updated = match &original {
                Some(existing) if !existing.is_empty() => {
                    format!("{stub_path}{separator}{existing}")
                }
                _ => stub_path.into_owned(),
            };
            std::env::set_var("PYTHONPATH", &updated);
            std::env::set_var("TINO_BRIDGE_RECORD", record_file);
            Self {
                pythonpath: original,
                record: record_original,
            }
        }
    }

    impl Drop for EnvGuard {
        fn drop(&mut self) {
            match &self.pythonpath {
                Some(value) => std::env::set_var("PYTHONPATH", value),
                None => std::env::remove_var("PYTHONPATH"),
            }
            match &self.record {
                Some(value) => std::env::set_var("TINO_BRIDGE_RECORD", value),
                None => std::env::remove_var("TINO_BRIDGE_RECORD"),
            }
        }
    }

    fn guard<'a>() -> std::sync::MutexGuard<'a, ()> {
        GUARD.get_or_init(|| Mutex::new(())).lock().unwrap()
    }

    fn write_stub_cli() -> (TempDir, PathBuf) {
        let temp_dir = TempDir::new().expect("temp dir");
        let scripts_dir = temp_dir.path().join("scripts");
        fs::create_dir_all(scripts_dir.join("tino_cli")).expect("scripts/tino_cli");
        fs::write(scripts_dir.join("__init__.py"), "").expect("scripts __init__");
        fs::write(
            scripts_dir.join("tino_cli").join("__init__.py"),
            "from .__main__ import main\n",
        )
        .expect("cli __init__");
        let main_path = scripts_dir.join("tino_cli").join("__main__.py");
        let script = r#"import json
import os
import sys

SIMPLE = {
    "plan": {"status": "ok", "data": {"steps": ["step-one"], "telemetry": None}},
    "exec": {"status": "ok", "data": {"output": "done", "telemetry": None}},
    "record-event": {"status": "ok", "data": {"success": True}},
    "toggle-plugin": {"status": "ok", "data": {"success": True, "path": "/tmp/mcp.json"}},
    "cockpit-logs": {"status": "ok", "data": {"entries": [{"timestamp": 1.5, "action": "demo", "payload": "line", "exit_code": 0}], "path": "/tmp/log"}},
    "dashboard": {"status": "ok", "data": {"dashboard": {"recent_plans": ["alpha"], "budget": 10, "budget_history": [1, 2], "plugins": [{"name": "demo", "enabled": True}]}}},
}


def _cockpit_action(command: str, args: list[str]) -> dict:
    payload = ""
    confirm = False
    job_id = None
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--confirm":
            confirm = True
        elif arg == "--job-id":
            index += 1
            if index < len(args):
                job_id = args[index]
        elif not arg.startswith("--") and not payload:
            payload = arg
        index += 1
    return {
        "status": "ok",
        "data": {
            "result": {
                "message": f"{command}:{payload}",
                "telemetry": None,
                "details": {"confirm": confirm, "payload": payload, "job_id": job_id},
            }
        },
    }


def _run() -> int:
    args = sys.argv[1:]
    record = os.environ.get("TINO_BRIDGE_RECORD")
    if record:
        with open(record, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(args) + "\n")
    if not args:
        print(json.dumps({"status": "error", "error": "missing command"}))
        return 1
    command, *rest = args
    if command.startswith("cockpit-") and command != "cockpit-logs":
        payload = _cockpit_action(command, rest)
    elif command == "cockpit-logs" and rest and rest[0] == "--limit":
        try:
            limit = int(rest[1])
        except (IndexError, ValueError):
            limit = 200
        response = SIMPLE["cockpit-logs"].copy()
        response["data"] = {
            "entries": [
                {
                    "timestamp": float(limit),
                    "action": "demo",
                    "payload": "line",
                    "exit_code": 0,
                }
            ],
            "path": "/tmp/log",
        }
        payload = response
    else:
        payload = SIMPLE.get(command)
        if payload is None:
            payload = {"status": "error", "error": f"unsupported {command}"}
    print(json.dumps(payload))
    return 0 if payload.get("status") == "ok" else 1


def main() -> None:
    sys.exit(_run())


if __name__ == "__main__":
    main()
"#;
        fs::File::create(&main_path)
            .expect("create __main__")
            .write_all(script.as_bytes())
            .expect("write __main__");
        let record_path = temp_dir.path().join("bridge-record.jsonl");
        (temp_dir, record_path)
    }

    fn read_calls(record: &Path) -> Vec<Vec<String>> {
        if !record.exists() {
            return vec![];
        }
        fs::read_to_string(record)
            .expect("record")
            .lines()
            .filter_map(|line| serde_json::from_str::<Vec<String>>(line).ok())
            .collect()
    }

    #[tokio::test]
    async fn plan_invokes_stub_cli() {
        let _lock = guard();
        let (temp_dir, record_path) = write_stub_cli();
        let _env = EnvGuard::install(temp_dir.path(), &record_path);

        let steps = commands::plan("demo".into()).await.expect("plan result");
        assert_eq!(steps, vec!["step-one".to_string()]);

        let calls = read_calls(&record_path);
        assert!(calls
            .iter()
            .any(|call| call.get(0) == Some(&"plan".to_string())));
    }

    #[tokio::test]
    async fn cockpit_down_propagates_confirmation() {
        let _lock = guard();
        let (temp_dir, record_path) = write_stub_cli();
        let _env = EnvGuard::install(temp_dir.path(), &record_path);

        let result = commands::cockpit_down(true).await.expect("cockpit down");
        assert!(result.message.starts_with("cockpit-down"));
        let details = result.details.unwrap();
        assert_eq!(details.get("confirm"), Some(&Value::Bool(true)));

        let calls = read_calls(&record_path);
        assert!(calls
            .iter()
            .any(|call| call.get(0) == Some(&"cockpit-down".to_string())
                && call.iter().any(|arg| arg == "--confirm")));
    }

    #[tokio::test]
    async fn cockpit_new_task_returns_message() {
        let _lock = guard();
        let (temp_dir, record_path) = write_stub_cli();
        let _env = EnvGuard::install(temp_dir.path(), &record_path);

        let result = commands::cockpit_new_task("write tests".into())
            .await
            .expect("cockpit new task");
        assert!(result.message.contains("write tests"));
        let details = result.details.unwrap();
        assert_eq!(
            details.get("payload"),
            Some(&Value::String("write tests".into()))
        );

        let calls = read_calls(&record_path);
        assert!(calls
            .iter()
            .any(|call| call.get(0) == Some(&"cockpit-new-task".to_string())
                && call.iter().any(|arg| arg.contains("write tests"))));
    }

    #[tokio::test]
    async fn cockpit_inject_context_forwards_job_id() {
        let _lock = guard();
        let (temp_dir, record_path) = write_stub_cli();
        let _env = EnvGuard::install(temp_dir.path(), &record_path);

        let result = commands::cockpit_inject_context("job-42".into(), "context blob".into())
            .await
            .expect("cockpit inject context");
        assert!(result.message.contains("context blob"));
        let details = result.details.unwrap();
        assert_eq!(
            details.get("payload"),
            Some(&Value::String("context blob".into()))
        );
        assert_eq!(details.get("job_id"), Some(&Value::String("job-42".into())));

        let calls = read_calls(&record_path);
        assert!(calls.iter().any(|call| {
            call.len() >= 4
                && call[0] == "cockpit-inject-context"
                && call[1] == "context blob"
                && call[2] == "--job-id"
                && call[3] == "job-42"
        }));
    }

    #[tokio::test]
    async fn cockpit_logs_maps_entries() {
        let _lock = guard();
        let (temp_dir, record_path) = write_stub_cli();
        let _env = EnvGuard::install(temp_dir.path(), &record_path);

        let logs = commands::cockpit_logs(Some(7)).await.expect("cockpit logs");
        assert_eq!(logs.entries.len(), 1);
        assert_eq!(logs.entries[0].timestamp, 7.0);
        assert_eq!(logs.entries[0].action, "demo");

        let calls = read_calls(&record_path);
        assert!(calls.iter().any(|call| call
            == &[
                "cockpit-logs".to_string(),
                "--limit".to_string(),
                "7".to_string()
            ]));
    }

    #[tokio::test]
    async fn dashboard_converts_envelope() {
        let _lock = guard();
        let (temp_dir, record_path) = write_stub_cli();
        let _env = EnvGuard::install(temp_dir.path(), &record_path);

        let dashboard = commands::dashboard().await.expect("dashboard");
        assert_eq!(dashboard.recent_plans, vec!["alpha".to_string()]);
        assert_eq!(dashboard.budget, Some(10));
        assert_eq!(dashboard.plugins.len(), 1);
        assert_eq!(dashboard.plugins[0].name, "demo");
    }
}

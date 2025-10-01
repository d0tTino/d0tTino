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
        tino_cli_bridge::cockpit_action("cockpit-up", None, false)
            .await
            .map(map_action)
            .map_err(|err| err.to_string())
    }

    pub async fn cockpit_down(confirm: bool) -> Result<ActionDetails, String> {
        tino_cli_bridge::cockpit_action("cockpit-down", None, confirm)
            .await
            .map(map_action)
            .map_err(|err| err.to_string())
    }

    pub async fn cockpit_new_task(task: String) -> Result<ActionDetails, String> {
        tino_cli_bridge::cockpit_action("cockpit-new-task", Some(&task), false)
            .await
            .map(map_action)
            .map_err(|err| err.to_string())
    }

    pub async fn cockpit_inject_context(context: String) -> Result<ActionDetails, String> {
        tino_cli_bridge::cockpit_action("cockpit-inject-context", Some(&context), false)
            .await
            .map(map_action)
            .map_err(|err| err.to_string())
    }

    pub async fn cockpit_research_ingest(path: String) -> Result<ActionDetails, String> {
        tino_cli_bridge::cockpit_action("cockpit-research-ingest", Some(&path), false)
            .await
            .map(map_action)
            .map_err(|err| err.to_string())
    }

    pub async fn cockpit_wishlist_add(item: String) -> Result<ActionDetails, String> {
        tino_cli_bridge::cockpit_action("cockpit-wishlist-add", Some(&item), false)
            .await
            .map(map_action)
            .map_err(|err| err.to_string())
    }

    pub async fn cockpit_publish_docs(confirm: bool) -> Result<ActionDetails, String> {
        tino_cli_bridge::cockpit_action("cockpit-publish-docs", None, confirm)
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

use std::ffi::OsStr;
use std::path::PathBuf;

use serde::de::DeserializeOwned;
use serde::Deserialize;
use serde_json::Value;
use thiserror::Error;
use tokio::process::Command;

#[derive(Debug, Error)]
pub enum CliError {
    #[error("command failed: {0}")]
    CommandFailed(String),
    #[error("python invocation error: {0}")]
    Invocation(std::io::Error),
    #[error("invalid response: {0}")]
    InvalidResponse(String),
}

#[derive(Debug, Deserialize)]
struct Envelope<T> {
    status: String,
    data: Option<T>,
    error: Option<String>,
}

impl<T> Envelope<T> {
    fn into_result(self) -> Result<T, CliError> {
        match self.status.as_str() {
            "ok" => self
                .data
                .ok_or_else(|| CliError::InvalidResponse("missing data".into())),
            _ => Err(CliError::CommandFailed(
                self.error.unwrap_or_else(|| "unknown error".into()),
            )),
        }
    }
}

async fn invoke_raw<I, S>(args: I) -> Result<Vec<u8>, CliError>
where
    I: IntoIterator<Item = S>,
    S: AsRef<OsStr>,
{
    let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..");
    let python_path = repo_root.to_string_lossy().to_string();
    let python_exe = std::env::var("PYTHON").unwrap_or_else(|_| "python3".into());

    let mut command = Command::new(python_exe);
    let separator = if cfg!(windows) { ";" } else { ":" };

    command
        .arg("-m")
        .arg("scripts.tino_cli")
        .args(args)
        .env(
            "PYTHONPATH",
            std::env::var("PYTHONPATH")
                .map(|existing| format!("{existing}{separator}{python_path}"))
                .unwrap_or(python_path),
        )
        .stdin(std::process::Stdio::null());

    let output = command.output().await.map_err(CliError::Invocation)?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        return Err(CliError::CommandFailed(stderr.trim().to_string()));
    }

    Ok(output.stdout)
}

async fn call_command<T, I, S>(args: I) -> Result<T, CliError>
where
    T: DeserializeOwned,
    I: IntoIterator<Item = S>,
    S: AsRef<OsStr>,
{
    let stdout = invoke_raw(args).await?;
    serde_json::from_slice::<Envelope<T>>(&stdout)
        .map_err(|err| CliError::InvalidResponse(err.to_string()))?
        .into_result()
}

pub async fn plan(goal: &str) -> Result<PlanResult, CliError> {
    call_command(["plan", goal]).await
}

pub async fn exec(goal: &str) -> Result<ExecResult, CliError> {
    call_command(["exec", goal]).await
}

pub async fn list_recipes() -> Result<RecipeList, CliError> {
    call_command(["list-recipes"]).await
}

pub async fn open_prompt_file(path: &str) -> Result<PromptFile, CliError> {
    call_command(["open-prompt-file", path]).await
}

pub async fn run_recipe(name: &str, goal: &str) -> Result<RecipeRun, CliError> {
    call_command(["run-recipe", name, goal]).await
}

pub async fn record_event(name: &str, payload: &Value) -> Result<RecordEvent, CliError> {
    call_command([
        "record-event",
        name,
        &serde_json::to_string(payload).map_err(|e| CliError::InvalidResponse(e.to_string()))?,
    ])
    .await
}

pub async fn toggle_plugin(name: &str, enable: bool) -> Result<TogglePlugin, CliError> {
    let value = if enable { "true" } else { "false" };
    call_command(["toggle-plugin", name, value]).await
}

pub async fn dashboard() -> Result<DashboardEnvelope, CliError> {
    call_command(["dashboard"]).await
}

pub async fn cockpit_action(
    action: &str,
    payload: Option<&str>,
    confirm: bool,
) -> Result<CockpitResult, CliError> {
    let mut args: Vec<std::ffi::OsString> = vec![action.into()];
    if let Some(value) = payload {
        args.push(value.into());
    }
    if confirm {
        args.push("--confirm".into());
    }
    call_command(args.iter())
        .await
}

pub async fn cockpit_logs(limit: Option<usize>) -> Result<CockpitLogs, CliError> {
    let mut args: Vec<std::ffi::OsString> = vec!["cockpit-logs".into()];
    if let Some(limit) = limit {
        args.push("--limit".into());
        args.push(limit.to_string().into());
    }
    call_command(args.iter()).await
}

#[derive(Debug, Deserialize)]
pub struct PlanResult {
    pub steps: Vec<String>,
    pub telemetry: Option<TelemetryInfo>,
}

#[derive(Debug, Deserialize)]
pub struct ExecResult {
    pub output: String,
    pub telemetry: Option<TelemetryInfo>,
}

#[derive(Debug, Deserialize)]
pub struct RecipeList {
    pub recipes: Vec<String>,
}

#[derive(Debug, Deserialize)]
pub struct PromptFile {
    pub content: String,
}

#[derive(Debug, Deserialize)]
pub struct RecipeRun {
    pub log: String,
    pub exit_code: i32,
    pub log_path: String,
    pub telemetry: Option<TelemetryInfo>,
}

#[derive(Debug, Deserialize)]
pub struct RecordEvent {
    pub success: bool,
    pub enabled: bool,
}

#[derive(Debug, Deserialize)]
pub struct TogglePlugin {
    pub success: bool,
    pub path: String,
}

#[derive(Debug, Deserialize)]
pub struct DashboardEnvelope {
    pub dashboard: Dashboard,
}

#[derive(Debug, Deserialize)]
pub struct Dashboard {
    pub recent_plans: Vec<String>,
    pub budget: Option<i64>,
    pub budget_history: Vec<i64>,
    pub plugins: Vec<PluginInfo>,
}

#[derive(Debug, Deserialize)]
pub struct PluginInfo {
    pub name: String,
    pub enabled: bool,
}

#[derive(Debug, Deserialize)]
pub struct TelemetryInfo {
    pub enabled: bool,
    pub endpoint: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct CockpitResult {
    pub result: CockpitActionResult,
}

#[derive(Debug, Deserialize)]
pub struct CockpitActionResult {
    pub message: String,
    pub telemetry: Option<TelemetryInfo>,
    pub details: Option<serde_json::Map<String, Value>>,
}

#[derive(Debug, Deserialize)]
pub struct CockpitLogs {
    pub entries: Vec<CockpitLogEntry>,
    pub path: String,
}

#[derive(Debug, Deserialize)]
pub struct CockpitLogEntry {
    pub timestamp: f64,
    pub action: String,
    pub payload: Option<String>,
    pub exit_code: i32,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn parse_envelope_error() {
        let err = serde_json::from_str::<Envelope<serde_json::Value>>("{\"status\":\"error\"}")
            .unwrap()
            .into_result()
            .unwrap_err();
        assert!(matches!(err, CliError::CommandFailed(_)));
    }
}

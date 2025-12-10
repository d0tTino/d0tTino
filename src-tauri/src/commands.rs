#[cfg(feature = "gui")]
use serde::Serialize;
#[cfg(feature = "gui")]
use serde_json::Value;
#[cfg(feature = "gui")]
use std::path::PathBuf;
#[cfg(feature = "gui")]
use std::sync::Arc;
#[cfg(feature = "gui")]
use std::time::Duration;
#[cfg(feature = "gui")]
use tauri::async_runtime::Mutex;
#[cfg(feature = "gui")]
use tauri::AppHandle;
#[cfg(feature = "gui")]
use tokio::io::{AsyncBufReadExt, BufReader};
#[cfg(feature = "gui")]
use tokio::process::{Child, Command};

#[cfg(feature = "gui")]
#[derive(Clone)]
pub struct LogStreamer {
    child: Arc<Mutex<Option<Child>>>,
}

#[cfg(feature = "gui")]
impl Default for LogStreamer {
    fn default() -> Self {
        Self {
            child: Arc::new(Mutex::new(None)),
        }
    }
}

#[cfg(feature = "gui")]
#[derive(Debug, Serialize)]
pub struct CliOutput {
    pub stdout: String,
    pub stderr: String,
    pub status: i32,
    pub json: Option<Value>,
}

#[cfg(feature = "gui")]
#[derive(Debug, Serialize)]
pub struct LogLinePayload {
    pub line: String,
    pub stream: String,
}

#[cfg(feature = "gui")]
fn build_pythonpath(repo_root: &PathBuf) -> String {
    let separator = if cfg!(windows) { ";" } else { ":" };
    let root_path = repo_root.to_string_lossy().to_string();
    match std::env::var("PYTHONPATH") {
        Ok(existing) if !existing.is_empty() => format!("{root_path}{separator}{existing}"),
        _ => root_path,
    }
}

#[cfg(feature = "gui")]
async fn run_cli_command(
    args: Vec<String>,
    confirm: bool,
    dry_run: bool,
) -> Result<CliOutput, String> {
    let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..");
    let python = std::env::var("PYTHON").unwrap_or_else(|_| "python3".into());
    let mut full_args: Vec<String> = Vec::new();
    if confirm {
        full_args.push("--confirm".into());
    }
    if dry_run {
        full_args.push("--dry-run".into());
    }
    full_args.extend(args);

    let output = Command::new(python)
        .arg("-m")
        .arg("scripts.tino_cli")
        .args(&full_args)
        .env("PYTHONPATH", build_pythonpath(&repo_root))
        .current_dir(&repo_root)
        .output()
        .await
        .map_err(|err| err.to_string())?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    let json = serde_json::from_str::<Value>(&stdout).ok();
    Ok(CliOutput {
        stdout,
        stderr,
        status: output.status.code().unwrap_or(-1),
        json,
    })
}

#[cfg(feature = "gui")]
#[tauri::command]
pub async fn tino_start(
    service: Option<String>,
    confirm: bool,
    dry_run: bool,
) -> Result<CliOutput, String> {
    let mut args = vec!["up".to_string()];
    if let Some(name) = service {
        args.push(name);
    }
    run_cli_command(args, confirm, dry_run).await
}

#[cfg(feature = "gui")]
#[tauri::command]
pub async fn tino_stop(
    service: Option<String>,
    confirm: bool,
    dry_run: bool,
) -> Result<CliOutput, String> {
    let mut args = vec!["down".to_string()];
    if let Some(name) = service {
        args.push(name);
    }
    run_cli_command(args, confirm, dry_run).await
}

#[cfg(feature = "gui")]
#[tauri::command]
pub async fn tino_task_run(
    task: String,
    payload: Option<String>,
    confirm: bool,
    dry_run: bool,
) -> Result<CliOutput, String> {
    let mut args = vec!["task".into(), "run".into(), task];
    if let Some(body) = payload {
        args.push("--json".into());
        args.push(body);
    }
    run_cli_command(args, confirm, dry_run).await
}

#[cfg(feature = "gui")]
#[tauri::command]
pub async fn tino_task_signal(
    task_id: String,
    signal: Option<String>,
    link: Option<String>,
    note: Option<String>,
    confirm: bool,
    dry_run: bool,
) -> Result<CliOutput, String> {
    let mut args = vec!["task".into(), "signal".into(), task_id];
    if let Some(sig) = signal {
        args.push("--signal".into());
        args.push(sig);
    }
    if let Some(link) = link {
        args.push("--link".into());
        args.push(link);
    }
    if let Some(note) = note {
        args.push("--note".into());
        args.push(note);
    }
    run_cli_command(args, confirm, dry_run).await
}

#[cfg(feature = "gui")]
#[tauri::command]
pub async fn tino_research_ingest(
    source: String,
    topic: Option<String>,
    confirm: bool,
    dry_run: bool,
) -> Result<CliOutput, String> {
    let mut args = vec!["research".into(), "ingest".into(), source];
    if let Some(topic) = topic {
        args.push("--topic".into());
        args.push(topic);
    }
    run_cli_command(args, confirm, dry_run).await
}

#[cfg(feature = "gui")]
#[tauri::command]
pub async fn tino_research_draft(
    topic: Option<String>,
    hint: Option<String>,
    doc: Option<String>,
    anchor: Option<String>,
    prompt: Option<String>,
    confirm: bool,
    dry_run: bool,
) -> Result<CliOutput, String> {
    let mut args = vec!["research".into(), "draft".into()];
    if let Some(topic) = topic {
        args.push("--topic".into());
        args.push(topic);
    }
    if let Some(hint) = hint {
        args.push("--hint".into());
        args.push(hint);
    }
    if let Some(doc) = doc {
        args.push("--doc".into());
        args.push(doc);
    }
    if let Some(anchor) = anchor {
        args.push("--anchor".into());
        args.push(anchor);
    }
    if let Some(prompt) = prompt {
        args.push("--prompt".into());
        args.push(prompt);
    }
    run_cli_command(args, confirm, dry_run).await
}

#[cfg(feature = "gui")]
#[tauri::command]
pub async fn tino_wishlist_add(
    url: String,
    tags: Option<String>,
    confirm: bool,
    dry_run: bool,
) -> Result<CliOutput, String> {
    let mut args = vec!["wishlist".into(), "add".into(), url];
    if let Some(tags) = tags {
        for tag in tags.split(',').map(|v| v.trim()).filter(|v| !v.is_empty()) {
            args.push("--tag".into());
            args.push(tag.into());
        }
    }
    run_cli_command(args, confirm, dry_run).await
}

#[cfg(feature = "gui")]
#[tauri::command]
pub async fn tino_finance_snapshot(
    period: String,
    month: Option<String>,
    confirm: bool,
    dry_run: bool,
) -> Result<CliOutput, String> {
    let mut args = vec!["finance".into(), "snapshot".into(), period];
    if let Some(month) = month {
        args.push("--month".into());
        args.push(month);
    }
    run_cli_command(args, confirm, dry_run).await
}

#[cfg(feature = "gui")]
#[tauri::command]
pub async fn tino_docs_publish(
    target: Option<String>,
    site: Option<String>,
    version: Option<String>,
    confirm: bool,
    dry_run: bool,
) -> Result<CliOutput, String> {
    let mut args = vec!["docs".into(), "publish".into()];
    if let Some(target) = target {
        args.push(target);
    }
    if let Some(site) = site {
        args.push("--site".into());
        args.push(site);
    }
    if let Some(version) = version {
        args.push("--version".into());
        args.push(version);
    }
    run_cli_command(args, confirm, dry_run).await
}

#[cfg(feature = "gui")]
#[tauri::command]
pub async fn tino_whoami(confirm: bool, dry_run: bool) -> Result<CliOutput, String> {
    run_cli_command(vec!["whoami".into()], confirm, dry_run).await
}

#[cfg(feature = "gui")]
async fn read_stream(
    mut reader: tokio::io::Lines<BufReader<impl tokio::io::AsyncRead + Unpin>>,
    app: AppHandle,
    stream: &str,
) {
    let stream_label = stream.to_string();
    while let Ok(Some(line)) = reader.next_line().await {
        let _ = app.emit_all(
            "tino-log-line",
            LogLinePayload {
                line: line.clone(),
                stream: stream_label.clone(),
            },
        );
    }
}

#[cfg(feature = "gui")]
#[tauri::command]
pub async fn start_log_stream(
    app_handle: AppHandle,
    state: tauri::State<'_, LogStreamer>,
    service: String,
    confirm: bool,
    dry_run: bool,
) -> Result<(), String> {
    let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..");
    let python = std::env::var("PYTHON").unwrap_or_else(|_| "python3".into());
    let mut args: Vec<String> = Vec::new();
    if confirm {
        args.push("--confirm".into());
    }
    if dry_run {
        args.push("--dry-run".into());
    }
    args.extend(["logs".into(), service]);

    let mut command = Command::new(python);
    command
        .arg("-m")
        .arg("scripts.tino_cli")
        .args(&args)
        .env("PYTHONPATH", build_pythonpath(&repo_root))
        .current_dir(&repo_root)
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped());

    let mut guard = state.child.lock().await;
    if let Some(mut existing) = guard.take() {
        let _ = existing.kill().await;
    }

    let mut child = command.spawn().map_err(|err| err.to_string())?;
    if let Some(stdout) = child.stdout.take() {
        tauri::async_runtime::spawn(read_stream(
            BufReader::new(stdout).lines(),
            app_handle.clone(),
            "stdout",
        ));
    }
    if let Some(stderr) = child.stderr.take() {
        tauri::async_runtime::spawn(read_stream(
            BufReader::new(stderr).lines(),
            app_handle.clone(),
            "stderr",
        ));
    }

    let child_ref = state.child.clone();
    tauri::async_runtime::spawn(async move {
        loop {
            let status = {
                let mut guard = child_ref.lock().await;
                match guard
                    .as_mut()
                    .and_then(|child| child.try_wait().transpose())
                {
                    Some(Ok(status)) => Some(status),
                    Some(Err(_)) => None,
                    None => None,
                }
            };
            if let Some(status) = status {
                let code = status.and_then(|s| s.code()).unwrap_or_else(|| {
                    if cfg!(windows) {
                        1
                    } else {
                        143
                    }
                });
                let _ = app_handle.emit_all("tino-log-exit", code);
                break;
            }
            tokio::time::sleep(Duration::from_millis(400)).await;
        }
    });

    *guard = Some(child);
    Ok(())
}

#[cfg(feature = "gui")]
#[tauri::command]
pub async fn stop_log_stream(state: tauri::State<'_, LogStreamer>) -> Result<(), String> {
    let mut guard = state.child.lock().await;
    if let Some(mut child) = guard.take() {
        let _ = child.kill().await;
    }
    Ok(())
}

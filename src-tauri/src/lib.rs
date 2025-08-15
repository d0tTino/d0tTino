pub mod commands {
    use reqwest::Client;
    use serde::{Deserialize, Serialize};
    use std::{
        fs::{self, OpenOptions},
        io::Write,
        path::PathBuf,
    };

    #[derive(Deserialize)]
    struct PlanResponse {
        steps: Option<Vec<String>>,
    }

    #[derive(Serialize)]
    pub struct PluginInfo {
        name: String,
        enabled: bool,
    }

    #[derive(Serialize)]
    pub struct Dashboard {
        recent_plans: Vec<String>,
        budget: Option<i64>,
        plugins: Vec<PluginInfo>,
    }

    pub async fn plan(goal: String) -> Result<Vec<String>, String> {
        let client = Client::new();
        let resp = client
            .post("http://localhost:8000/api/plan")
            .json(&serde_json::json!({ "goal": goal }))
            .send()
            .await
            .map_err(|e| e.to_string())?;
        let plan: PlanResponse = resp.json().await.map_err(|e| e.to_string())?;
        let steps = plan.steps.unwrap_or_default();
        if let Ok(home) = std::env::var("HOME") {
            let log_path = PathBuf::from(home)
                .join(".cache")
                .join("d0ttino")
                .join("plans.log");
            if let Some(parent) = log_path.parent() {
                let _ = fs::create_dir_all(parent);
            }
            if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(log_path) {
                let _ = writeln!(file, "{}", goal);
            }
        }
        Ok(steps)
    }

    pub async fn exec(goal: String) -> Result<String, String> {
        let client = Client::new();
        let resp = client
            .get("http://localhost:8000/api/exec")
            .query(&[("goal", goal)])
            .send()
            .await
            .map_err(|e| e.to_string())?;
        resp.text().await.map_err(|e| e.to_string())
    }

    pub async fn list_recipes() -> Result<Vec<String>, String> {
        let base = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../scripts/recipes/plugins");
        let mut names = Vec::new();
        for entry in fs::read_dir(base).map_err(|e| e.to_string())? {
            let entry = entry.map_err(|e| e.to_string())?;
            let path = entry.path();
            if path.extension().and_then(|s| s.to_str()) == Some("py") {
                if let Some(stem) = path.file_stem().and_then(|s| s.to_str()) {
                    if stem != "__init__" {
                        names.push(stem.to_string());
                    }
                }
            }
        }
        names.sort();
        Ok(names)
    }

    pub async fn open_prompt_file(path: String) -> Result<String, String> {
        fs::read_to_string(path).map_err(|e| e.to_string())
    }

    pub async fn run_recipe(name: String, goal: String) -> Result<String, String> {
        use tokio::process::Command;

        // first get the recipe steps as JSON from a small Python snippet
        let output = Command::new("python3")
            .arg("-c")
            .arg(
                "import json,sys,scripts.recipes as r;print(json.dumps(r.discover_recipes()[sys.argv[1]](sys.argv[2])))",
            )
            .arg(&name)
            .arg(&goal)
            .output()
            .await
            .map_err(|e| e.to_string())?;
        if !output.status.success() {
            return Err(String::from_utf8_lossy(&output.stderr).to_string());
        }
        let steps: Vec<String> =
            serde_json::from_slice(&output.stdout).map_err(|e| e.to_string())?;

        let mut log = String::new();
        for step in steps {
            log.push_str(&format!("$ {}\n", step));
            let child = if cfg!(target_os = "windows") {
                Command::new("cmd").arg("/C").arg(&step).output()
            } else {
                Command::new("sh").arg("-c").arg(&step).output()
            };
            let res = child.await.map_err(|e| e.to_string())?;
            log.push_str(&String::from_utf8_lossy(&res.stdout));
            if !res.status.success() {
                log.push_str(&String::from_utf8_lossy(&res.stderr));
            }
            let code = res.status.code().unwrap_or_default();
            log.push_str(&format!("(exit {})\n\n", code));
        }
        Ok(log)
    }

    pub async fn dashboard() -> Result<Dashboard, String> {
        let mut plans = Vec::new();
        if let Ok(home) = std::env::var("HOME") {
            let log_path = PathBuf::from(&home)
                .join(".cache")
                .join("d0ttino")
                .join("plans.log");
            if let Ok(content) = fs::read_to_string(log_path) {
                plans = content
                    .lines()
                    .rev()
                    .take(5)
                    .map(|s| s.to_string())
                    .collect();
            }
        }

        let budget = std::env::var("LLM_ROUTER_BUDGET")
            .ok()
            .and_then(|s| s.parse().ok());

        let mut plugins = Vec::new();
        let reg_path = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../plugin-registry.json");
        if let Ok(data) = fs::read_to_string(reg_path) {
            if let Ok(json) = serde_json::from_str::<serde_json::Value>(&data) {
                if let Some(map) = json.get("plugins").and_then(|v| v.as_object()) {
                    for name in map.keys() {
                        plugins.push(PluginInfo {
                            name: name.clone(),
                            enabled: true,
                        });
                    }
                }
            }
        }

        Ok(Dashboard {
            recent_plans: plans,
            budget,
            plugins,
        })
    }
}

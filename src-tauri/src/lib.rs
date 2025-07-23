pub mod commands {
    use reqwest::Client;
    use serde::Deserialize;
    use std::{fs, path::PathBuf};

    #[derive(Deserialize)]
    struct PlanResponse {
        steps: Option<Vec<String>>,
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
        Ok(plan.steps.unwrap_or_default())
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
}

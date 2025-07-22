use reqwest::Client;
use serde::Deserialize;

#[derive(Deserialize)]
struct PlanResponse {
    steps: Option<Vec<String>>,
}

#[tauri::command]
async fn plan(goal: String) -> Result<Vec<String>, String> {
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

#[tauri::command]
async fn exec(goal: String) -> Result<String, String> {
    let client = Client::new();
    let resp = client
        .get("http://localhost:8000/api/exec")
        .query(&[("goal", goal)])
        .send()
        .await
        .map_err(|e| e.to_string())?;
    resp.text().await.map_err(|e| e.to_string())
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![plan, exec])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

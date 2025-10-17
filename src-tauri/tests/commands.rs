use hyper::{
    service::{make_service_fn, service_fn},
    Body, Method, Request, Response, Server,
};
use std::convert::Infallible;
use std::ffi::OsString;
use std::io::Write;
use std::net::SocketAddr;
use std::sync::Once;
use tokio::task::JoinHandle;
use ume_tauri::commands::{
    cockpit_down, cockpit_logs, cockpit_up, exec, list_recipes, open_prompt_file, plan, run_recipe,
};

async fn spawn_server() -> JoinHandle<()> {
    ensure_pythonpath();
    std::env::set_var("TINO_API_URL", "http://127.0.0.1:8000");
    async fn handler(req: Request<Body>) -> Result<Response<Body>, Infallible> {
        match (req.method(), req.uri().path()) {
            (&Method::POST, "/api/plan") => Ok(Response::new(Body::from("{\"steps\":[\"s\"]}"))),
            (&Method::GET, "/api/exec") => Ok(Response::new(Body::from("ok"))),
            _ => Ok(Response::builder().status(404).body(Body::empty()).unwrap()),
        }
    }

    let addr: SocketAddr = ([127, 0, 0, 1], 8000).into();
    let server = Server::bind(&addr).serve(make_service_fn(|_| async {
        Ok::<_, Infallible>(service_fn(handler))
    }));

    tokio::spawn(async move {
        server.await.expect("server error");
    })
}

#[tokio::test]
async fn list_recipes_returns_sample() {
    let recipes = list_recipes().await.expect("list");
    assert!(recipes.contains(&"sample".to_string()));
}

#[tokio::test]
async fn open_prompt_file_reads_content() {
    let mut file = tempfile::NamedTempFile::new().expect("tempfile");
    writeln!(file, "hello").unwrap();
    let content = open_prompt_file(file.path().display().to_string())
        .await
        .expect("read file");
    assert_eq!(content.trim_end(), "hello");
}

#[tokio::test]
async fn plan_and_exec_use_server() {
    let srv = spawn_server().await;

    let steps = plan("goal".to_string()).await.expect("plan");
    assert_eq!(steps, vec!["s".to_string()]);

    let out = exec("goal".to_string()).await.expect("exec");
    assert_eq!(out, "ok".to_string());

    srv.abort();
}

#[tokio::test]
async fn run_recipe_executes_sample() {
    ensure_pythonpath();
    let out = run_recipe("sample".to_string(), "hello".to_string())
        .await
        .expect("run recipe");
    assert!(out.contains("$ echo hello"));
    assert!(out.contains("hello"));
}

#[tokio::test]
async fn cockpit_actions_execute() {
    ensure_pythonpath();
    let result = cockpit_up().await.expect("cockpit up");
    assert!(result.message.contains("Start"));
    assert!(result.telemetry.is_some());

    let err = cockpit_down(false).await.expect_err("missing confirm");
    assert!(err.contains("confirmation"));

    let details = cockpit_down(true).await.expect("confirmed down");
    assert!(details.message.contains("Stop"));

    let logs = cockpit_logs(Some(10)).await.expect("logs");
    assert!(logs.path.ends_with("cockpit.log"));
}

fn ensure_pythonpath() {
    static INIT: Once = Once::new();
    INIT.call_once(|| {
        let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("..");

        let mut pythonpath = OsString::new();
        pythonpath.push(&root);
        if let Some(existing) = std::env::var_os("PYTHONPATH") {
            if !existing.is_empty() {
                pythonpath.push(if cfg!(windows) { ";" } else { ":" });
                pythonpath.push(existing);
            }
        }
        std::env::set_var("PYTHONPATH", pythonpath);

        let stub_bin = root.join("scripts").join("bin");
        let mut new_path = OsString::new();
        new_path.push(&stub_bin);
        if let Some(existing) = std::env::var_os("PATH") {
            if !existing.is_empty() {
                new_path.push(if cfg!(windows) { ";" } else { ":" });
                new_path.push(existing);
            }
        }
        std::env::set_var("PATH", new_path);
    });
}

#[tokio::test]
async fn list_recipes_detects_new_file() {
    use std::fs;
    use std::path::Path;

    let dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("../scripts/recipes/plugins");
    let file = dir.join("temp_test.py");
    fs::write(&file, "# temp").expect("write file");

    let recipes = list_recipes().await.expect("list");
    fs::remove_file(&file).expect("cleanup");

    assert!(recipes.contains(&"temp_test".to_string()));
}

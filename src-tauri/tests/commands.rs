use std::io::Write;
use std::convert::Infallible;
use std::net::SocketAddr;
use hyper::{service::{make_service_fn, service_fn}, Body, Method, Request, Response, Server};
use tokio::task::JoinHandle;
use ume_tauri::commands::{list_recipes, open_prompt_file, plan, exec, run_recipe};

async fn spawn_server() -> JoinHandle<()> {
    async fn handler(req: Request<Body>) -> Result<Response<Body>, Infallible> {
        match (req.method(), req.uri().path()) {
            (&Method::POST, "/api/plan") => {
                Ok(Response::new(Body::from("{\"steps\":[\"s\"]}")))
            }
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
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("..");
    std::env::set_var("PYTHONPATH", root);
    let out = run_recipe("sample".to_string(), "hello".to_string())
        .await
        .expect("run recipe");
    assert!(out.contains("$ echo hello"));
    assert!(out.contains("hello"));
}

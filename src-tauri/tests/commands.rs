use std::io::Write;
use ume_tauri::commands::{list_recipes, open_prompt_file};

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

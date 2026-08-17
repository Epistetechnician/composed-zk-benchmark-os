use std::fs;
use std::path::{Path, PathBuf};

// State slice: `research-synthesis-trace-replay-v1-repo-hygiene-venv-boundary`.
// A repository-local Python environment is an ignored dependency root, not
// repository source. Its installed lab extensions must not affect the source
// hygiene assertion.

#[test]
fn repo_preserves_level1_hygiene_boundary() {
    let repo_root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("crate should live under workspace/crates");
    let mut forbidden_artifacts = Vec::new();
    let mut empty_files = Vec::new();

    scan_repo(repo_root, &mut forbidden_artifacts, &mut empty_files);

    assert!(
        forbidden_artifacts.is_empty(),
        "Level 1 repo boundary forbids JS package-manager artifacts and node_modules: {forbidden_artifacts:?}"
    );
    assert!(
        empty_files.is_empty(),
        "repo should not contain empty files outside ignored/build roots: {empty_files:?}"
    );
}

fn scan_repo(root: &Path, forbidden_artifacts: &mut Vec<PathBuf>, empty_files: &mut Vec<PathBuf>) {
    let metadata = fs::metadata(root).expect("repo path should be readable");
    if metadata.is_file() {
        let file_name = root
            .file_name()
            .and_then(|name| name.to_str())
            .unwrap_or("");
        if matches!(
            file_name,
            "package.json" | "pnpm-lock.yaml" | "yarn.lock" | "package-lock.json"
        ) {
            forbidden_artifacts.push(root.to_path_buf());
        }
        if metadata.len() == 0 {
            empty_files.push(root.to_path_buf());
        }
        return;
    }

    let dir_name = root
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("");
    if matches!(
        dir_name,
        ".git" | "target" | ".autoresearch" | ".phala-capture" | ".venv"
    ) {
        return;
    }
    if dir_name == "node_modules" {
        forbidden_artifacts.push(root.to_path_buf());
        return;
    }

    for entry in fs::read_dir(root).expect("repo directory should be readable") {
        let entry = entry.expect("repo directory entry should be readable");
        scan_repo(&entry.path(), forbidden_artifacts, empty_files);
    }
}

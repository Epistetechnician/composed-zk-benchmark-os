use std::fs;
use std::path::{Path, PathBuf};

const REQUIRED_BOUNDARIES: &[&str] = &[
    "A benchmark pass is not a proof.",
    "A local replay is not official benchmark evidence.",
    "Evidence append proposals are not accepted evidence.",
    "Evidence-record candidates are not accepted evidence.",
    "Append previews are not accepted evidence",
    "Level2 eligibility reports are not Level2 evidence.",
    "Local soak telemetry is not official benchmark evidence.",
    "Internal timing telemetry is not ZK backend performance.",
    "Failure corpus entries are reproduction aids",
    "Managed-attestation Phase 4 anchor-registry output means one active HSAI identity per accepted, non-reused registered anchor set.",
];

#[test]
fn repo_docs_preserve_required_claim_boundary_statements() {
    let repo_root = repo_root();
    let mut combined = String::new();
    for relative in ["README.md", "AGENTS.md", "docs"] {
        read_markdown_tree(&repo_root.join(relative), &mut combined);
    }

    let missing: Vec<&str> = REQUIRED_BOUNDARIES
        .iter()
        .copied()
        .filter(|boundary| !combined.contains(boundary))
        .collect();
    assert!(missing.is_empty(), "missing claim boundaries: {missing:?}");
}

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("crate should live under repo_root/crates/zkbench-core")
        .to_path_buf()
}

fn read_markdown_tree(path: &Path, combined: &mut String) {
    if path.is_file() {
        if path.extension().and_then(|ext| ext.to_str()) == Some("md") {
            let text = fs::read_to_string(path).expect("markdown file should be readable");
            combined.push_str(&text);
            combined.push('\n');
        }
        return;
    }

    for entry in fs::read_dir(path).expect("markdown directory should be readable") {
        let entry = entry.expect("markdown directory entry should be readable");
        read_markdown_tree(&entry.path(), combined);
    }
}

use std::fs;
use std::path::{Path, PathBuf};

#[test]
fn non_envelope_hsai_crates_do_not_emit_proven_maturity() {
    let workspace_root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("crate should live under workspace/crates");
    let hsai_crates = workspace_root.join("crates");
    let mut violations = Vec::new();

    for file in rust_sources(&hsai_crates) {
        if file
            .file_name()
            .is_some_and(|name| name == "claim_boundary_source_scan.rs")
        {
            continue;
        }
        if file.components().any(|part| {
            part.as_os_str()
                .to_string_lossy()
                .contains("hsai-claim-envelope")
        }) {
            continue;
        }
        let text = fs::read_to_string(&file).expect("source file should be readable");
        for (line_index, line) in text.lines().enumerate() {
            if !line.contains("Maturity::Proven") {
                continue;
            }
            let allowed_boundary_assertion =
                line.contains("< Maturity::Proven") || line.contains("<= Maturity::Attested");
            if !allowed_boundary_assertion {
                violations.push(format!("{}:{}", file.display(), line_index + 1));
            }
        }
        if text.contains("maturity: Maturity::Proven") {
            violations.push(format!("{}:constructs-proven-field", file.display()));
        }
    }

    assert!(
        violations.is_empty(),
        "non-envelope HSAI crates must not emit Proven maturity: {violations:?}"
    );
}

fn rust_sources(root: &Path) -> Vec<PathBuf> {
    let mut out = Vec::new();
    collect_rust_sources(root, &mut out);
    out.sort();
    out
}

fn collect_rust_sources(path: &Path, out: &mut Vec<PathBuf>) {
    let metadata = fs::metadata(path).expect("path should be readable");
    if metadata.is_file() {
        if path.extension().is_some_and(|ext| ext == "rs") {
            out.push(path.to_path_buf());
        }
        return;
    }
    for entry in fs::read_dir(path).expect("directory should be readable") {
        let entry = entry.expect("directory entry should be readable");
        collect_rust_sources(&entry.path(), out);
    }
}

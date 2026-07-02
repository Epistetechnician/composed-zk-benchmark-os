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

#[test]
fn hsai_crates_do_not_use_process_or_network_apis() {
    let workspace_root = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("crate should live under workspace/crates");
    let hsai_crates = workspace_root.join("crates");
    let forbidden_patterns = [
        "std::process",
        "Command::new",
        "std::net",
        "TcpStream",
        "UdpSocket",
        "reqwest::",
        "ureq::",
        "hyper::",
        "tonic::",
        "tokio::net",
        "curl::",
        "surf::",
        "isahc::",
    ];
    let mut violations = Vec::new();

    for file in rust_sources(&hsai_crates) {
        if file
            .file_name()
            .is_some_and(|name| name == "claim_boundary_source_scan.rs")
        {
            continue;
        }
        let text = fs::read_to_string(&file).expect("source file should be readable");
        for (line_index, line) in text.lines().enumerate() {
            for pattern in forbidden_patterns {
                if line.contains(pattern) {
                    if is_phase102_operator_provider_exception(&file, pattern) {
                        continue;
                    }
                    if is_phase113_tls_channel_exception(&file, pattern) {
                        continue;
                    }
                    if is_phase313_fixture_runner_exception(&file, pattern, line) {
                        continue;
                    }
                    violations.push(format!("{}:{}:{pattern}", file.display(), line_index + 1));
                }
            }
        }
    }

    assert!(
        violations.is_empty(),
        "HSAI crates must stay local-only and avoid process/network APIs: {violations:?}"
    );
}

fn is_phase102_operator_provider_exception(file: &Path, pattern: &str) -> bool {
    pattern == "ureq::"
        && file.ends_with(Path::new(
            "hsai-attestation-phala/src/operator_live_provider.rs",
        ))
}

fn is_phase113_tls_channel_exception(file: &Path, pattern: &str) -> bool {
    let tls_example = file.ends_with(Path::new(
        "hsai-attestation-phala/examples/operator_live_tls_channel_artifact.rs",
    ));
    let tls_contract_test = file.ends_with(Path::new(
        "hsai-attestation-phala/tests/phala_operator_live_tls_channel_contract.rs",
    ));
    if tls_example {
        matches!(pattern, "std::net" | "TcpStream" | "std::process")
    } else {
        tls_contract_test && matches!(pattern, "reqwest::" | "ureq::" | "Command::new")
    }
}

fn is_phase313_fixture_runner_exception(file: &Path, pattern: &str, line: &str) -> bool {
    if !file.ends_with(Path::new("hsai-agent-admission/src/lib.rs")) {
        return false;
    }
    match pattern {
        "std::process" => {
            line == "use std::process::Stdio;"
                || line.contains("std::process::Command::new(executable)")
        }
        "Command::new" => line.contains("std::process::Command::new(executable)"),
        _ => false,
    }
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
        let entry_path = entry.path();
        if path.file_name().is_some_and(|name| name == "crates") {
            let crate_name = entry_path
                .file_name()
                .map(|name| name.to_string_lossy())
                .unwrap_or_default();
            if !crate_name.starts_with("hsai-") {
                continue;
            }
        }
        collect_rust_sources(&entry_path, out);
    }
}

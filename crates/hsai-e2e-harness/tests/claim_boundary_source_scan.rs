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
                    if is_phase325_real_command_lane_fixed_smt_exception(
                        &file, pattern, &text, line_index, line,
                    ) {
                        continue;
                    }
                    if is_phase529_tiny_z3_hermetic_backend_execution_exception(
                        &file, pattern, &text, line_index, line,
                    ) {
                        continue;
                    }
                    if is_phase657_tiny_z3_gateway_digest_binding_execution_exception(
                        &file, pattern, &text, line_index, line,
                    ) {
                        continue;
                    }
                    if is_phase609_real_materialized_staging_runner_exception(
                        &file, pattern, &text, line_index, line,
                    ) {
                        continue;
                    }
                    if is_phase798_native_transcript_test_exception(
                        workspace_root,
                        &file,
                        pattern,
                        &text,
                        line_index,
                        line,
                    ) {
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

fn is_phase325_real_command_lane_fixed_smt_exception(
    file: &Path,
    pattern: &str,
    text: &str,
    line_index: usize,
    line: &str,
) -> bool {
    if !file.ends_with(Path::new("hsai-agent-admission/src/lib.rs")) {
        return false;
    }
    if !matches!(pattern, "std::process" | "Command::new") {
        return false;
    }
    if line.trim() != "let mut command = std::process::Command::new(fixed_executable);" {
        return false;
    }
    enclosing_function_name(text, line_index)
        == Some("run_gateway_formal_real_command_lane_fixed_smt_process")
}

fn is_phase529_tiny_z3_hermetic_backend_execution_exception(
    file: &Path,
    pattern: &str,
    text: &str,
    line_index: usize,
    line: &str,
) -> bool {
    if !file.ends_with(Path::new("hsai-agent-admission/src/lib.rs")) {
        return false;
    }
    if !matches!(pattern, "std::process" | "Command::new") {
        return false;
    }
    if line.trim() != "let mut command = std::process::Command::new(z3_executable);" {
        return false;
    }
    text.contains(GATEWAY_FORMAL_TINY_Z3_PHASE529_CLAIM_BOUNDARY_NEEDLE)
        && enclosing_function_name(text, line_index)
            == Some("run_gateway_formal_tiny_z3_hermetic_backend_execution_result")
}

const GATEWAY_FORMAL_TINY_Z3_PHASE529_CLAIM_BOUNDARY_NEEDLE: &str =
    "local tiny-Z3 hermetic backend execution result metadata only";

fn is_phase657_tiny_z3_gateway_digest_binding_execution_exception(
    file: &Path,
    pattern: &str,
    text: &str,
    line_index: usize,
    line: &str,
) -> bool {
    if !file.ends_with(Path::new("hsai-agent-admission/src/lib.rs")) {
        return false;
    }
    if !matches!(pattern, "std::process" | "Command::new") {
        return false;
    }
    if line.trim() != "let mut command = std::process::Command::new(z3_executable);" {
        return false;
    }
    text.contains(HSAI_TINY_Z3_PHASE657_CLAIM_BOUNDARY_NEEDLE)
        && enclosing_function_name(text, line_index)
            == Some("run_hsai_tiny_z3_gateway_digest_binding_local_execution")
}

const HSAI_TINY_Z3_PHASE657_CLAIM_BOUNDARY_NEEDLE: &str =
    "local HSAI tiny-Z3 gateway proposal digest-binding execution observation";

fn is_phase609_real_materialized_staging_runner_exception(
    file: &Path,
    pattern: &str,
    text: &str,
    line_index: usize,
    line: &str,
) -> bool {
    if !file.ends_with(Path::new(
        "hsai-agent-admission/examples/phase609_real_materialized_staging_runner.rs",
    )) {
        return false;
    }
    match pattern {
        "std::process" => line.trim() == "use std::process::{Command, Stdio};",
        "Command::new" => {
            line.trim() == "let output = Command::new(program)"
                && enclosing_function_name(text, line_index) == Some("run_output")
        }
        _ => false,
    }
}

fn is_phase798_native_transcript_test_exception(
    workspace_root: &Path,
    file: &Path,
    pattern: &str,
    text: &str,
    line_index: usize,
    line: &str,
) -> bool {
    let descriptor_test = file
        == workspace_root.join(
            "crates/hsai-native-transcript-preparation/tests/descriptor_relative_collector.rs",
        );
    let driver_test = file
        == workspace_root
            .join("crates/hsai-native-transcript-preparation/tests/operator_preparation_driver.rs");

    let authorized = if descriptor_test {
        match (line_index, pattern, line) {
            (9, "std::process", "use std::process::Command;") => true,
            (36, "std::process", "            std::process::id(),") => {
                line_is_within_impl_function(text, line_index, "impl Fixture {", "new")
            }
            (282, "Command::new", "    let fifo_status = Command::new(\"/usr/bin/mkfifo\")") => {
                line_is_within_function(
                    text,
                    line_index,
                    "rejects_non_utf8_symlink_and_terminal_kind_and_size_boundaries",
                )
            }
            (492, "std::process", "        \"std::process\",")
            | (494, "std::net", "        \"std::net\",")
            | (495, "TcpStream", "        \"TcpStream\",") => line_is_within_function(
                text,
                line_index,
                "collector_source_has_no_process_network_shell_or_canonicalization_path",
            ),
            _ => false,
        }
    } else if driver_test {
        match (line_index, pattern, line) {
            (199, "std::process", "        \"std::process\",")
            | (200, "std::net", "        \"std::net\",")
            | (206, "Command::new", "        \"Command::new\",")
            | (207, "TcpStream", "        \"TcpStream\",")
            | (208, "UdpSocket", "        \"UdpSocket\",") => line_is_within_function(
                text,
                line_index,
                "driver_source_has_no_forbidden_execution_or_io_surface",
            ),
            _ => false,
        }
    } else {
        false
    };

    authorized && text.lines().filter(|candidate| *candidate == line).count() == 1
}

fn line_is_within_impl_function(
    text: &str,
    line_index: usize,
    expected_impl: &str,
    expected_function: &str,
) -> bool {
    let lines = text.lines().collect::<Vec<_>>();
    let Some(impl_index) = lines
        .iter()
        .take(line_index + 1)
        .rposition(|line| line.trim() == expected_impl)
    else {
        return false;
    };
    let mut depth = 0;
    for line in &lines[impl_index..line_index] {
        depth += source_brace_delta(line);
        if depth <= 0 {
            return false;
        }
    }
    line_is_within_function(
        &lines[impl_index..=line_index].join("\n"),
        line_index - impl_index,
        expected_function,
    )
}

fn line_is_within_function(text: &str, line_index: usize, expected: &str) -> bool {
    let mut target_depth = None;
    for (index, line) in text.lines().enumerate().take(line_index + 1) {
        if target_depth.is_none() {
            let trimmed = line.trim_start();
            let name = trimmed
                .strip_prefix("pub fn ")
                .or_else(|| trimmed.strip_prefix("fn "))
                .and_then(|rest| rest.split('(').next());
            if name == Some(expected) {
                let depth = source_brace_delta(line);
                if depth <= 0 {
                    return false;
                }
                target_depth = Some(depth);
            }
        } else if index < line_index {
            let depth = target_depth.expect("target depth should be initialized")
                + source_brace_delta(line);
            if depth <= 0 {
                return false;
            }
            target_depth = Some(depth);
        }
    }
    target_depth.is_some()
}

fn source_brace_delta(line: &str) -> i32 {
    let mut delta = 0;
    let mut in_string = false;
    let mut escaped = false;
    let bytes = line.as_bytes();
    let mut index = 0;
    while index < bytes.len() {
        let byte = bytes[index];
        if in_string {
            if escaped {
                escaped = false;
            } else if byte == b'\\' {
                escaped = true;
            } else if byte == b'"' {
                in_string = false;
            }
        } else if byte == b'"' {
            in_string = true;
        } else if byte == b'/' && bytes.get(index + 1) == Some(&b'/') {
            break;
        } else if byte == b'{' {
            delta += 1;
        } else if byte == b'}' {
            delta -= 1;
        }
        index += 1;
    }
    delta
}

fn enclosing_function_name(text: &str, line_index: usize) -> Option<&str> {
    let lines = text.lines().take(line_index + 1).collect::<Vec<_>>();
    lines
        .iter()
        .rev()
        .find_map(|line| {
            let line = line.trim_start();
            line.strip_prefix("pub fn ")
                .or_else(|| line.strip_prefix("fn "))
        })
        .and_then(|rest| rest.split('(').next())
}

#[test]
fn phase325_real_command_lane_process_exception_is_single_function_only() {
    let file = Path::new("hsai-agent-admission/src/lib.rs");
    let allowed = "pub fn run_gateway_formal_real_command_lane_fixed_smt_process(\n\
        fixed_executable: &std::path::Path,\n\
    ) {\n\
        let mut command = std::process::Command::new(fixed_executable);\n\
    }\n";
    let denied = "pub fn arbitrary_backend_runner(\n\
        fixed_executable: &std::path::Path,\n\
    ) {\n\
        let mut command = std::process::Command::new(fixed_executable);\n\
    }\n";
    assert!(is_phase325_real_command_lane_fixed_smt_exception(
        file,
        "Command::new",
        allowed,
        3,
        "        let mut command = std::process::Command::new(fixed_executable);",
    ));
    assert!(!is_phase325_real_command_lane_fixed_smt_exception(
        file,
        "Command::new",
        denied,
        3,
        "        let mut command = std::process::Command::new(fixed_executable);",
    ));
}

#[test]
fn phase529_tiny_z3_process_exception_is_single_function_only() {
    let file = Path::new("hsai-agent-admission/src/lib.rs");
    let allowed = format!(
        "const CLAIM: &str = \"{GATEWAY_FORMAL_TINY_Z3_PHASE529_CLAIM_BOUNDARY_NEEDLE}\";\n\
        pub fn run_gateway_formal_tiny_z3_hermetic_backend_execution_result(\n\
            z3_executable: &std::path::Path,\n\
        ) {{\n\
            let mut command = std::process::Command::new(z3_executable);\n\
        }}\n"
    );
    let denied_function = format!(
        "const CLAIM: &str = \"{GATEWAY_FORMAL_TINY_Z3_PHASE529_CLAIM_BOUNDARY_NEEDLE}\";\n\
        pub fn arbitrary_backend_runner(\n\
            z3_executable: &std::path::Path,\n\
        ) {{\n\
            let mut command = std::process::Command::new(z3_executable);\n\
        }}\n"
    );
    let denied_boundary = "pub fn run_gateway_formal_tiny_z3_hermetic_backend_execution_result(\n\
        z3_executable: &std::path::Path,\n\
    ) {\n\
        let mut command = std::process::Command::new(z3_executable);\n\
    }\n";
    assert!(is_phase529_tiny_z3_hermetic_backend_execution_exception(
        file,
        "Command::new",
        &allowed,
        4,
        "            let mut command = std::process::Command::new(z3_executable);",
    ));
    assert!(!is_phase529_tiny_z3_hermetic_backend_execution_exception(
        file,
        "Command::new",
        &denied_function,
        4,
        "            let mut command = std::process::Command::new(z3_executable);",
    ));
    assert!(!is_phase529_tiny_z3_hermetic_backend_execution_exception(
        file,
        "Command::new",
        denied_boundary,
        3,
        "        let mut command = std::process::Command::new(z3_executable);",
    ));
}

#[test]
fn phase657_tiny_z3_process_exception_is_single_function_only() {
    let file = Path::new("hsai-agent-admission/src/lib.rs");
    let allowed = format!(
        "const CLAIM: &str = \"{HSAI_TINY_Z3_PHASE657_CLAIM_BOUNDARY_NEEDLE}\";\n\
        pub fn run_hsai_tiny_z3_gateway_digest_binding_local_execution(\n\
            z3_executable: &std::path::Path,\n\
        ) {{\n\
            let mut command = std::process::Command::new(z3_executable);\n\
        }}\n"
    );
    let denied_function = format!(
        "const CLAIM: &str = \"{HSAI_TINY_Z3_PHASE657_CLAIM_BOUNDARY_NEEDLE}\";\n\
        pub fn arbitrary_backend_runner(\n\
            z3_executable: &std::path::Path,\n\
        ) {{\n\
            let mut command = std::process::Command::new(z3_executable);\n\
        }}\n"
    );
    let denied_boundary = "pub fn run_hsai_tiny_z3_gateway_digest_binding_local_execution(\n\
        z3_executable: &std::path::Path,\n\
    ) {\n\
        let mut command = std::process::Command::new(z3_executable);\n\
    }\n";
    assert!(
        is_phase657_tiny_z3_gateway_digest_binding_execution_exception(
            file,
            "Command::new",
            &allowed,
            3,
            "        let mut command = std::process::Command::new(z3_executable);",
        )
    );
    assert!(
        !is_phase657_tiny_z3_gateway_digest_binding_execution_exception(
            file,
            "Command::new",
            &denied_function,
            3,
            "        let mut command = std::process::Command::new(z3_executable);",
        )
    );
    assert!(
        !is_phase657_tiny_z3_gateway_digest_binding_execution_exception(
            file,
            "Command::new",
            denied_boundary,
            2,
            "        let mut command = std::process::Command::new(z3_executable);",
        )
    );
}

#[test]
fn phase609_staging_runner_process_exception_is_single_function_only() {
    let file =
        Path::new("hsai-agent-admission/examples/phase609_real_materialized_staging_runner.rs");
    let allowed = "fn run_output(program: &str) {\n\
        let output = Command::new(program)\n\
            .output();\n\
    }\n";
    let denied = "fn arbitrary_runner(program: &str) {\n\
        let output = Command::new(program)\n\
            .output();\n\
    }\n";
    assert!(is_phase609_real_materialized_staging_runner_exception(
        file,
        "Command::new",
        allowed,
        1,
        "        let output = Command::new(program)",
    ));
    assert!(!is_phase609_real_materialized_staging_runner_exception(
        file,
        "Command::new",
        denied,
        1,
        "        let output = Command::new(program)",
    ));
}

#[test]
fn phase798_native_transcript_test_exception_is_exactly_confined() {
    let workspace_root = Path::new("/workspace");
    let descriptor_file = workspace_root
        .join("crates/hsai-native-transcript-preparation/tests/descriptor_relative_collector.rs");
    let driver_file = workspace_root
        .join("crates/hsai-native-transcript-preparation/tests/operator_preparation_driver.rs");
    let descriptor = include_str!(
        "../../hsai-native-transcript-preparation/tests/descriptor_relative_collector.rs"
    );
    let driver = include_str!(
        "../../hsai-native-transcript-preparation/tests/operator_preparation_driver.rs"
    );

    for (line_index, pattern) in [
        (9, "std::process"),
        (36, "std::process"),
        (282, "Command::new"),
        (492, "std::process"),
        (494, "std::net"),
        (495, "TcpStream"),
    ] {
        let line = descriptor.lines().nth(line_index).unwrap();
        assert!(is_phase798_native_transcript_test_exception(
            workspace_root,
            &descriptor_file,
            pattern,
            descriptor,
            line_index,
            line,
        ));
    }
    for (line_index, pattern) in [
        (199, "std::process"),
        (200, "std::net"),
        (206, "Command::new"),
        (207, "TcpStream"),
        (208, "UdpSocket"),
    ] {
        let line = driver.lines().nth(line_index).unwrap();
        assert!(is_phase798_native_transcript_test_exception(
            workspace_root,
            &driver_file,
            pattern,
            driver,
            line_index,
            line,
        ));
    }

    let import = descriptor.lines().nth(9).unwrap();
    assert!(!is_phase798_native_transcript_test_exception(
        workspace_root,
        Path::new(
            "/workspace/crates/nested/crates/hsai-native-transcript-preparation/tests/descriptor_relative_collector.rs",
        ),
        "std::process",
        descriptor,
        9,
        import,
    ));
    assert!(!is_phase798_native_transcript_test_exception(
        workspace_root,
        &descriptor_file,
        "std::process",
        descriptor,
        10,
        import,
    ));
    assert!(!is_phase798_native_transcript_test_exception(
        workspace_root,
        &descriptor_file,
        "Command::new",
        descriptor,
        282,
        "    let fifo_status = Command::new(\"/usr/bin/printf\")",
    ));

    let duplicate_import = format!("{descriptor}{import}\n");
    assert!(!is_phase798_native_transcript_test_exception(
        workspace_root,
        &descriptor_file,
        "std::process",
        &duplicate_import,
        9,
        import,
    ));

    let wrong_impl = descriptor.replace("impl Fixture {", "mod OtherScope {");
    let process_id = descriptor.lines().nth(36).unwrap();
    assert!(!is_phase798_native_transcript_test_exception(
        workspace_root,
        &descriptor_file,
        "std::process",
        &wrong_impl,
        36,
        process_id,
    ));

    let descriptor_after_close = descriptor.replace(
        "    let source = include_str!(\"../src/collector.rs\");",
        "} // close before the exact forbidden literals",
    );
    let descriptor_literal = descriptor.lines().nth(492).unwrap();
    assert!(!is_phase798_native_transcript_test_exception(
        workspace_root,
        &descriptor_file,
        "std::process",
        &descriptor_after_close,
        492,
        descriptor_literal,
    ));

    let driver_after_close = driver.replace(
        "    let source = include_str!(\"../src/driver.rs\");",
        "} // close before the exact forbidden literals",
    );
    let driver_literal = driver.lines().nth(199).unwrap();
    assert!(!is_phase798_native_transcript_test_exception(
        workspace_root,
        &driver_file,
        "std::process",
        &driver_after_close,
        199,
        driver_literal,
    ));
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

// Operator-facing Phase 609 staging runner.
//
// This example runs the exact Phase 604 focused local command, hashes bounded
// stdout/stderr transcripts in memory, and materializes a Phase 607 quarantined
// capture packet under the ignored `.gateway-demo-runs/` root. It does not retain raw logs.
// It does not import external results, claim not accepted evidence as accepted
// evidence, mutate accepted evidence outside the focused local test fixture
// path, create Level2+ evidence, populate score axes, run Lean, run COBALT,
// create proof/checker/solver artifacts, or claim semantic correctness.
// It does not claim production readiness.
// It does not grant authority.

use hsai_agent_admission::{
    materialize_gateway_formal_tiny_z3_real_materialized_staging_runner_capture,
    read_gateway_formal_tiny_z3_real_materialized_operator_capture_output_bundle,
    GatewayFormalTinyZ3RealMaterializedStagingRunnerObservedProcess,
    GatewayFormalTinyZ3RealMaterializedStagingRunnerRequest,
    GATEWAY_FORMAL_TINY_Z3_REAL_MATERIALIZED_PHASE604_FOCUSED_COMMAND,
};
use hsai_claim_envelope::Hash;
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::{Instant, SystemTime, UNIX_EPOCH};

const ENV_ACK: &str = "HSAI_PHASE609_ACK";
const ENV_OUTPUT_ROOT: &str = "HSAI_PHASE609_OUTPUT_ROOT";
const ENV_RUN_ID: &str = "HSAI_PHASE609_RUN_ID";
const ENV_OPERATOR_ID: &str = "HSAI_PHASE609_OPERATOR_ID";
const ENV_CREATED_AT_UNIX: &str = "HSAI_PHASE609_CREATED_AT_UNIX";
const ENV_OVERWRITE: &str = "HSAI_PHASE609_OVERWRITE";
const ENV_Z3_EXECUTABLE: &str = "HSAI_PHASE609_Z3_EXECUTABLE";

const FIXED_ACK: &str =
    "I acknowledge Phase 609 writes local quarantined staging capture metadata only under .gateway-demo-runs.";

#[derive(Debug, Serialize)]
struct Phase609Summary {
    schema_version: String,
    run_id: String,
    output_root: String,
    manifest_digest: String,
    readback_validation_digest: String,
    command_line: String,
    process_exit_status: i32,
    stdout_transcript_digest: String,
    stderr_transcript_digest: String,
    claim_boundary: String,
    external_result_import_created: bool,
    accepted_evidence_ledger_mutated: bool,
    creates_level2_evidence: bool,
    populates_score_axes: bool,
    semantic_correctness_claimed: bool,
    production_readiness_claimed: bool,
}

struct CapturedOutput {
    status_code: i32,
    stdout: Vec<u8>,
    stderr: Vec<u8>,
}

fn fail(message: &str) -> ! {
    panic!("phase609_real_materialized_staging_runner: {message}");
}

fn require_env(name: &str) -> String {
    match std::env::var(name) {
        Ok(value) if !value.trim().is_empty() => value,
        Ok(_) => fail(&format!("{name} must be non-empty")),
        Err(_) => fail(&format!("{name} must be set")),
    }
}

fn optional_env(name: &str) -> Option<String> {
    match std::env::var(name) {
        Ok(value) if !value.trim().is_empty() => Some(value),
        _ => None,
    }
}

fn parse_bool_env(name: &str, raw: Option<String>, default: bool) -> bool {
    match raw.as_deref() {
        None => default,
        Some("true") => true,
        Some("false") => false,
        Some(other) => fail(&format!("{name} must be 'true' or 'false', got '{other}'")),
    }
}

fn parse_created_at(raw: Option<String>) -> u64 {
    match raw {
        None => now_unix(),
        Some(value) => value.parse::<u64>().unwrap_or_else(|_| {
            fail(&format!(
                "{ENV_CREATED_AT_UNIX} must be a non-negative integer"
            ))
        }),
    }
}

fn now_unix() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_else(|err| fail(&format!("system clock before unix epoch: {err}")))
        .as_secs()
}

fn hash_hex(hash: Hash) -> String {
    let mut out = String::with_capacity(64);
    for byte in hash.0 {
        out.push_str(&format!("{byte:02x}"));
    }
    out
}

fn hash_bytes(bytes: &[u8]) -> Hash {
    let digest = Sha256::digest(bytes);
    let mut out = [0u8; 32];
    out.copy_from_slice(&digest);
    Hash(out)
}

fn ensure_ignored_demo_root(output_root: &Path) {
    if !output_root.is_absolute() {
        fail(&format!(
            "{ENV_OUTPUT_ROOT} must be absolute, got '{}'",
            output_root.display()
        ));
    }
    let current_dir =
        std::env::current_dir().unwrap_or_else(|err| fail(&format!("current_dir failed: {err}")));
    let ignored_root = current_dir.join(".gateway-demo-runs");
    if !output_root.starts_with(&ignored_root) {
        fail(&format!(
            "{ENV_OUTPUT_ROOT} must be under ignored root '{}'",
            ignored_root.display()
        ));
    }
    fs::create_dir_all(&ignored_root)
        .unwrap_or_else(|err| fail(&format!("failed to create ignored demo root: {err}")));
}

fn run_output(program: &str, args: &[&str], cwd: &Path) -> CapturedOutput {
    let output = Command::new(program)
        .args(args)
        .current_dir(cwd)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .unwrap_or_else(|err| fail(&format!("{program} failed to spawn: {err}")));
    CapturedOutput {
        status_code: output.status.code().unwrap_or(-1),
        stdout: output.stdout,
        stderr: output.stderr,
    }
}

fn run_output_text(program: &str, args: &[&str], cwd: &Path) -> String {
    let output = run_output(program, args, cwd);
    if output.status_code != 0 {
        fail(&format!(
            "{program} exited with status {}",
            output.status_code
        ));
    }
    String::from_utf8(output.stdout)
        .unwrap_or_else(|err| fail(&format!("{program} stdout was not UTF-8: {err}")))
        .trim()
        .to_owned()
}

fn dirty_status(cwd: &Path) -> String {
    let status = run_output("git", &["status", "--short"], cwd);
    if status.status_code != 0 {
        return "unknown".to_owned();
    }
    if status.stdout.is_empty() {
        "clean".to_owned()
    } else {
        "dirty".to_owned()
    }
}

fn main() {
    let ack = require_env(ENV_ACK);
    if ack != FIXED_ACK {
        fail(&format!(
            "{ENV_ACK} did not match the required acknowledgement literal"
        ));
    }

    let output_root = PathBuf::from(require_env(ENV_OUTPUT_ROOT));
    ensure_ignored_demo_root(&output_root);
    let run_id = optional_env(ENV_RUN_ID).unwrap_or_else(|| "phase609-staging-run".to_owned());
    let operator_id = optional_env(ENV_OPERATOR_ID).unwrap_or_else(|| format!("{run_id}-operator"));
    let created_at_unix = parse_created_at(optional_env(ENV_CREATED_AT_UNIX));
    let overwrite = parse_bool_env(ENV_OVERWRITE, optional_env(ENV_OVERWRITE), true);
    let z3_executable = optional_env(ENV_Z3_EXECUTABLE).unwrap_or_else(|| "z3".to_owned());
    let current_dir =
        std::env::current_dir().unwrap_or_else(|err| fail(&format!("current_dir failed: {err}")));

    let repository_commit = run_output_text("git", &["rev-parse", "HEAD"], &current_dir);
    let branch_name = run_output_text("git", &["rev-parse", "--abbrev-ref", "HEAD"], &current_dir);
    let rust_toolchain_version = run_output_text("rustc", &["--version"], &current_dir);
    let z3_version_output = run_output_text(&z3_executable, &["--version"], &current_dir);

    let run_started_at_unix = now_unix();
    let started = Instant::now();
    let focused = run_output(
        "cargo",
        &[
            "test",
            "-p",
            "hsai-agent-admission",
            "phase604_real_z3_unsat_result_materializes_accepted_ledger_artifact_without_claim_escalation",
            "--",
            "--nocapture",
        ],
        &current_dir,
    );
    let elapsed_ms = u64::try_from(started.elapsed().as_millis()).unwrap_or(u64::MAX);
    let run_finished_at_unix = now_unix();

    let protected_roots = vec![
        current_dir.join(".git"),
        current_dir.join("crates"),
        current_dir.join("docs"),
        current_dir.join("target"),
    ];
    let request = GatewayFormalTinyZ3RealMaterializedStagingRunnerRequest {
        run_id: run_id.clone(),
        operator_id,
        source_remote_or_bundle: "local-worktree".to_owned(),
        repository_commit,
        branch_name,
        dirty_status: dirty_status(&current_dir),
        operating_system: std::env::consts::OS.to_owned(),
        architecture: std::env::consts::ARCH.to_owned(),
        rust_toolchain_version,
        z3_executable_path: z3_executable,
        z3_version_output,
        run_started_at_unix,
        run_finished_at_unix,
        elapsed_ms: elapsed_ms.max(1),
        created_at_unix,
        overwrite,
        protected_roots,
    };
    let observed = GatewayFormalTinyZ3RealMaterializedStagingRunnerObservedProcess {
        command_line: GATEWAY_FORMAL_TINY_Z3_REAL_MATERIALIZED_PHASE604_FOCUSED_COMMAND.to_owned(),
        process_exit_status: focused.status_code,
        stdout_transcript: focused.stdout,
        stderr_transcript: focused.stderr,
        z3_available: true,
        run_skipped: false,
    };
    let manifest = materialize_gateway_formal_tiny_z3_real_materialized_staging_runner_capture(
        &output_root,
        &request,
        &observed,
    )
    .unwrap_or_else(|err| fail(&format!("staging runner capture failed: {err:?}")));
    let readback =
        read_gateway_formal_tiny_z3_real_materialized_operator_capture_output_bundle(&output_root)
            .unwrap_or_else(|err| fail(&format!("capture readback failed: {err:?}")));
    if readback != manifest {
        fail("capture bundle readback drifted");
    }

    let summary = Phase609Summary {
        schema_version: "hsai-phase609-staging-runner-summary-v1".to_owned(),
        run_id,
        output_root: output_root.display().to_string(),
        manifest_digest: hash_hex(manifest.digest()),
        readback_validation_digest: hash_hex(manifest.readback_validation_digest),
        command_line: GATEWAY_FORMAL_TINY_Z3_REAL_MATERIALIZED_PHASE604_FOCUSED_COMMAND.to_owned(),
        process_exit_status: observed.process_exit_status,
        stdout_transcript_digest: hash_hex(hash_bytes(&observed.stdout_transcript)),
        stderr_transcript_digest: hash_hex(hash_bytes(&observed.stderr_transcript)),
        claim_boundary: manifest.claim_boundary,
        external_result_import_created: manifest.external_result_import_created,
        accepted_evidence_ledger_mutated: manifest.accepted_evidence_ledger_mutated,
        creates_level2_evidence: manifest.creates_level2_evidence,
        populates_score_axes: manifest.populates_score_axes,
        semantic_correctness_claimed: manifest.semantic_correctness_claimed,
        production_readiness_claimed: manifest.production_readiness_claimed,
    };
    match serde_json::to_string_pretty(&summary) {
        Ok(json) => println!("{json}"),
        Err(err) => fail(&format!("summary serialization failed: {err}")),
    }
}

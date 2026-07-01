use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};

const PACKET_PATH: &str = "docs/254-hsai-gateway-bridge-public-claim-packet.md";
const PACKET_BASE_COMMIT: &str = "edbae44ea2f47f067683e28d2c6d5cb8af4362e8";
const IGNORED_DEMO_ROOT: &str = ".gateway-demo-runs/phase-253-gateway-acceptance-preview/";
const MANIFEST_FENCE: &str = "```claim-packet-manifest-v1";

#[test]
fn phase_254_public_claim_packet_matches_committed_reproduction_contract() {
    let repo_root = repo_root();
    let packet = read(&repo_root.join(PACKET_PATH));
    let manifest = parse_manifest(&packet).expect("committed packet manifest should parse");
    validate_manifest_contract(&manifest).expect("committed packet manifest should validate");

    assert_contains_all(
        &packet,
        &[
            "# Phase 254 HSAI Gateway Bridge Public Claim Packet",
            "Status: complete for bounded public claim packaging.",
            PACKET_BASE_COMMIT,
            "edbae44 Materialize gateway acceptance preview bundle",
            "Phase 249: gateway action proposal to attestation challenge binding.",
            "Phase 250: ignored local gateway/operator bridge bundle.",
            "Phase 251: reviewed local promotion preflight metadata.",
            "Phase 252: candidate-only acceptance preview metadata.",
            "Phase 253: ignored local acceptance-preview output bundle.",
            "This is a local metadata and artifact-shape claim only.",
        ],
    );

    assert_manifest_singletons(
        &manifest,
        &[
            (
                "packet_id",
                "phase-254-hsai-gateway-bridge-public-claim-packet",
            ),
            ("packet_path", PACKET_PATH),
            ("base_commit", PACKET_BASE_COMMIT),
            (
                "top_commit",
                "edbae44 Materialize gateway acceptance preview bundle",
            ),
            ("claim_level", "local_metadata_and_artifact_shape_only"),
            ("max_claim_maturity", "Attested"),
            ("ignored_demo_root", IGNORED_DEMO_ROOT),
            ("ignored_status", "!! .gateway-demo-runs/"),
        ],
    );

    assert_manifest_values(
        &manifest,
        "validated_phase",
        &["249", "250", "251", "252", "253"],
    );
    assert_manifest_values(
        &manifest,
        "declared_file",
        &[
            "gateway-acceptance-preview/manifest.json",
            "gateway-acceptance-preview/acceptance-preview-request.json",
            "gateway-acceptance-preview/acceptance-preview-report.json",
            "gateway-acceptance-preview/source-preflight-report.json",
            "gateway-acceptance-preview/non-claims.md",
            "gateway-acceptance-preview/validation-report.json",
        ],
    );
    assert_manifest_values(
        &manifest,
        "summary_flag",
        &[
            "candidate_only:true",
            "mutates_accepted_evidence_ledger:false",
            "creates_level2_evidence:false",
            "populates_score_axes:false",
            "grants_authority:false",
            "retains_raw_provider_artifacts:false",
            "retains_credentials_or_secrets:false",
        ],
    );

    assert_contains_all(
        &packet,
        &[
            "cargo fmt --all --check",
            "git diff --check",
            "cargo test -p hsai-agent-admission --lib gateway_acceptance_preview_bundle",
            "cargo test -p hsai-agent-admission --test gateway_acceptance_preview_bundle_contract",
            "cargo check -p hsai-agent-admission --examples",
            "cargo run -p hsai-agent-admission --example gateway_acceptance_preview_bundle",
            "cargo test -p hsai-agent-admission --lib --quiet",
            "cargo test -p zkbench-core --test repo_hygiene --quiet",
            "cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet",
            "cargo test --workspace --quiet",
            "cargo test --workspace --features external-runner --quiet",
        ],
    );
    assert_manifest_values(
        &manifest,
        "phase253_command",
        &[
            "cargo fmt --all --check",
            "git diff --check",
            "cargo test -p hsai-agent-admission --lib gateway_acceptance_preview_bundle",
            "cargo test -p hsai-agent-admission --test gateway_acceptance_preview_bundle_contract",
            "cargo check -p hsai-agent-admission --examples",
            "cargo run -p hsai-agent-admission --example gateway_acceptance_preview_bundle",
            "cargo test -p hsai-agent-admission --lib --quiet",
            "cargo test -p zkbench-core --test repo_hygiene --quiet",
            "cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet",
            "cargo test --workspace --quiet",
            "cargo test --workspace --features external-runner --quiet",
        ],
    );
    assert_manifest_values(
        &manifest,
        "packet_validation_command",
        &[
            "cargo fmt --all --check",
            "git diff --check",
            "cargo test -p zkbench-core --test gateway_claim_packet_reproduction --quiet",
            "cargo test -p zkbench-core --test repo_hygiene --quiet",
            "cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet",
            "cargo test --workspace --quiet",
            "cargo test --workspace --features external-runner --quiet",
        ],
    );

    assert_contains_all(
        &packet,
        &[
            IGNORED_DEMO_ROOT,
            "!! .gateway-demo-runs/",
            "gateway-acceptance-preview/manifest.json",
            "gateway-acceptance-preview/acceptance-preview-request.json",
            "gateway-acceptance-preview/acceptance-preview-report.json",
            "gateway-acceptance-preview/source-preflight-report.json",
            "gateway-acceptance-preview/non-claims.md",
            "gateway-acceptance-preview/validation-report.json",
            "candidate_only: true",
            "mutates_accepted_evidence_ledger: false",
            "creates_level2_evidence: false",
            "populates_score_axes: false",
            "grants_authority: false",
            "retains_raw_provider_artifacts: false",
            "retains_credentials_or_secrets: false",
        ],
    );

    assert_contains_all(
        &packet,
        &[
            "- accepted evidence;",
            "- final acceptance;",
            "- accepted Evidence Ledger mutation;",
            "- Level2+ evidence;",
            "- live provider evidence;",
            "- live attestation capture;",
            "- benchmark evidence;",
            "- official benchmark submission;",
            "- score-axis population;",
            "- live gateway execution;",
            "- live model behavior;",
            "- verifier-agent runtime behavior;",
            "- production readiness;",
            "- semantic correctness;",
            "- SOTA status;",
            "- breakthrough status;",
            "- full security;",
            "- credential handling;",
            "- global software-agent uniqueness;",
            "- any claim above `Attested`.",
        ],
    );
    assert_manifest_values(
        &manifest,
        "nonclaim",
        &[
            "accepted evidence",
            "final acceptance",
            "accepted Evidence Ledger mutation",
            "Level2+ evidence",
            "live provider evidence",
            "live attestation capture",
            "benchmark evidence",
            "score-axis population",
            "production readiness",
            "semantic correctness",
            "SOTA status",
            "breakthrough status",
            "full security",
            "global software-agent uniqueness",
            "any claim above Attested",
        ],
    );

    assert_contains_all(
        &packet,
        &[
            "It is not live provider evidence or accepted production",
            "evidence.",
            "without granting authority",
            "mutating accepted evidence.",
            "HSAI has proven production-ready secure agent execution.",
            "HSAI has accepted live attestation evidence.",
            "HSAI is SOTA.",
            "HSAI has proven a breakthrough.",
            "HSAI has Level2+ evidence.",
            "HSAI is fully secure.",
        ],
    );
    assert_manifest_values(
        &manifest,
        "do_not_use",
        &[
            "HSAI has proven production-ready secure agent execution.",
            "HSAI has accepted live attestation evidence.",
            "HSAI is SOTA.",
            "HSAI has proven a breakthrough.",
            "HSAI has Level2+ evidence.",
            "HSAI is fully secure.",
        ],
    );

    let gitignore = read(&repo_root.join(".gitignore"));
    assert!(
        gitignore.lines().any(|line| line.trim() == "/.gateway-demo-runs/"),
        "Phase 254 packet documents an ignored demo root, but .gitignore no longer ignores .gateway-demo-runs/"
    );

    let readme = read(&repo_root.join("README.md"));
    assert_contains_all(
        &readme,
        &[
            PACKET_PATH,
            "Phase 254 HSAI Gateway bridge bounded public claim packet.",
        ],
    );

    let task_list = read(&repo_root.join("docs/12-task-list.md"));
    assert_contains_all(
        &task_list,
        &[
            "## Phase 254 HSAI Gateway Bridge Public Claim Packet",
            "`docs/254-hsai-gateway-bridge-public-claim-packet.md`",
            "Status: complete.",
        ],
    );

    let validation_report = read(&repo_root.join("docs/90-whole-codebase-validation-report.md"));
    assert_contains_all(
        &validation_report,
        &[
            "Phase 254 packages Phases 249 through 253 into",
            "local claim-packet reproduction checker",
        ],
    );

    let agents = read(&repo_root.join("AGENTS.md"));
    assert_contains_all(
        &agents,
        &[
            "Explicit Phase 254 HSAI gateway bridge public claim packet now allowed and completed",
            "It does not permit Rust/source changes, generated output, accepted Evidence Ledger mutation",
        ],
    );
}

#[test]
fn claim_packet_manifest_rejects_malformed_local_packet_examples() {
    let repo_root = repo_root();
    let packet = read(&repo_root.join(PACKET_PATH));

    assert_parse_error(
        "missing manifest fence",
        &packet.replace(MANIFEST_FENCE, "```text"),
        "missing claim-packet-manifest-v1 fence",
    );

    let unterminated = format!("{MANIFEST_FENCE}\npacket_id=unterminated\n");
    assert_parse_error(
        "unterminated manifest fence",
        &unterminated,
        "unterminated claim-packet-manifest-v1 fence",
    );

    assert_parse_error(
        "malformed manifest line",
        &packet.replace(
            "packet_path=docs/254-hsai-gateway-bridge-public-claim-packet.md",
            "packet_path docs/254-hsai-gateway-bridge-public-claim-packet.md",
        ),
        "manifest line should use key=value format",
    );

    assert_parse_error(
        "empty manifest key",
        &packet.replace(
            "packet_id=phase-254-hsai-gateway-bridge-public-claim-packet",
            "=phase-254-hsai-gateway-bridge-public-claim-packet",
        ),
        "manifest key should not be empty",
    );

    assert_parse_error(
        "empty manifest value",
        &packet.replace(
            "claim_level=local_metadata_and_artifact_shape_only",
            "claim_level=",
        ),
        "manifest value should not be empty",
    );

    assert_contract_error(
        "maturity drift",
        &packet.replace("max_claim_maturity=Attested", "max_claim_maturity=Proven"),
        "manifest singleton mismatch for max_claim_maturity",
    );

    assert_contract_error(
        "missing focused checker command",
        &packet.replace(
            "packet_validation_command=cargo test -p zkbench-core --test gateway_claim_packet_reproduction --quiet\n",
            "",
        ),
        "manifest repeated-value mismatch for packet_validation_command",
    );

    assert_contract_error(
        "nonclaim drift",
        &packet.replace("nonclaim=full security", "nonclaim=production security"),
        "manifest repeated-value mismatch for nonclaim",
    );
}

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .expect("crate should live under repo_root/crates/zkbench-core")
        .to_path_buf()
}

fn read(path: &Path) -> String {
    fs::read_to_string(path).unwrap_or_else(|error| {
        panic!("failed to read {}: {error}", path.display());
    })
}

fn assert_contains_all(text: &str, needles: &[&str]) {
    let missing: Vec<&str> = needles
        .iter()
        .copied()
        .filter(|needle| !text.contains(needle))
        .collect();
    assert!(missing.is_empty(), "missing expected text: {missing:?}");
}

fn parse_manifest(packet: &str) -> Result<BTreeMap<String, Vec<String>>, String> {
    let (_, rest) = packet
        .split_once(MANIFEST_FENCE)
        .ok_or_else(|| "missing claim-packet-manifest-v1 fence".to_string())?;
    let (manifest_body, _) = rest
        .split_once("```")
        .ok_or_else(|| "unterminated claim-packet-manifest-v1 fence".to_string())?;

    let mut manifest = BTreeMap::<String, Vec<String>>::new();
    for line in manifest_body
        .lines()
        .map(str::trim)
        .filter(|line| !line.is_empty())
    {
        let (key, value) = line
            .split_once('=')
            .ok_or_else(|| format!("manifest line should use key=value format: {line}"))?;
        if key.is_empty() {
            return Err("manifest key should not be empty".to_string());
        }
        if value.is_empty() {
            return Err(format!("manifest value should not be empty for {key}"));
        }
        manifest
            .entry(key.to_string())
            .or_default()
            .push(value.to_string());
    }
    Ok(manifest)
}

fn validate_manifest_contract(manifest: &BTreeMap<String, Vec<String>>) -> Result<(), String> {
    expect_manifest_singletons(
        manifest,
        &[
            (
                "packet_id",
                "phase-254-hsai-gateway-bridge-public-claim-packet",
            ),
            ("packet_path", PACKET_PATH),
            ("base_commit", PACKET_BASE_COMMIT),
            (
                "top_commit",
                "edbae44 Materialize gateway acceptance preview bundle",
            ),
            ("claim_level", "local_metadata_and_artifact_shape_only"),
            ("max_claim_maturity", "Attested"),
            ("ignored_demo_root", IGNORED_DEMO_ROOT),
            ("ignored_status", "!! .gateway-demo-runs/"),
        ],
    )?;
    expect_manifest_values(
        manifest,
        "validated_phase",
        &["249", "250", "251", "252", "253"],
    )?;
    expect_manifest_values(
        manifest,
        "declared_file",
        &[
            "gateway-acceptance-preview/manifest.json",
            "gateway-acceptance-preview/acceptance-preview-request.json",
            "gateway-acceptance-preview/acceptance-preview-report.json",
            "gateway-acceptance-preview/source-preflight-report.json",
            "gateway-acceptance-preview/non-claims.md",
            "gateway-acceptance-preview/validation-report.json",
        ],
    )?;
    expect_manifest_values(
        manifest,
        "summary_flag",
        &[
            "candidate_only:true",
            "mutates_accepted_evidence_ledger:false",
            "creates_level2_evidence:false",
            "populates_score_axes:false",
            "grants_authority:false",
            "retains_raw_provider_artifacts:false",
            "retains_credentials_or_secrets:false",
        ],
    )?;
    expect_manifest_values(
        manifest,
        "phase253_command",
        &[
            "cargo fmt --all --check",
            "git diff --check",
            "cargo test -p hsai-agent-admission --lib gateway_acceptance_preview_bundle",
            "cargo test -p hsai-agent-admission --test gateway_acceptance_preview_bundle_contract",
            "cargo check -p hsai-agent-admission --examples",
            "cargo run -p hsai-agent-admission --example gateway_acceptance_preview_bundle",
            "cargo test -p hsai-agent-admission --lib --quiet",
            "cargo test -p zkbench-core --test repo_hygiene --quiet",
            "cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet",
            "cargo test --workspace --quiet",
            "cargo test --workspace --features external-runner --quiet",
        ],
    )?;
    expect_manifest_values(
        manifest,
        "packet_validation_command",
        &[
            "cargo fmt --all --check",
            "git diff --check",
            "cargo test -p zkbench-core --test gateway_claim_packet_reproduction --quiet",
            "cargo test -p zkbench-core --test repo_hygiene --quiet",
            "cargo test -p zkbench-core --test repo_claim_boundary_docs --quiet",
            "cargo test --workspace --quiet",
            "cargo test --workspace --features external-runner --quiet",
        ],
    )?;
    expect_manifest_values(
        manifest,
        "nonclaim",
        &[
            "accepted evidence",
            "final acceptance",
            "accepted Evidence Ledger mutation",
            "Level2+ evidence",
            "live provider evidence",
            "live attestation capture",
            "benchmark evidence",
            "score-axis population",
            "production readiness",
            "semantic correctness",
            "SOTA status",
            "breakthrough status",
            "full security",
            "global software-agent uniqueness",
            "any claim above Attested",
        ],
    )?;
    expect_manifest_values(
        manifest,
        "do_not_use",
        &[
            "HSAI has proven production-ready secure agent execution.",
            "HSAI has accepted live attestation evidence.",
            "HSAI is SOTA.",
            "HSAI has proven a breakthrough.",
            "HSAI has Level2+ evidence.",
            "HSAI is fully secure.",
        ],
    )?;
    Ok(())
}

fn assert_manifest_singletons(manifest: &BTreeMap<String, Vec<String>>, expected: &[(&str, &str)]) {
    expect_manifest_singletons(manifest, expected)
        .expect("manifest singleton contract should hold");
}

fn assert_manifest_values(manifest: &BTreeMap<String, Vec<String>>, key: &str, expected: &[&str]) {
    expect_manifest_values(manifest, key, expected)
        .expect("manifest repeated-value contract should hold");
}

fn expect_manifest_singletons(
    manifest: &BTreeMap<String, Vec<String>>,
    expected: &[(&str, &str)],
) -> Result<(), String> {
    for (key, expected_value) in expected {
        let values = manifest
            .get(*key)
            .ok_or_else(|| format!("manifest missing key {key}"))?;
        if values.as_slice() != [*expected_value] {
            return Err(format!(
                "manifest singleton mismatch for {key}: expected {:?}, got {:?}",
                &[*expected_value],
                values
            ));
        }
    }
    Ok(())
}

fn expect_manifest_values(
    manifest: &BTreeMap<String, Vec<String>>,
    key: &str,
    expected: &[&str],
) -> Result<(), String> {
    let values = manifest
        .get(key)
        .ok_or_else(|| format!("manifest missing repeated key {key}"))?;
    let expected_values: Vec<String> = expected.iter().map(|value| (*value).to_string()).collect();
    if values != &expected_values {
        return Err(format!(
            "manifest repeated-value mismatch for {key}: expected {expected_values:?}, got {values:?}"
        ));
    }
    Ok(())
}

fn assert_parse_error(case: &str, packet: &str, expected_message: &str) {
    let error = parse_manifest(packet).expect_err(case);
    assert!(
        error.contains(expected_message),
        "{case} should contain {expected_message:?}, got {error:?}"
    );
}

fn assert_contract_error(case: &str, packet: &str, expected_message: &str) {
    let manifest = parse_manifest(packet).unwrap_or_else(|error| {
        panic!("{case} should parse before contract validation, got {error}");
    });
    let error = validate_manifest_contract(&manifest).expect_err(case);
    assert!(
        error.contains(expected_message),
        "{case} should contain {expected_message:?}, got {error:?}"
    );
}

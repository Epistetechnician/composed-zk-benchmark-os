use std::fs;
use std::path::Path;

use tempfile::tempdir;
use zkbench_core::{
    build_default_artifact_capture_contract, build_default_external_result_import_schema,
    build_default_external_runner_policy, build_default_provenance_contract,
    build_local_replay_manifest_for_instance, build_zk_harness_dry_run_plan_from_pack,
    build_zk_harness_manual_handoff_bundle, generate_instance, run_local_replay,
    BenchmarkPackReader, BenchmarkPackWriter, ClaimBoundary, EvidenceLedger, GeneratorConfig,
    InstanceParams,
};

fn dry_run_plan() -> zkbench_core::ZkHarnessDryRunPlan {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(107),
        InstanceParams::default(),
    )
    .expect("baseline instance should generate");
    let manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    let result = run_local_replay(&manifest).expect("local replay should run");
    let mut ledger = EvidenceLedger::new();
    ledger
        .append_replay_result(&result)
        .expect("ledger append should work");

    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_h_claim_boundary_pack")
        .with_generated_instance(instance)
        .with_replay_manifest(manifest)
        .with_replay_result(result)
        .with_evidence_ledger(ledger)
        .write_to(dir.path())
        .expect("pack should write");
    let reader = BenchmarkPackReader::read(dir.path()).expect("pack should read");
    build_zk_harness_dry_run_plan_from_pack(&reader).expect("dry-run plan should build")
}

#[test]
fn phase_h_artifacts_do_not_produce_level2_actual_evidence() {
    let policy = build_default_external_runner_policy();
    let capture = build_default_artifact_capture_contract();
    let provenance = build_default_provenance_contract();
    let schema = build_default_external_result_import_schema();
    let handoff =
        build_zk_harness_manual_handoff_bundle(&dry_run_plan()).expect("handoff should build");

    assert_eq!(policy.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(capture.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(provenance.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(schema.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(handoff.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(
        handoff.handoff_bundle.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
}

#[test]
fn local_pack_evidence_remains_level1_when_referenced() {
    let plan = dry_run_plan();
    let handoff = build_zk_harness_manual_handoff_bundle(&plan).expect("handoff should build");

    assert_eq!(
        plan.subject.local_pack_claim_boundary,
        ClaimBoundary::Level1LocalReplay
    );
    assert_eq!(
        handoff.handoff_bundle.subject.local_pack_claim_boundary,
        ClaimBoundary::Level1LocalReplay
    );
    assert_eq!(
        handoff.mapping.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
}

#[test]
fn generated_phase_h_artifacts_do_not_contain_official_acceptance_language() {
    let handoff =
        build_zk_harness_manual_handoff_bundle(&dry_run_plan()).expect("handoff should build");
    let json = serde_json::to_string(&handoff).expect("handoff should serialize");

    let forbidden_status = ["AcceptedAsOfficial", "BenchmarkEvidence"].concat();
    assert!(!json.contains(&forbidden_status));
    assert!(!json.contains("accepted as official"));
    assert!(!json.contains("prover_time"));
    assert!(!json.contains("verifier_time"));
    assert!(!json.contains("proof_size"));
}

#[test]
fn source_contains_no_process_command_api_or_live_public_methods() {
    let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let mut source = read_source_tree(&manifest_dir.join("src/external_runner"));
    source.push_str(
        &fs::read_to_string(manifest_dir.join("src/adapters/zk_harness/handoff.rs"))
            .expect("zk-Harness handoff source should be readable"),
    );

    assert!(!source.contains("std::process::Command"));
    assert!(!source.contains("Command::new"));
    assert!(!source.contains("pub fn run_"));
    assert!(!source.contains("pub fn execute_"));
    assert!(!source.contains("pub fn spawn_"));
    assert!(!source.contains("pub fn invoke_"));
}

fn read_source_tree(root: &Path) -> String {
    let mut combined = String::new();
    read_source_tree_into(root, &mut combined);
    combined
}

fn read_source_tree_into(path: &Path, combined: &mut String) {
    if path.is_file() {
        if path.extension().and_then(|extension| extension.to_str()) == Some("rs") {
            let text = fs::read_to_string(path).expect("source file should be readable");
            combined.push_str(&text);
            combined.push('\n');
        }
        return;
    }
    for entry in fs::read_dir(path).expect("source directory should be readable") {
        let entry = entry.expect("source directory entry should be readable");
        read_source_tree_into(&entry.path(), combined);
    }
}

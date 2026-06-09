use tempfile::tempdir;
use zkbench_core::{
    build_local_replay_manifest_for_instance, build_manual_handoff_bundle_from_zk_harness_plan,
    build_zk_harness_dry_run_plan_from_pack, deserialize_manual_handoff_bundle_json,
    generate_instance, run_local_replay, serialize_manual_handoff_bundle_json,
    validate_manual_handoff_bundle, BenchmarkPackReader, BenchmarkPackWriter, ClaimBoundary,
    EvidenceLedger, ExternalExecutionMode, GeneratorConfig, InstanceParams,
};

fn dry_run_plan() -> zkbench_core::ZkHarnessDryRunPlan {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(101),
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
    BenchmarkPackWriter::new("phase_h_manual_handoff_pack")
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
fn manual_handoff_bundle_builds_from_valid_dry_run_plan() {
    let plan = dry_run_plan();
    let bundle = build_manual_handoff_bundle_from_zk_harness_plan(&plan)
        .expect("manual handoff should build");

    assert_eq!(bundle.subject.dry_run_plan_id, plan.id);
    assert_eq!(bundle.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert!(bundle.contains_manual_instructions_only());
    assert!(!bundle.allows_live_execution());
    assert_eq!(
        bundle.artifact_capture_contract.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert_eq!(
        bundle.provenance_contract.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert_eq!(
        bundle.result_import_schema.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );

    let validation = validate_manual_handoff_bundle(&bundle);
    assert!(
        validation.valid,
        "validation errors: {:?}",
        validation.issues
    );
}

#[test]
fn manual_handoff_bundle_round_trips_and_contains_no_shell_or_absolute_paths() {
    let plan = dry_run_plan();
    let bundle = build_manual_handoff_bundle_from_zk_harness_plan(&plan)
        .expect("manual handoff should build");
    let json = serialize_manual_handoff_bundle_json(&bundle).expect("bundle should serialize");
    let parsed = deserialize_manual_handoff_bundle_json(&json).expect("bundle should deserialize");
    let json_again =
        serialize_manual_handoff_bundle_json(&parsed).expect("bundle should serialize again");

    assert_eq!(bundle, parsed);
    assert_eq!(json, json_again);
    assert!(!json.contains("#!/"));
    assert!(!json.contains("/Users/"));
    assert!(!json.contains("/tmp/"));
    assert!(!json.contains("Command::new"));
}

#[test]
fn manual_handoff_validation_fails_if_live_execution_is_requested() {
    let plan = dry_run_plan();
    let mut bundle = build_manual_handoff_bundle_from_zk_harness_plan(&plan)
        .expect("manual handoff should build");
    bundle.external_runner_policy.mode = ExternalExecutionMode::FutureLiveExecutionNotImplemented;

    let validation = validate_manual_handoff_bundle(&bundle);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.message.contains("live execution")));
}

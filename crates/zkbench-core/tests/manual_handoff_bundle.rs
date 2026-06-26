use tempfile::tempdir;
use zkbench_core::{
    build_local_replay_manifest_for_instance, build_manual_handoff_bundle_from_zk_harness_plan,
    build_zk_harness_dry_run_plan_from_pack, deserialize_manual_handoff_bundle_json,
    generate_instance, run_local_replay, serialize_manual_handoff_bundle_json,
    validate_manual_handoff_bundle, BenchmarkPackReader, BenchmarkPackWriter, ClaimBoundary,
    EvidenceLedger, ExternalExecutionMode, GeneratorConfig, InstanceParams,
    ManualHandoffValidation,
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

#[test]
fn manual_handoff_validation_rejects_nested_contract_boundary_elevation() {
    let plan = dry_run_plan();
    let mut bundle = build_manual_handoff_bundle_from_zk_harness_plan(&plan)
        .expect("manual handoff should build");
    bundle.artifact_capture_contract.claim_boundary = ClaimBoundary::Level1LocalReplay;

    let validation = validate_manual_handoff_bundle(&bundle);

    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.path.contains("artifact_capture_contract") && issue.path.contains("claim_boundary")
    }));
}

#[test]
fn manual_handoff_validation_rejects_bundle_subject_and_empty_steps() {
    let plan = dry_run_plan();
    let mut bundle = build_manual_handoff_bundle_from_zk_harness_plan(&plan)
        .expect("manual handoff should build");
    bundle.id = "  ".to_string();
    bundle.claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    bundle.subject.dry_run_plan_id.clear();
    bundle.subject.source_benchmark_pack_id = "  ".to_string();
    bundle.subject.local_pack_claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    bundle.steps.clear();

    let validation = validate_manual_handoff_bundle(&bundle);

    assert!(!validation.valid);
    assert_issue_path(&validation, "bundle.id");
    assert_issue_path(&validation, "bundle.claim_boundary");
    assert_issue_path(&validation, "bundle.subject.dry_run_plan_id");
    assert_issue_path(&validation, "bundle.subject.source_benchmark_pack_id");
    assert_issue_path(&validation, "bundle.subject.local_pack_claim_boundary");
    assert_issue_path(&validation, "bundle.steps");
}

#[test]
fn manual_handoff_validation_rejects_step_instruction_drift() {
    let plan = dry_run_plan();
    let mut bundle = build_manual_handoff_bundle_from_zk_harness_plan(&plan)
        .expect("manual handoff should build");
    let step = bundle
        .steps
        .first_mut()
        .expect("manual handoff should include steps");
    step.id = " ".to_string();
    step.instruction.manual_only = false;
    step.instruction.title = "../escape".to_string();
    step.instruction.detail = "copy && execute".to_string();
    step.instruction.inert_planned_program_name = Some("/usr/bin/zk-harness".to_string());
    step.instruction.inert_arguments = vec!["alpha || beta".to_string()];
    step.instruction.artifact_refs = vec!["../pack/manifest.json".to_string()];

    let validation = validate_manual_handoff_bundle(&bundle);

    assert!(!validation.valid);
    assert_issue_path(&validation, "bundle.steps[0].id");
    assert_issue_path(&validation, "bundle.steps[0].instruction.manual_only");
    assert_issue_path(&validation, "bundle.steps[0].instruction.title");
    assert_issue_path(&validation, "bundle.steps[0].instruction.detail");
    assert_issue_path(
        &validation,
        "bundle.steps[0].instruction.inert_planned_program_name",
    );
    assert_issue_path(
        &validation,
        "bundle.steps[0].instruction.inert_arguments[0]",
    );
    assert_issue_path(&validation, "bundle.steps[0].instruction.artifact_refs[0]");
}

#[test]
fn manual_handoff_validation_rejects_export_shape_drift() {
    let plan = dry_run_plan();
    let mut bundle = build_manual_handoff_bundle_from_zk_harness_plan(&plan)
        .expect("manual handoff should build");
    bundle.export.id.clear();
    bundle.export.relative_uri = "/tmp/manual-handoff.json".to_string();
    bundle.export.claim_boundary = ClaimBoundary::Level1LocalReplay;

    let validation = validate_manual_handoff_bundle(&bundle);

    assert!(!validation.valid);
    assert_issue_path(&validation, "bundle.export.id");
    assert_issue_path(&validation, "bundle.export.relative_uri");
    assert_issue_path(&validation, "bundle.export.claim_boundary");
}

#[test]
fn manual_handoff_validation_rejects_nested_provenance_and_import_schema_drift() {
    let plan = dry_run_plan();
    let mut bundle = build_manual_handoff_bundle_from_zk_harness_plan(&plan)
        .expect("manual handoff should build");
    bundle.provenance_contract.id.clear();
    bundle.provenance_contract.claim_boundary = ClaimBoundary::Level1LocalReplay;
    bundle.provenance_contract.required_fields.clear();
    bundle.result_import_schema.id = " ".to_string();
    bundle.result_import_schema.claim_boundary = ClaimBoundary::Level1LocalReplay;
    bundle
        .result_import_schema
        .required_provenance_fields
        .clear();

    let validation = validate_manual_handoff_bundle(&bundle);

    assert!(!validation.valid);
    assert_issue_path(&validation, "bundle.provenance_contract.contract.id");
    assert_issue_path(
        &validation,
        "bundle.provenance_contract.contract.claim_boundary",
    );
    assert!(validation.issues.iter().any(|issue| {
        issue
            .path
            .starts_with("bundle.provenance_contract.contract.required_fields.")
    }));
    assert_issue_path(&validation, "bundle.result_import_schema.schema.id");
    assert_issue_path(
        &validation,
        "bundle.result_import_schema.schema.claim_boundary",
    );
    assert!(validation.issues.iter().any(|issue| {
        issue
            .path
            .starts_with("bundle.result_import_schema.schema.required_provenance_fields.")
    }));
}

#[test]
fn manual_handoff_manual_only_check_requires_valid_step_validation() {
    let plan = dry_run_plan();
    let mut bundle = build_manual_handoff_bundle_from_zk_harness_plan(&plan)
        .expect("manual handoff should build");
    let step = bundle
        .steps
        .first_mut()
        .expect("manual handoff should include steps");
    step.validation.valid = false;

    assert!(!bundle.contains_manual_instructions_only());
}

#[test]
fn manual_handoff_manual_only_check_requires_manual_only_steps() {
    let plan = dry_run_plan();
    let mut bundle = build_manual_handoff_bundle_from_zk_harness_plan(&plan)
        .expect("manual handoff should build");
    let step = bundle
        .steps
        .first_mut()
        .expect("manual handoff should include steps");
    step.instruction.manual_only = false;

    assert!(!bundle.contains_manual_instructions_only());
}

fn assert_issue_path(validation: &ManualHandoffValidation, path: &str) {
    assert!(
        validation.issues.iter().any(|issue| issue.path == path),
        "expected validation issue at {path}, got {:?}",
        validation.issues
    );
}

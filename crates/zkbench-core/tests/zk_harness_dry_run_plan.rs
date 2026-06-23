use tempfile::tempdir;
use zkbench_core::{
    build_local_replay_manifest_for_instance, build_zk_harness_dry_run_plan_from_pack,
    deserialize_zk_harness_dry_run_plan_json, generate_instance, run_local_replay,
    serialize_zk_harness_dry_run_plan_json, validate_zk_harness_dry_run_plan, BenchmarkPackReader,
    BenchmarkPackWriter, ClaimBoundary, EvidenceLedger, GeneratorConfig, InstanceParams,
    ZkHarnessExecutionPolicy, ZkHarnessPlanStepKind,
};

fn local_pack_reader() -> (tempfile::TempDir, BenchmarkPackReader) {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(71),
        InstanceParams::default(),
    )
    .expect("baseline instance should generate");
    let manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    let result = run_local_replay(&manifest).expect("local replay should run");
    let mut ledger = EvidenceLedger::new();
    ledger
        .append_replay_result(&result)
        .expect("local evidence should append");

    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_g_minimal_pack")
        .with_generated_instance(instance)
        .with_replay_manifest(manifest)
        .with_replay_result(result)
        .with_evidence_ledger(ledger)
        .write_to(dir.path())
        .expect("local pack should write");
    let reader = BenchmarkPackReader::read(dir.path()).expect("pack reader should load");
    (dir, reader)
}

fn validation_error_paths(plan: &zkbench_core::ZkHarnessDryRunPlan) -> Vec<String> {
    validate_zk_harness_dry_run_plan(plan)
        .errors
        .into_iter()
        .map(|issue| issue.path)
        .collect()
}

fn assert_has_path(paths: &[String], expected: &str) {
    assert!(
        paths.iter().any(|path| path == expected),
        "missing path {expected}; got {paths:?}"
    );
}

#[test]
fn dry_run_plan_builds_serializes_and_validates() {
    let (_dir, reader) = local_pack_reader();
    let plan = build_zk_harness_dry_run_plan_from_pack(&reader)
        .expect("dry-run plan should build from local pack");

    assert_eq!(
        plan.execution_policy,
        ZkHarnessExecutionPolicy::DisabledByDefault
    );
    assert_eq!(plan.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert!(plan.contains_no_executable_process());
    assert!(plan.planned_commands().iter().all(|command| command.inert));

    let kinds = plan
        .planned_steps
        .iter()
        .map(|step| step.kind)
        .collect::<Vec<_>>();
    assert!(kinds.contains(&ZkHarnessPlanStepKind::PrepareInputs));
    assert!(kinds.contains(&ZkHarnessPlanStepKind::CompileCircuit));
    assert!(kinds.contains(&ZkHarnessPlanStepKind::GenerateWitness));
    assert!(kinds.contains(&ZkHarnessPlanStepKind::Prove));
    assert!(kinds.contains(&ZkHarnessPlanStepKind::Verify));
    assert!(kinds.contains(&ZkHarnessPlanStepKind::CollectMetrics));
    assert!(kinds.contains(&ZkHarnessPlanStepKind::NormalizeResults));

    let validation = validate_zk_harness_dry_run_plan(&plan);
    assert!(
        validation.valid,
        "validation errors: {:?}",
        validation.errors
    );

    let json =
        serialize_zk_harness_dry_run_plan_json(&plan).expect("plan should serialize to JSON");
    let parsed = deserialize_zk_harness_dry_run_plan_json(&json).expect("plan should deserialize");
    let json_again = serialize_zk_harness_dry_run_plan_json(&parsed)
        .expect("plan should serialize deterministically");
    assert_eq!(plan, parsed);
    assert_eq!(json, json_again);
}

#[test]
fn dry_run_validation_rejects_live_policy_elevated_claims_and_fake_metrics() {
    let (_dir, reader) = local_pack_reader();
    let plan = build_zk_harness_dry_run_plan_from_pack(&reader).expect("dry-run plan should build");

    let mut live = plan.clone();
    live.execution_policy = ZkHarnessExecutionPolicy::FutureLiveExecution;
    assert!(!validate_zk_harness_dry_run_plan(&live).valid);

    let mut elevated = plan.clone();
    elevated.claim_boundary = ClaimBoundary::Level1LocalReplay;
    assert!(!validate_zk_harness_dry_run_plan(&elevated).valid);

    let mut fake_metric = plan;
    fake_metric.metric_mappings[0].observed_value = Some("1".to_string());
    assert!(!validate_zk_harness_dry_run_plan(&fake_metric).valid);
}

#[test]
fn dry_run_validation_reports_fail_closed_paths_for_plan_drift() {
    let (_dir, reader) = local_pack_reader();
    let plan = build_zk_harness_dry_run_plan_from_pack(&reader).expect("dry-run plan should build");

    let mut missing_ids = plan.clone();
    missing_ids.id.clear();
    missing_ids.adapter_manifest_id.clear();
    missing_ids.source_benchmark_pack_id.clear();
    let missing_id_paths = validation_error_paths(&missing_ids);
    assert_has_path(&missing_id_paths, "plan.id");
    assert_has_path(&missing_id_paths, "plan.adapter_manifest_id");
    assert_has_path(&missing_id_paths, "plan.source_benchmark_pack_id");

    let mut unsupported = plan.clone();
    unsupported.unsupported_features.clear();
    let unsupported_validation = validate_zk_harness_dry_run_plan(&unsupported);
    assert!(unsupported_validation.valid);
    assert_eq!(
        unsupported_validation.warnings[0].path,
        "plan.unsupported_features"
    );

    let mut metric = plan.clone();
    metric.metric_mappings[0].planned_only = false;
    metric.metric_mappings[0].observed_value = Some("benchmark pass".to_string());
    let metric_paths = validation_error_paths(&metric);
    assert_has_path(&metric_paths, "plan.metric_mappings[0].planned_only");
    assert_has_path(&metric_paths, "plan.metric_mappings[0].observed_value");
    assert_has_path(&metric_paths, "plan");

    let mut command = plan.clone();
    command.planned_steps[0].dry_run_only = false;
    command.planned_steps[0].planned_command.inert = false;
    command.planned_steps[0]
        .planned_command
        .display_program_name = "bash".to_string();
    command.planned_steps[0]
        .planned_command
        .working_directory_policy = "../repo".to_string();
    command.planned_steps[0].planned_command.arguments[0].inert = false;
    command.planned_steps[0].planned_command.arguments[0].value = "$HOME".to_string();
    command.planned_steps[0].planned_command.environment[0].inert = false;
    command.planned_steps[0].planned_command.environment[0].value = "A|B".to_string();
    command.planned_steps[0].planned_command.input_artifacts[0].relative_uri =
        "..\\pack.json".to_string();
    let command_paths = validation_error_paths(&command);
    assert_has_path(&command_paths, "plan.planned_steps[0].dry_run_only");
    assert_has_path(&command_paths, "plan.planned_steps[0].planned_command");
    assert_has_path(
        &command_paths,
        "plan.planned_steps[0].planned_command.display_program_name",
    );
    assert_has_path(
        &command_paths,
        "plan.planned_steps[0].planned_command.working_directory_policy",
    );
    assert_has_path(
        &command_paths,
        "plan.planned_steps[0].planned_command.arguments[0].inert",
    );
    assert_has_path(
        &command_paths,
        "plan.planned_steps[0].planned_command.arguments[0].value",
    );
    assert_has_path(
        &command_paths,
        "plan.planned_steps[0].planned_command.environment[0].inert",
    );
    assert_has_path(
        &command_paths,
        "plan.planned_steps[0].planned_command.environment[0].value",
    );
    assert_has_path(
        &command_paths,
        "plan.planned_steps[0].planned_command.input_artifacts[0].relative_uri",
    );

    let mut mapping = plan.clone();
    mapping.pack_mapping.artifact_mappings[0].local_only = false;
    mapping.pack_mapping.artifact_mappings[0].source_relative_path = "/tmp/file".to_string();
    mapping.pack_mapping.artifact_mappings[0]
        .source_digest
        .byte_len = 0;
    mapping.pack_mapping.family_mappings[0].candidate_workload_label =
        "wrong-family-label".to_string();
    mapping.pack_mapping.trace_mappings[0].local_only = false;
    mapping
        .notes
        .push("official benchmark evidence".to_string());
    let mapping_paths = validation_error_paths(&mapping);
    assert_has_path(
        &mapping_paths,
        "plan.pack_mapping.artifact_mappings[0].local_only",
    );
    assert_has_path(
        &mapping_paths,
        "plan.pack_mapping.artifact_mappings[0].source_relative_path",
    );
    assert_has_path(
        &mapping_paths,
        "plan.pack_mapping.artifact_mappings[0].source_digest",
    );
    assert_has_path(&mapping_paths, "plan.pack_mapping.family_mappings[0]");
    assert_has_path(
        &mapping_paths,
        "plan.pack_mapping.trace_mappings[0].local_only",
    );
    assert_has_path(&mapping_paths, "plan");
}

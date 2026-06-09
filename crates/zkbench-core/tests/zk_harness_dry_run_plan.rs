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

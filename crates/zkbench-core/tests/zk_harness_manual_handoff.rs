use tempfile::tempdir;
use zkbench_core::{
    build_local_replay_manifest_for_instance, build_zk_harness_dry_run_plan_from_pack,
    build_zk_harness_manual_handoff_bundle, generate_instance, run_local_replay,
    BenchmarkPackReader, BenchmarkPackWriter, ClaimBoundary, EvidenceLedger, GeneratorConfig,
    InstanceParams, ManualHandoffStepKind, ZkHarnessFutureExecutionPrerequisite,
};

fn dry_run_plan() -> zkbench_core::ZkHarnessDryRunPlan {
    let instance = generate_instance(
        GeneratorConfig::bounded_counter_loop()
            .seed(103)
            .loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded counter instance should generate");
    let manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    let result = run_local_replay(&manifest).expect("local replay should run");
    let mut ledger = EvidenceLedger::new();
    ledger
        .append_replay_result(&result)
        .expect("ledger append should work");

    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_h_zk_harness_handoff_pack")
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
fn dry_run_plan_maps_to_manual_handoff_bundle() {
    let plan = dry_run_plan();
    let handoff =
        build_zk_harness_manual_handoff_bundle(&plan).expect("handoff bundle should build");

    assert_eq!(handoff.mapping.dry_run_plan_id, plan.id);
    assert_eq!(
        handoff.mapping.source_benchmark_pack_id,
        plan.source_benchmark_pack_id
    );
    assert_eq!(handoff.mapping.source_pack_digest, plan.source_pack_digest);
    assert_eq!(
        handoff.mapping.source_artifact_digests,
        plan.pack_mapping
            .artifact_mappings
            .iter()
            .map(|artifact| artifact.source_digest.clone())
            .collect::<Vec<_>>()
    );
    assert_eq!(handoff.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert!(!handoff.emits_zk_harness_result);
}

#[test]
fn planned_commands_become_manual_instructions_and_prerequisites_are_present() {
    let plan = dry_run_plan();
    let handoff =
        build_zk_harness_manual_handoff_bundle(&plan).expect("handoff bundle should build");
    let manual_tool_steps = handoff
        .handoff_bundle
        .steps
        .iter()
        .filter(|step| step.kind == ManualHandoffStepKind::RunExternalToolManually)
        .count();

    assert_eq!(manual_tool_steps, plan.planned_steps.len());
    assert!(handoff
        .handoff_bundle
        .steps
        .iter()
        .all(|step| step.instruction.manual_only));
    assert!(handoff
        .future_execution_prerequisites
        .contains(&ZkHarnessFutureExecutionPrerequisite::VerifyOfficialZkHarnessSchemaSource));
    assert!(handoff
        .future_execution_prerequisites
        .contains(&ZkHarnessFutureExecutionPrerequisite::RunOnlyWithExplicitFutureApproval));
}

#[test]
fn local_replay_result_is_not_converted_to_zk_harness_result() {
    let plan = dry_run_plan();
    let handoff =
        build_zk_harness_manual_handoff_bundle(&plan).expect("handoff bundle should build");
    let json = serde_json::to_string(&handoff).expect("handoff should serialize");

    assert!(!handoff.emits_zk_harness_result);
    assert!(json.contains("Local replay results are not converted"));
    let forbidden_status = ["AcceptedAsOfficial", "BenchmarkEvidence"].concat();
    assert!(!json.contains(&forbidden_status));
    assert!(!json.contains("proof-system acceptance"));
}

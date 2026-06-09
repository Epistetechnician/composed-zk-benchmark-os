use tempfile::tempdir;
use zkbench_core::{
    build_local_replay_manifest_for_instance, build_zk_harness_dry_run_plan_from_pack,
    generate_instance, run_local_replay, serialize_zk_harness_dry_run_plan_json,
    BenchmarkPackReader, BenchmarkPackWriter, ClaimBoundary, EvidenceLedger, GeneratorConfig,
    InstanceParams,
};

#[test]
fn dry_run_plan_does_not_elevate_local_pack_evidence() {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(91),
        InstanceParams::default(),
    )
    .expect("baseline should generate");
    let manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    let result = run_local_replay(&manifest).expect("local replay should run");
    let mut ledger = EvidenceLedger::new();
    ledger
        .append_replay_result(&result)
        .expect("local evidence should append");

    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_g_claim_pack")
        .with_generated_instance(instance)
        .with_replay_manifest(manifest)
        .with_replay_result(result)
        .with_evidence_ledger(ledger)
        .write_to(dir.path())
        .expect("pack should write");
    let reader = BenchmarkPackReader::read(dir.path()).expect("pack should load");
    assert_eq!(
        reader.manifest().claim_boundary,
        ClaimBoundary::Level1LocalReplay
    );

    let plan = build_zk_harness_dry_run_plan_from_pack(&reader).expect("dry-run plan should build");
    assert_eq!(plan.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(
        plan.subject.local_pack_claim_boundary,
        ClaimBoundary::Level1LocalReplay
    );
    assert_eq!(
        plan.evidence_mapping.current_phase_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(!plan.evidence_mapping.emits_evidence_records);
    assert!(plan
        .metric_mappings
        .iter()
        .all(|metric| metric.observed_value.is_none()));

    let json =
        serialize_zk_harness_dry_run_plan_json(&plan).expect("plan should serialize to JSON");
    assert!(!json.contains("benchmark pass"));
    assert!(!json.contains("official benchmark evidence"));
    assert!(!json.contains("BackendOutcome::Accepted"));
}

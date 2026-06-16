use tempfile::tempdir;
use zkbench_core::{
    attach_reproduction_bundle_to_pack, build_local_replay_manifest_for_instance,
    generate_instance, run_local_replay, BenchmarkPackReader, BenchmarkPackWriter, ClaimBoundary,
    EvidenceLedger, GeneratorConfig, InstanceParams,
};

#[test]
fn attach_reproduction_bundle_adds_inert_external_plans() {
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
        .expect("replay evidence should append");

    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_m_reproduction_pack")
        .with_generated_instance(instance)
        .with_replay_manifest(manifest)
        .with_replay_result(result)
        .with_evidence_ledger(ledger)
        .write_to(dir.path())
        .expect("pack should write");

    let metadata =
        attach_reproduction_bundle_to_pack(dir.path()).expect("reproduction attach should work");
    let reader = BenchmarkPackReader::read(dir.path()).expect("reader should load pack");

    assert_eq!(metadata.attachments.len(), 3);
    assert!(metadata.attachments_are_inert());
    assert_eq!(metadata.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert!(!metadata.level2_eligibility.eligible);
    assert_eq!(
        reader.manifest().claim_boundary,
        ClaimBoundary::Level1LocalReplay
    );
    assert_eq!(reader.manifest().summary.external_replay_plan_count, 3);
    assert_eq!(reader.manifest().summary.reproduction_metadata_count, 1);
    assert!(reader.validate().valid);
}

#[test]
fn reproduction_attach_is_idempotent_by_rejection() {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(72),
        InstanceParams::default(),
    )
    .expect("baseline instance should generate");
    let manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    let result = run_local_replay(&manifest).expect("local replay should run");
    let mut ledger = EvidenceLedger::new();
    ledger
        .append_replay_result(&result)
        .expect("replay evidence should append");

    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_m_reproduction_pack_twice")
        .with_generated_instance(instance)
        .with_replay_manifest(manifest)
        .with_replay_result(result)
        .with_evidence_ledger(ledger)
        .write_to(dir.path())
        .expect("pack should write");

    attach_reproduction_bundle_to_pack(dir.path()).expect("first attach should work");
    assert!(attach_reproduction_bundle_to_pack(dir.path()).is_err());
}

#[test]
fn reproduction_metadata_round_trips_deterministically() {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(73),
        InstanceParams::default(),
    )
    .expect("baseline instance should generate");
    let manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    let result = run_local_replay(&manifest).expect("local replay should run");
    let mut ledger = EvidenceLedger::new();
    ledger
        .append_replay_result(&result)
        .expect("replay evidence should append");

    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_m_reproduction_roundtrip")
        .with_generated_instance(instance)
        .with_replay_manifest(manifest)
        .with_replay_result(result)
        .with_evidence_ledger(ledger)
        .write_to(dir.path())
        .expect("pack should write");

    let metadata =
        attach_reproduction_bundle_to_pack(dir.path()).expect("reproduction attach should work");
    let reader = BenchmarkPackReader::read(dir.path()).expect("reader should load pack");
    let loaded = reader
        .load_reproduction_metadata()
        .expect("metadata should load")
        .expect("metadata should exist");

    assert_eq!(metadata, loaded);
}

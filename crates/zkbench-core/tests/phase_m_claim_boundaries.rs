use tempfile::tempdir;
use zkbench_core::{
    attach_reproduction_bundle_to_pack, build_local_replay_manifest_for_instance,
    generate_instance, run_local_replay, BenchmarkPackReader, BenchmarkPackWriter, ClaimBoundary,
    EvidenceLedger, GeneratorConfig, InstanceParams,
};

#[test]
fn reproduction_attach_does_not_promote_pack_or_ledger_to_level2() {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(81),
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
    BenchmarkPackWriter::new("phase_m_claim_boundary_pack")
        .with_generated_instance(instance)
        .with_replay_manifest(manifest)
        .with_replay_result(result)
        .with_evidence_ledger(ledger.clone())
        .write_to(dir.path())
        .expect("pack should write");

    let metadata =
        attach_reproduction_bundle_to_pack(dir.path()).expect("reproduction attach should work");
    let reader = BenchmarkPackReader::read(dir.path()).expect("reader should load pack");
    let loaded_ledger = reader
        .load_evidence_ledger()
        .expect("ledger should load")
        .expect("ledger should exist");

    assert_eq!(
        reader.manifest().claim_boundary,
        ClaimBoundary::Level1LocalReplay
    );
    assert_eq!(metadata.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(
        metadata.level2_eligibility.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(!metadata.level2_eligibility.eligible);
    assert_eq!(loaded_ledger.entries.len(), ledger.entries.len());
    assert!(loaded_ledger.validate().valid);
}

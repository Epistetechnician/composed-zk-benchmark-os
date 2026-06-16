use tempfile::tempdir;
use zkbench_core::{
    attach_reproduction_bundle_to_pack, build_local_replay_manifest_for_instance,
    generate_instance, run_local_replay, BenchmarkPackReader, BenchmarkPackWriter,
    EvidenceLedger, GeneratorConfig, InstanceParams, Level2EligibilityBlockingReason,
    Level2EligibilityStatus,
};

#[test]
fn level2_eligibility_remains_blocked_without_reviewed_external_artifacts() {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(91),
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
    BenchmarkPackWriter::new("phase_m_level2_eligibility_pack")
        .with_generated_instance(instance)
        .with_replay_manifest(manifest)
        .with_replay_result(result)
        .with_evidence_ledger(ledger)
        .write_to(dir.path())
        .expect("pack should write");

    let metadata =
        attach_reproduction_bundle_to_pack(dir.path()).expect("reproduction attach should work");
    let reader = BenchmarkPackReader::read(dir.path()).expect("reader should load pack");
    let report = metadata.level2_eligibility;

    assert!(!report.eligible);
    assert_eq!(report.status, Level2EligibilityStatus::Blocked);
    assert!(report.blocking_reasons.contains(
        &Level2EligibilityBlockingReason::MissingReviewedExternalResultCandidate
    ));
    assert!(report
        .blocking_reasons
        .contains(&Level2EligibilityBlockingReason::MissingReproducibleExternalArtifacts));
    assert!(report
        .blocking_reasons
        .contains(&Level2EligibilityBlockingReason::PhaseJBlocksLevel2ActualEvidence));
    assert!(reader.validate().valid);
}

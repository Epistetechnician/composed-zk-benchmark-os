use std::fs;

use tempfile::tempdir;
use zkbench_core::{
    attach_reproduction_bundle_to_pack, build_failure_corpus_entry, generate_instance,
    read_reproduction_bundle_from_pack, validate_reproduction_bundle, BenchmarkPackWriter,
    ClaimBoundary, FailureCorpusEntryInput, FailureCorpusKind, FamilyKind, GeneratorConfig,
    GeneratorTunables, InstanceParams, MutationClass, ReproductionBundle, SoakShardId,
};

fn sample_entry(case_id: &str) -> zkbench_core::FailureCorpusEntry {
    build_failure_corpus_entry(FailureCorpusEntryInput {
        shard_id: SoakShardId::from_index(0),
        case_id: case_id.to_string(),
        family_kind: FamilyKind::BaselineFsm,
        generator_seed: 7,
        tunables: GeneratorTunables::default(),
        mutation_class: Some(MutationClass::MissingConstraints),
        trace_id: None,
        failure_kind: FailureCorpusKind::ReplayFailure,
        local_error_summary: "simulated replay failure".to_string(),
    })
}

fn bundle_with_entries(entries: Vec<zkbench_core::FailureCorpusEntry>) -> ReproductionBundle {
    ReproductionBundle {
        bundle_id: "phase_188_bundle".to_string(),
        bundle_version: "phase-l-reproduction-bundle-v0".to_string(),
        pack_id: "phase_188_pack".to_string(),
        entries,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: Vec::new(),
    }
}

fn write_sample_pack(root: &std::path::Path, pack_id: &str) {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(11),
        InstanceParams::default(),
    )
    .expect("instance should generate");
    BenchmarkPackWriter::new(pack_id)
        .with_generated_instance(instance)
        .include_score_report(false)
        .write_to(root)
        .expect("pack should write");
}

#[test]
fn reproduction_bundle_validation_rejects_boundary_elevation() {
    let mut bundle = bundle_with_entries(vec![sample_entry("case_boundary")]);
    bundle.claim_boundary = ClaimBoundary::Level1LocalReplay;

    let error =
        validate_reproduction_bundle(&bundle).expect_err("elevated bundle should be rejected");

    assert!(error.to_string().contains("claim_boundary"));
    assert!(error.to_string().contains("Level0DesignNote"));
}

#[test]
fn reproduction_bundle_validation_rejects_empty_entry_id() {
    let mut entry = sample_entry("case_empty_entry");
    entry.entry_id.clear();
    let bundle = bundle_with_entries(vec![entry]);

    let error =
        validate_reproduction_bundle(&bundle).expect_err("empty entry id should be rejected");

    assert!(error.to_string().contains("entries[0].entry_id"));
    assert!(error.to_string().contains("entry id is empty"));
}

#[test]
fn reproduction_bundle_validation_rejects_entry_boundary_elevation() {
    let mut entry = sample_entry("case_entry_boundary");
    entry.claim_boundary = ClaimBoundary::Level1LocalReplay;
    let bundle = bundle_with_entries(vec![entry]);

    let error = validate_reproduction_bundle(&bundle)
        .expect_err("elevated entry boundary should be rejected");

    assert!(error.to_string().contains("entries[0].claim_boundary"));
    assert!(error.to_string().contains("Level0DesignNote"));

    let mut entry = sample_entry("case_manifest_boundary");
    entry.reproduction_manifest.claim_boundary = ClaimBoundary::Level1LocalReplay;
    let bundle = bundle_with_entries(vec![entry]);

    let error = validate_reproduction_bundle(&bundle)
        .expect_err("elevated reproduction manifest boundary should be rejected");

    assert!(error.to_string().contains("entries[0].claim_boundary"));
    assert!(error.to_string().contains("Level0DesignNote"));
}

#[test]
fn attach_reproduction_bundle_reports_pack_validation_failure_after_sidecar_write() {
    let dir = tempdir().expect("tempdir should be available");
    write_sample_pack(dir.path(), "phase_188_invalid_after_attachment");
    fs::write(
        dir.path().join("README.md"),
        "local reproduction aid\nmodified after manifest digest\n",
    )
    .expect("pack readme should be mutable in tempdir");

    let error = attach_reproduction_bundle_to_pack(dir.path(), &[sample_entry("case_tampered")])
        .expect_err("digest-invalid pack should fail post-attachment validation");

    assert!(error.to_string().contains("pack_validation"));
    assert!(error.to_string().contains("digest mismatch"));
}

#[test]
fn read_reproduction_bundle_reports_malformed_sidecar_json() {
    let dir = tempdir().expect("tempdir should be available");
    write_sample_pack(dir.path(), "phase_188_malformed_sidecar");
    attach_reproduction_bundle_to_pack(dir.path(), &[sample_entry("case_malformed")])
        .expect("bundle should attach before corruption");
    fs::write(
        dir.path().join("reproduction/reproduction_bundle.json"),
        b"{not valid json",
    )
    .expect("sidecar should be mutable in tempdir");

    let error = read_reproduction_bundle_from_pack(dir.path())
        .expect_err("malformed sidecar should fail deserialization");

    assert!(error
        .to_string()
        .contains("read_reproduction_bundle_from_pack"));
}

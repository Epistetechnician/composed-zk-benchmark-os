use std::fs;

use tempfile::tempdir;
use zkbench_core::{
    apply_mutation_pass, build_local_replay_manifest_for_instance,
    build_local_replay_manifest_for_mutation, compute_artifact_digest_bytes, generate_instance,
    run_local_replay, serialize_replay_manifest_json, ArtifactKind, ArtifactRole, BadCountersPass,
    BenchmarkPackReader, BenchmarkPackWriter, EvidenceLedger, GeneratorConfig, InstanceParams,
};

#[test]
fn same_inputs_write_byte_identical_local_packs() {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(59),
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

    let left = tempdir().expect("left tempdir should be available");
    let right = tempdir().expect("right tempdir should be available");

    let left_manifest = BenchmarkPackWriter::new("phase_f_reproducible_pack")
        .with_generated_instance(instance.clone())
        .with_replay_manifest(manifest.clone())
        .with_replay_result(result.clone())
        .with_evidence_ledger(ledger.clone())
        .write_to(left.path())
        .expect("left pack should write");
    let right_manifest = BenchmarkPackWriter::new("phase_f_reproducible_pack")
        .with_generated_instance(instance)
        .with_replay_manifest(manifest)
        .with_replay_result(result)
        .with_evidence_ledger(ledger)
        .write_to(right.path())
        .expect("right pack should write");

    assert_eq!(left_manifest, right_manifest);
    for relative_path in ["pack.json", "README.md", "evidence/ledger.json"] {
        let left_bytes = fs::read(left.path().join(relative_path))
            .expect("left artifact bytes should be readable");
        let right_bytes = fs::read(right.path().join(relative_path))
            .expect("right artifact bytes should be readable");
        assert_eq!(
            left_bytes, right_bytes,
            "{relative_path} should be byte-identical"
        );
    }

    let reader = BenchmarkPackReader::read(left.path()).expect("reader should load left pack");
    assert!(reader.manifest().uses_relative_paths_only());
    assert!(reader.validate().valid);
}

#[test]
fn generated_mutated_and_manifest_json_are_deterministic() {
    let left_instance = generate_instance(
        GeneratorConfig::bounded_counter_loop()
            .seed(61)
            .loop_bound(3),
        InstanceParams::default(),
    )
    .expect("left instance should generate");
    let right_instance = generate_instance(
        GeneratorConfig::bounded_counter_loop()
            .seed(61)
            .loop_bound(3),
        InstanceParams::default(),
    )
    .expect("right instance should generate");
    let left_mutation =
        apply_mutation_pass(&left_instance, &BadCountersPass).expect("left mutation should apply");
    let right_mutation = apply_mutation_pass(&right_instance, &BadCountersPass)
        .expect("right mutation should apply");
    let left_manifest = build_local_replay_manifest_for_mutation(&left_mutation)
        .expect("left manifest should build");
    let right_manifest = build_local_replay_manifest_for_mutation(&right_mutation)
        .expect("right manifest should build");

    assert_eq!(
        serde_json::to_string_pretty(&left_instance).expect("left instance should serialize"),
        serde_json::to_string_pretty(&right_instance).expect("right instance should serialize")
    );
    assert_eq!(
        serde_json::to_string_pretty(&left_mutation).expect("left mutation should serialize"),
        serde_json::to_string_pretty(&right_mutation).expect("right mutation should serialize")
    );
    assert_eq!(
        serialize_replay_manifest_json(&left_manifest).expect("left manifest should serialize"),
        serialize_replay_manifest_json(&right_manifest).expect("right manifest should serialize")
    );
}

#[test]
fn artifact_digests_are_byte_deterministic_and_content_sensitive() {
    let left = compute_artifact_digest_bytes(
        b"{\"stable\":true}",
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Digest),
    );
    let right = compute_artifact_digest_bytes(
        b"{\"stable\":true}",
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Digest),
    );
    let changed = compute_artifact_digest_bytes(
        b"{\"stable\":false}",
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Digest),
    );

    assert_eq!(left, right);
    assert_ne!(left.hex_digest, changed.hex_digest);
    assert_eq!(left.byte_len, b"{\"stable\":true}".len());
}

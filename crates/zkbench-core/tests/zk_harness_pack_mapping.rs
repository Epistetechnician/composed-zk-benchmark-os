use std::fs;

use tempfile::tempdir;
use zkbench_core::{
    adapters::zk_harness::mapping::{
        candidate_family_label, candidate_mutation_label, map_pack_reader_to_zk_harness,
    },
    apply_mutation_pass, build_default_zk_harness_adapter_manifest,
    build_local_replay_manifest_for_instance, build_zk_harness_dry_run_plan_from_pack,
    compute_artifact_digest_bytes, deserialize_zk_harness_dry_run_plan_json,
    deserialize_zk_harness_manifest_json, export_pack_to_zk_harness_dry_run_plan,
    generate_instance, run_local_replay, serialize_zk_harness_dry_run_plan_json,
    serialize_zk_harness_manifest_json, BadCountersPass, BenchmarkPackFileRole,
    BenchmarkPackManifest, BenchmarkPackReader, BenchmarkPackWriter, CorruptedGuardsPass,
    EvidenceLedger, ExpectedVerdict, FamilyKind, GeneratorConfig, InstanceParams,
    InvalidUnrollBoundsPass, MissingConstraintsPass, MutationClass,
};

fn write_pack_manifest(root: &std::path::Path, manifest: &BenchmarkPackManifest) {
    let json = serde_json::to_string_pretty(manifest).expect("pack manifest should serialize");
    fs::write(root.join("pack.json"), json).expect("pack manifest should be writable");
}

fn write_single_generated_pack(
    pack_id: &str,
    mut instance: zkbench_core::GeneratedBenchmarkInstance,
) -> tempfile::TempDir {
    instance.id = format!("{pack_id}_instance");
    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new(pack_id)
        .with_generated_instance(instance)
        .write_to(dir.path())
        .expect("generated pack should write");
    dir
}

#[test]
fn pack_mapping_preserves_ids_digests_and_candidate_labels() {
    let baseline = generate_instance(
        GeneratorConfig::baseline_fsm().seed(81),
        InstanceParams::default(),
    )
    .expect("baseline should generate");
    let branching = generate_instance(
        GeneratorConfig::branching_fsm().seed(83),
        InstanceParams::default(),
    )
    .expect("branching should generate");
    let bounded = generate_instance(
        GeneratorConfig::bounded_counter_loop()
            .seed(85)
            .loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded should generate");

    let missing = apply_mutation_pass(&branching, &MissingConstraintsPass)
        .expect("missing constraints should apply");
    let corrupted =
        apply_mutation_pass(&bounded, &CorruptedGuardsPass).expect("corrupted guards should apply");
    let bad = apply_mutation_pass(&bounded, &BadCountersPass).expect("bad counters should apply");

    let replay_manifest = build_local_replay_manifest_for_instance(&baseline)
        .expect("baseline manifest should build");
    let replay_result = run_local_replay(&replay_manifest).expect("local replay should run");
    let mut ledger = EvidenceLedger::new();
    ledger
        .append_replay_result(&replay_result)
        .expect("local replay evidence should append");

    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_g_mapping_pack")
        .with_generated_instance(baseline)
        .with_generated_instance(branching)
        .with_generated_instance(bounded)
        .with_mutated_instance(missing)
        .with_mutated_instance(corrupted)
        .with_mutated_instance(bad)
        .with_replay_manifest(replay_manifest)
        .with_replay_result(replay_result)
        .with_evidence_ledger(ledger)
        .write_to(dir.path())
        .expect("mapping pack should write");

    let reader = BenchmarkPackReader::read(dir.path()).expect("pack reader should load");
    let plan = build_zk_harness_dry_run_plan_from_pack(&reader).expect("dry-run plan should build");
    let mapping = &plan.pack_mapping;

    assert_eq!(mapping.source_pack_id, "phase_g_mapping_pack");
    assert_eq!(mapping.source_pack_id, reader.manifest().id);
    assert_eq!(
        mapping.artifact_mappings.len(),
        reader.manifest().files.len()
    );
    for artifact in &mapping.artifact_mappings {
        let source = reader
            .manifest()
            .files
            .iter()
            .find(|file| file.relative_path == artifact.source_relative_path)
            .expect("artifact mapping should preserve source file");
        assert_eq!(artifact.source_digest, source.digest);
        assert!(artifact.local_only);
    }

    let family_labels = mapping
        .family_mappings
        .iter()
        .map(|mapping| mapping.candidate_workload_label.as_str())
        .collect::<Vec<_>>();
    assert!(family_labels.contains(&"control_flow_baseline_fsm"));
    assert!(family_labels.contains(&"control_flow_branching_fsm"));
    assert!(family_labels.contains(&"control_flow_bounded_counter_loop"));

    let mutation_labels = mapping
        .mutation_mappings
        .iter()
        .map(|mapping| {
            (
                mapping.source_mutation_class,
                mapping.candidate_negative_test_label.as_str(),
            )
        })
        .collect::<Vec<_>>();
    assert!(mutation_labels.contains(&(
        MutationClass::MissingConstraints,
        "missing_constraints_negative_case"
    )));
    assert!(mutation_labels.contains(&(
        MutationClass::CorruptedGuards,
        "corrupted_guards_negative_case"
    )));
    assert!(mutation_labels.contains(&(MutationClass::BadCounters, "bad_counters_negative_case")));

    assert!(mapping
        .expected_outcome_mappings
        .iter()
        .any(|outcome| outcome.expected_verdict == ExpectedVerdict::Accept));
    assert!(mapping
        .expected_outcome_mappings
        .iter()
        .any(|outcome| outcome.expected_verdict == ExpectedVerdict::Reject));
    assert!(mapping
        .expected_outcome_mappings
        .iter()
        .any(|outcome| outcome.expected_verdict == ExpectedVerdict::UnsoundIfAccepted));

    assert_eq!(
        mapping.local_replay_result_refs,
        reader.manifest().replay_result_ids
    );
    assert!(mapping.artifact_mappings.iter().any(|artifact| {
        artifact.source_role == BenchmarkPackFileRole::ReplayResult && artifact.local_only
    }));
}

#[test]
fn candidate_label_helpers_cover_current_registry() {
    assert_eq!(
        candidate_family_label(FamilyKind::RecursiveEnvelope),
        Some("control_flow_recursive_envelope")
    );
    assert_eq!(
        candidate_family_label(FamilyKind::MemoryHeavyStateMachine),
        Some("control_flow_memory_heavy_state_machine")
    );
    assert_eq!(
        candidate_family_label(FamilyKind::PublicPrivateBoundaryStress),
        Some("control_flow_public_private_boundary_stress")
    );
    assert_eq!(
        candidate_family_label(FamilyKind::ZkMlControlFlowMixed),
        Some("control_flow_zkml_control_flow_mixed")
    );

    assert_eq!(
        candidate_mutation_label(MutationClass::InvalidUnrollBounds),
        None
    );
    assert_eq!(
        candidate_mutation_label(MutationClass::TraceOrderingCorruption),
        None
    );
}

#[test]
fn pack_mapping_rejects_invalid_source_pack_before_mapping() {
    let baseline = generate_instance(
        GeneratorConfig::baseline_fsm().seed(101),
        InstanceParams::default(),
    )
    .expect("baseline should generate");
    let dir = write_single_generated_pack("phase_g_invalid_source_pack", baseline);
    fs::remove_file(dir.path().join("evidence/ledger.json"))
        .expect("required evidence ledger should be removable");

    let reader = BenchmarkPackReader::read(dir.path()).expect("pack reader should load");
    let error = map_pack_reader_to_zk_harness(&reader)
        .expect_err("invalid source pack should fail before mapping");

    assert!(error.to_string().contains("source pack validation failed"));
}

#[test]
fn pack_mapping_reports_malformed_generated_instance_payload() {
    let baseline = generate_instance(
        GeneratorConfig::baseline_fsm().seed(103),
        InstanceParams::default(),
    )
    .expect("baseline should generate");
    let dir = write_single_generated_pack("phase_g_malformed_payload_pack", baseline);
    let malformed = b"{not generated instance json";
    fs::write(dir.path().join("specs/generated_instance.json"), malformed)
        .expect("generated instance should be rewritable");

    let mut manifest = BenchmarkPackReader::read(dir.path())
        .expect("pack reader should load before manifest repair")
        .manifest()
        .clone();
    let generated_file = manifest
        .files
        .iter_mut()
        .find(|file| file.role == BenchmarkPackFileRole::GeneratedInstance)
        .expect("generated file should be listed");
    generated_file.digest = compute_artifact_digest_bytes(
        malformed,
        Some(generated_file.role.artifact_kind()),
        Some(generated_file.role.artifact_role()),
    );
    write_pack_manifest(dir.path(), &manifest);

    let reader = BenchmarkPackReader::read(dir.path()).expect("repaired pack reader should load");
    assert!(
        reader.validate().valid,
        "digest-repaired pack should reach mapping payload parsing"
    );
    let error =
        map_pack_reader_to_zk_harness(&reader).expect_err("malformed generated JSON should fail");

    assert!(error.to_string().contains("specs/generated_instance.json"));
}

#[test]
fn pack_mapping_reports_malformed_mutated_instance_payload() {
    let bounded = generate_instance(
        GeneratorConfig::bounded_counter_loop()
            .seed(104)
            .loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded instance should generate");
    let mutation =
        apply_mutation_pass(&bounded, &BadCountersPass).expect("bad-counter mutation should apply");

    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_g_malformed_mutation_payload_pack")
        .with_generated_instance(bounded)
        .with_mutated_instance(mutation)
        .write_to(dir.path())
        .expect("pack with mutation should write");
    let malformed = b"{not mutated instance json";

    let mut manifest = BenchmarkPackReader::read(dir.path())
        .expect("pack reader should load before manifest repair")
        .manifest()
        .clone();
    let mutated_file = manifest
        .files
        .iter_mut()
        .find(|file| file.role == BenchmarkPackFileRole::MutatedInstance)
        .expect("mutated file should be listed");
    fs::write(dir.path().join(&mutated_file.relative_path), malformed)
        .expect("mutated instance should be rewritable");
    mutated_file.digest = compute_artifact_digest_bytes(
        malformed,
        Some(mutated_file.role.artifact_kind()),
        Some(mutated_file.role.artifact_role()),
    );
    let mutated_path = mutated_file.relative_path.clone();
    write_pack_manifest(dir.path(), &manifest);

    let reader = BenchmarkPackReader::read(dir.path()).expect("repaired pack reader should load");
    assert!(
        reader.validate().valid,
        "digest-repaired pack should reach mutated payload parsing"
    );
    let error =
        map_pack_reader_to_zk_harness(&reader).expect_err("malformed mutated JSON should fail");

    assert!(error.to_string().contains(&mutated_path));
}

#[test]
fn pack_mapping_reports_missing_optional_generated_instance_payload() {
    let baseline = generate_instance(
        GeneratorConfig::baseline_fsm().seed(105),
        InstanceParams::default(),
    )
    .expect("baseline should generate");
    let dir = write_single_generated_pack("phase_g_missing_optional_payload_pack", baseline);

    let mut manifest = BenchmarkPackReader::read(dir.path())
        .expect("pack reader should load before optional-file mutation")
        .manifest()
        .clone();
    let generated_file = manifest
        .files
        .iter_mut()
        .find(|file| file.role == BenchmarkPackFileRole::GeneratedInstance)
        .expect("generated file should be listed");
    generated_file.required = false;
    fs::remove_file(dir.path().join(&generated_file.relative_path))
        .expect("optional generated instance should be removable");
    write_pack_manifest(dir.path(), &manifest);

    let reader = BenchmarkPackReader::read(dir.path()).expect("mutated pack reader should load");
    assert!(
        reader.validate().valid,
        "optional missing file should pass pack validation before mapping"
    );
    let error =
        map_pack_reader_to_zk_harness(&reader).expect_err("missing mapped payload should fail");

    assert!(error.to_string().contains("specs/generated_instance.json"));
}

#[test]
fn pack_mapping_records_unsupported_mutation_class_warning() {
    let loop_instance = generate_instance(
        GeneratorConfig::bounded_counter_loop()
            .seed(107)
            .loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded loop should generate");
    let unsupported_mutation = apply_mutation_pass(&loop_instance, &InvalidUnrollBoundsPass)
        .expect("invalid-unroll mutation should apply");

    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_g_unsupported_mutation_pack")
        .with_generated_instance(loop_instance)
        .with_mutated_instance(unsupported_mutation)
        .write_to(dir.path())
        .expect("unsupported mutation pack should write");

    let reader = BenchmarkPackReader::read(dir.path()).expect("pack reader should load");
    let mapping =
        map_pack_reader_to_zk_harness(&reader).expect("unsupported mutation should warn only");

    assert!(mapping.mutation_mappings.is_empty());
    assert!(mapping.unsupported_features.iter().any(|feature| {
        feature.id == "mutation_class_InvalidUnrollBounds"
            && feature
                .description
                .contains("no Phase G candidate zk-Harness label")
    }));
    assert!(mapping.warnings.iter().any(|warning| {
        warning
            .message
            .contains("unsupported mutation class for Phase G mapping")
    }));
}

#[test]
fn pack_mapping_preserves_non_default_expected_outcome_labels() {
    let mut instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(109),
        InstanceParams::default(),
    )
    .expect("baseline should generate");
    instance.accepted_traces[0].expected_verdict = Some(ExpectedVerdict::BackendError);
    instance.rejected_traces[0].expected_verdict = Some(ExpectedVerdict::CapabilityGap);
    let mut inconclusive_trace = instance.accepted_traces[0].clone();
    inconclusive_trace.id = "inconclusive_trace".to_string();
    inconclusive_trace.expected_verdict = None;
    instance.accepted_traces.push(inconclusive_trace);

    let dir = write_single_generated_pack("phase_g_expected_outcome_pack", instance);
    let reader = BenchmarkPackReader::read(dir.path()).expect("pack reader should load");
    let mapping = map_pack_reader_to_zk_harness(&reader).expect("mapping should build");
    let outcome_labels = mapping
        .expected_outcome_mappings
        .iter()
        .map(|mapping| mapping.candidate_expected_outcome_label.as_str())
        .collect::<Vec<_>>();

    assert!(outcome_labels.contains(&"expected_backend_error"));
    assert!(outcome_labels.contains(&"expected_capability_gap"));
    assert!(outcome_labels.contains(&"expected_inconclusive"));
}

#[test]
fn zk_harness_export_helpers_roundtrip_and_fail_closed() {
    let baseline = generate_instance(
        GeneratorConfig::baseline_fsm().seed(91),
        InstanceParams::default(),
    )
    .expect("baseline should generate");
    let replay_manifest = build_local_replay_manifest_for_instance(&baseline)
        .expect("baseline manifest should build");
    let replay_result = run_local_replay(&replay_manifest).expect("local replay should run");

    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_g_export_pack")
        .with_generated_instance(baseline)
        .with_replay_manifest(replay_manifest)
        .with_replay_result(replay_result)
        .write_to(dir.path())
        .expect("export pack should write");

    let reader = BenchmarkPackReader::read(dir.path()).expect("pack reader should load");
    let plan = export_pack_to_zk_harness_dry_run_plan(&reader)
        .expect("direct export helper should build a valid dry-run plan");
    assert_eq!(plan.pack_mapping.source_pack_id, "phase_g_export_pack");

    let plan_json = serialize_zk_harness_dry_run_plan_json(&plan).expect("plan should serialize");
    let parsed_plan =
        deserialize_zk_harness_dry_run_plan_json(&plan_json).expect("plan should deserialize");
    assert_eq!(parsed_plan.id, plan.id);
    assert_eq!(
        parsed_plan.pack_mapping.source_pack_id,
        plan.pack_mapping.source_pack_id
    );

    let manifest = build_default_zk_harness_adapter_manifest();
    let manifest_json =
        serialize_zk_harness_manifest_json(&manifest).expect("manifest should serialize");
    let parsed_manifest =
        deserialize_zk_harness_manifest_json(&manifest_json).expect("manifest should deserialize");
    assert_eq!(parsed_manifest.id, manifest.id);
    assert_eq!(parsed_manifest.scope, manifest.scope);

    assert!(deserialize_zk_harness_manifest_json("{not json").is_err());
    assert!(deserialize_zk_harness_dry_run_plan_json("{not json").is_err());
}

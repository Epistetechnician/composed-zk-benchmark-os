use tempfile::tempdir;
use zkbench_core::{
    apply_mutation_pass, build_local_replay_manifest_for_instance,
    build_zk_harness_dry_run_plan_from_pack, generate_instance, run_local_replay, BadCountersPass,
    BenchmarkPackFileRole, BenchmarkPackReader, BenchmarkPackWriter, CorruptedGuardsPass,
    EvidenceLedger, ExpectedVerdict, GeneratorConfig, InstanceParams, MissingConstraintsPass,
    MutationClass,
};

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

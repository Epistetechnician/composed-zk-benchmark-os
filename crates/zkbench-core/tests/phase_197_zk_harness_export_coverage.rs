use tempfile::tempdir;
use zkbench_core::{
    build_local_replay_manifest_for_instance, build_zk_harness_dry_run_plan_from_pack,
    export_pack_to_zk_harness_dry_run_plan, generate_instance, run_local_replay,
    BenchmarkPackReader, BenchmarkPackWriter, EvidenceLedger, GeneratorConfig, InstanceParams,
};

fn local_pack_reader_with_id(pack_id: &str) -> (tempfile::TempDir, BenchmarkPackReader) {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(197),
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
    BenchmarkPackWriter::new(pack_id)
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
fn build_helper_delegates_to_direct_export_for_safe_pack() {
    let (_dir, reader) = local_pack_reader_with_id("phase_197_safe_export_pack");

    let direct = export_pack_to_zk_harness_dry_run_plan(&reader)
        .expect("direct export helper should build a dry-run plan");
    let delegated = build_zk_harness_dry_run_plan_from_pack(&reader)
        .expect("delegating build helper should build the same dry-run plan");

    assert_eq!(delegated, direct);
    assert_eq!(delegated.pack_mapping.source_pack_id, reader.manifest().id);
    assert_eq!(
        delegated.pack_mapping.export_manifest.dry_run_plan_id,
        Some(delegated.id.clone())
    );
}

#[test]
fn export_rejects_source_pack_id_that_breaks_dry_run_validation() {
    let (_dir, reader) = local_pack_reader_with_id("phase_197$unsafe_export_pack");

    let pack_validation = reader.validate();
    assert!(
        pack_validation.valid,
        "source pack should be locally valid before zk-Harness export: {:?}",
        pack_validation.errors
    );

    let error = export_pack_to_zk_harness_dry_run_plan(&reader)
        .expect_err("unsafe source pack id should fail dry-run export validation")
        .to_string();

    assert!(error.contains("zk_harness.dry_run_plan.validation"));
    assert!(error.contains("dry-run plan validation failed"));
    assert!(error.contains("shell metacharacter payload is not allowed"));
    assert!(error.contains("planned_command.arguments[1].value"));
}

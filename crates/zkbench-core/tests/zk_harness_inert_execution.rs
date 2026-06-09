use std::fs;

use tempfile::tempdir;
use zkbench_core::{
    build_local_replay_manifest_for_instance, build_zk_harness_dry_run_plan_from_pack,
    generate_instance, run_local_replay, validate_zk_harness_dry_run_plan, BenchmarkPackReader,
    BenchmarkPackWriter, EvidenceLedger, GeneratorConfig, InstanceParams,
};

fn dry_run_plan() -> zkbench_core::ZkHarnessDryRunPlan {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(101),
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
    BenchmarkPackWriter::new("phase_g_inert_pack")
        .with_generated_instance(instance)
        .with_replay_manifest(manifest)
        .with_replay_result(result)
        .with_evidence_ledger(ledger)
        .write_to(dir.path())
        .expect("pack should write");
    let reader = BenchmarkPackReader::read(dir.path()).expect("pack should load");
    build_zk_harness_dry_run_plan_from_pack(&reader).expect("dry-run plan should build")
}

#[test]
fn planned_commands_are_serializable_inert_data_only() {
    let plan = dry_run_plan();
    assert!(plan.contains_no_executable_process());
    for command in plan.planned_commands() {
        assert!(command.inert);
        assert_eq!(command.display_program_name, "zk-harness");
        assert!(!command.display_program_name.starts_with('/'));
        assert!(!command.display_program_name.contains(';'));
        assert!(command.arguments.iter().all(|argument| argument.inert));
        assert!(command
            .environment
            .iter()
            .all(|environment| environment.inert));
    }
}

#[test]
fn validation_rejects_shell_fragments_and_absolute_paths() {
    let mut shell_fragment = dry_run_plan();
    shell_fragment.planned_steps[0].planned_command.arguments[0].value =
        "dry_run_plan;rm".to_string();
    assert!(!validate_zk_harness_dry_run_plan(&shell_fragment).valid);

    let mut absolute_path = dry_run_plan();
    absolute_path.planned_steps[0]
        .planned_command
        .input_artifacts[0]
        .relative_uri = "/tmp/not-relative".to_string();
    assert!(!validate_zk_harness_dry_run_plan(&absolute_path).valid);
}

#[test]
fn zk_harness_adapter_source_exposes_no_process_execution_api() {
    let manifest_dir = env!("CARGO_MANIFEST_DIR");
    let source_dir = format!("{manifest_dir}/src/adapters/zk_harness");
    let mut combined = String::new();
    for entry in fs::read_dir(source_dir).expect("zk_harness source dir should be readable") {
        let entry = entry.expect("source dir entry should be readable");
        if entry
            .path()
            .extension()
            .and_then(|extension| extension.to_str())
            == Some("rs")
        {
            combined.push_str(
                &fs::read_to_string(entry.path()).expect("source file should be readable"),
            );
        }
    }

    assert!(!combined.contains("std::process::Command"));
    assert!(!combined.contains("Command::new"));
    assert!(!combined.contains("fn execute"));
    assert!(!combined.contains("fn run("));
    assert!(!combined.contains("fn spawn"));
    assert!(!combined.contains("fn invoke"));
}

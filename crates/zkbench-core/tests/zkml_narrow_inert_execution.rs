use std::fs;

use zkbench_core::{
    build_zkml_narrow_workload_plan, validate_zkml_narrow_workload_plan, ZkmlNarrowExecutionPolicy,
};

#[test]
fn planned_commands_are_serializable_inert_data_only() {
    let plan = build_zkml_narrow_workload_plan().expect("workload plan should build");
    assert!(plan.contains_no_executable_process());
    for command in plan.planned_commands() {
        assert!(command.inert);
        assert_eq!(command.display_program_name, "zkml-workload-runner");
        assert!(!command.display_program_name.starts_with('/'));
        assert!(!command.display_program_name.contains(';'));
    }
}

#[test]
fn validation_rejects_future_live_execution_policy() {
    let mut plan = build_zkml_narrow_workload_plan().expect("workload plan should build");
    plan.execution_policy = ZkmlNarrowExecutionPolicy::FutureLiveExecution;
    assert!(!validate_zkml_narrow_workload_plan(&plan).valid);
}

#[test]
fn validation_rejects_absolute_fixture_paths() {
    let mut plan = build_zkml_narrow_workload_plan().expect("workload plan should build");
    plan.scope.relative_fixture_path = "/tmp/zkml_control_flow_mixed.yaml".to_string();
    assert!(!validate_zkml_narrow_workload_plan(&plan).valid);
}

#[test]
fn zkml_narrow_adapter_source_exposes_no_process_execution_api() {
    let manifest_dir = env!("CARGO_MANIFEST_DIR");
    let source_dir = format!("{manifest_dir}/src/adapters/zkml_narrow");
    let mut combined = String::new();
    for entry in fs::read_dir(source_dir).expect("zkml_narrow source dir should be readable") {
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

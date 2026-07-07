const EXAMPLE_SOURCE: &str =
    include_str!("../examples/phase609_real_materialized_staging_runner.rs");

#[test]
fn phase609_staging_runner_uses_declared_environment_contract() {
    for key in [
        "HSAI_PHASE609_ACK",
        "HSAI_PHASE609_OUTPUT_ROOT",
        "HSAI_PHASE609_RUN_ID",
        "HSAI_PHASE609_OPERATOR_ID",
        "HSAI_PHASE609_CREATED_AT_UNIX",
        "HSAI_PHASE609_OVERWRITE",
        "HSAI_PHASE609_Z3_EXECUTABLE",
    ] {
        assert!(
            EXAMPLE_SOURCE.contains(key),
            "example must document env key {key}"
        );
    }
    assert!(
        !EXAMPLE_SOURCE.contains("std::env::args"),
        "phase609 example must not parse CLI args"
    );
}

#[test]
fn phase609_staging_runner_preserves_ignored_output_root_contract() {
    assert!(
        EXAMPLE_SOURCE.contains(".gateway-demo-runs"),
        "phase609 output must be constrained to ignored .gateway-demo-runs root"
    );
    assert!(
        EXAMPLE_SOURCE.contains(
            "read_gateway_formal_tiny_z3_real_materialized_operator_capture_output_bundle"
        ),
        "phase609 runner must read back the materialized Phase 607 bundle"
    );
}

#[test]
fn phase609_staging_runner_executes_only_the_exact_focused_command() {
    assert!(
        EXAMPLE_SOURCE
            .contains("GATEWAY_FORMAL_TINY_Z3_REAL_MATERIALIZED_PHASE604_FOCUSED_COMMAND"),
        "phase609 runner must bind the exact Phase 604 command constant"
    );
    for arg in [
        "\"cargo\"",
        "\"test\"",
        "\"-p\"",
        "\"hsai-agent-admission\"",
        "\"phase604_real_z3_unsat_result_materializes_accepted_ledger_artifact_without_claim_escalation\"",
        "\"--nocapture\"",
    ] {
        assert!(
            EXAMPLE_SOURCE.contains(arg),
            "phase609 runner must include focused command arg {arg}"
        );
    }
}

#[test]
fn phase609_staging_runner_preserves_nonclaims_and_no_raw_log_retention() {
    for phrase in [
        "does not retain raw logs",
        "not accepted evidence",
        "create Level2+ evidence",
        "populate score axes",
        "run Lean",
        "run COBALT",
        "claim semantic correctness",
        "claim production readiness",
        "grant authority",
    ] {
        assert!(
            EXAMPLE_SOURCE.contains(phrase),
            "missing nonclaim phrase: {phrase}"
        );
    }
    assert!(
        !EXAMPLE_SOURCE.contains("fs::write(&observed.stdout_transcript"),
        "phase609 runner must not write raw stdout"
    );
    assert!(
        !EXAMPLE_SOURCE.contains("fs::write(&observed.stderr_transcript"),
        "phase609 runner must not write raw stderr"
    );
}

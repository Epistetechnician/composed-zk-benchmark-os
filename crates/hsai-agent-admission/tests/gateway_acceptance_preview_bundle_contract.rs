const EXAMPLE_SOURCE: &str = include_str!("../examples/gateway_acceptance_preview_bundle.rs");

#[test]
fn gateway_acceptance_preview_bundle_uses_declared_environment_contract() {
    for key in [
        "HSAI_GATEWAY_ACCEPTANCE_PREVIEW_ACK",
        "HSAI_GATEWAY_ACCEPTANCE_PREVIEW_OUTPUT_ROOT",
        "HSAI_GATEWAY_ACCEPTANCE_PREVIEW_BUNDLE_ID",
        "HSAI_GATEWAY_ACCEPTANCE_PREVIEW_CREATED_AT_UNIX",
        "HSAI_GATEWAY_ACCEPTANCE_PREVIEW_OVERWRITE",
    ] {
        assert!(
            EXAMPLE_SOURCE.contains(key),
            "example must document env key {key}"
        );
    }
    assert!(
        !EXAMPLE_SOURCE.contains("std::env::args"),
        "preview example must not parse CLI args"
    );
}

#[test]
fn gateway_acceptance_preview_bundle_preserves_ignored_output_root_contract() {
    assert!(
        EXAMPLE_SOURCE.contains(".gateway-demo-runs"),
        "preview output must be constrained to ignored .gateway-demo-runs root"
    );
    assert!(
        EXAMPLE_SOURCE.contains("gateway-acceptance-preview"),
        "preview demo must materialize the gateway-acceptance-preview bundle"
    );
    assert!(
        EXAMPLE_SOURCE.contains("read_gateway_operator_bridge_acceptance_preview_bundle"),
        "preview demo must read back the materialized bundle"
    );
}

#[test]
fn gateway_acceptance_preview_bundle_preserves_candidate_only_boundary() {
    for phrase in [
        "not final acceptance",
        "not accepted evidence",
        "not production readiness",
        "not semantic correctness",
        "not live provider evidence",
        "not accepted Evidence Ledger mutation",
        "not Level2+ evidence",
        "not benchmark evidence",
        "not authority to execute an action",
    ] {
        assert!(
            EXAMPLE_SOURCE.contains(phrase),
            "missing nonclaim phrase: {phrase}"
        );
    }
    assert!(
        EXAMPLE_SOURCE.contains("candidate_only: true"),
        "preview request must remain candidate-only"
    );
    assert!(
        EXAMPLE_SOURCE.contains("accepted_evidence_mutation_requested: false"),
        "preview request must not request accepted ledger mutation"
    );
}

#[test]
fn gateway_acceptance_preview_bundle_does_not_retain_raw_or_secret_inputs() {
    assert!(
        !EXAMPLE_SOURCE.contains("raw-response.json"),
        "preview demo must not retain raw provider bodies"
    );
    assert!(
        EXAMPLE_SOURCE.contains("retains_raw_provider_artifacts: false"),
        "summary must expose raw artifact retention flag"
    );
    assert!(
        EXAMPLE_SOURCE.contains("retains_credentials_or_secrets: false"),
        "summary must expose credential retention flag"
    );
}

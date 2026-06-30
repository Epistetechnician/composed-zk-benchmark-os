const EXAMPLE_SOURCE: &str = include_str!("../examples/gateway_operator_bridge_bundle.rs");

#[test]
fn gateway_operator_bridge_bundle_uses_declared_environment_contract() {
    for key in [
        "HSAI_GATEWAY_BRIDGE_ACK",
        "HSAI_GATEWAY_BRIDGE_OUTPUT_ROOT",
        "HSAI_GATEWAY_BRIDGE_BUNDLE_ID",
        "HSAI_GATEWAY_BRIDGE_CREATED_AT_UNIX",
        "HSAI_GATEWAY_BRIDGE_OVERWRITE",
    ] {
        assert!(
            EXAMPLE_SOURCE.contains(key),
            "example must document env key {key}"
        );
    }
    assert!(
        !EXAMPLE_SOURCE.contains("std::env::args"),
        "bridge example must not parse CLI args"
    );
}

#[test]
fn gateway_operator_bridge_bundle_preserves_ignored_output_root_contract() {
    assert!(
        EXAMPLE_SOURCE.contains(".gateway-demo-runs"),
        "bridge output must be constrained to ignored .gateway-demo-runs root"
    );
    assert!(
        EXAMPLE_SOURCE.contains("gateway-bridge"),
        "bridge demo must materialize the gateway-bridge bundle"
    );
    assert!(
        EXAMPLE_SOURCE.contains("read_gateway_operator_bridge_bundle"),
        "bridge demo must read back the materialized bundle"
    );
}

#[test]
fn gateway_operator_bridge_bundle_references_repo_external_artifact_only() {
    assert!(
        EXAMPLE_SOURCE.contains("repo_external: true"),
        "operator artifact reference must be repo-external"
    );
    assert!(
        EXAMPLE_SOURCE.contains("operator-live artifact reference only; not accepted evidence"),
        "operator artifact reference must preserve nonclaim boundary"
    );
    assert!(
        !EXAMPLE_SOURCE.contains("raw-response.json"),
        "bridge demo must not retain raw provider bodies"
    );
}

#[test]
fn gateway_operator_bridge_bundle_preserves_nonclaims_and_no_authority() {
    for phrase in [
        "not production readiness",
        "not semantic correctness",
        "not live provider evidence",
        "not accepted Evidence Ledger mutation",
        "not benchmark evidence",
        "not authority to execute an action",
    ] {
        assert!(
            EXAMPLE_SOURCE.contains(phrase),
            "missing nonclaim phrase: {phrase}"
        );
    }
    assert!(
        EXAMPLE_SOURCE.contains("authority_granted"),
        "summary must expose authority flag"
    );
    assert!(
        EXAMPLE_SOURCE.contains("accepted_evidence_mutation"),
        "summary must expose accepted evidence mutation flag"
    );
}

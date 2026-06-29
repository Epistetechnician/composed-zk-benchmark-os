const EXAMPLE_SOURCE: &str = include_str!("../examples/gateway_demo_report.rs");

#[test]
fn gateway_demo_report_uses_only_declared_environment_contract() {
    for key in [
        "HSAI_GATEWAY_DEMO_ACK",
        "HSAI_GATEWAY_DEMO_OUTPUT_ROOT",
        "HSAI_GATEWAY_DEMO_BUNDLE_ID",
        "HSAI_GATEWAY_DEMO_CREATED_AT_UNIX",
        "HSAI_GATEWAY_DEMO_OVERWRITE",
    ] {
        assert!(
            EXAMPLE_SOURCE.contains(key),
            "example must document env key {key}"
        );
    }
    assert!(
        !EXAMPLE_SOURCE.contains("std::env::args"),
        "demo example must not parse CLI args"
    );
}

#[test]
fn gateway_demo_report_preserves_ignored_output_root_contract() {
    assert!(
        EXAMPLE_SOURCE.contains(".gateway-demo-runs"),
        "demo output must be constrained to ignored .gateway-demo-runs root"
    );
    assert!(
        EXAMPLE_SOURCE.contains("gateway-report"),
        "demo must materialize the existing gateway-report bundle"
    );
    assert!(
        EXAMPLE_SOURCE.contains("read_gateway_report_bundle"),
        "demo must read back the materialized bundle"
    );
}

#[test]
fn gateway_demo_report_preserves_nonclaim_language() {
    for phrase in [
        "not production readiness",
        "not semantic correctness",
        "not model execution evidence",
        "not live provider evidence",
        "not accepted Evidence Ledger mutation",
        "not benchmark evidence",
        "not Level2+ evidence",
        "not authority to execute an action",
    ] {
        assert!(
            EXAMPLE_SOURCE.contains(phrase),
            "missing nonclaim phrase: {phrase}"
        );
    }
}

#[test]
fn gateway_demo_report_has_no_authority_grant() {
    assert!(
        EXAMPLE_SOURCE.contains("authority_granted: false"),
        "demo example must preserve authority_granted=false"
    );
    assert!(
        !EXAMPLE_SOURCE.contains("authority_granted: true"),
        "demo example must never grant authority"
    );
}

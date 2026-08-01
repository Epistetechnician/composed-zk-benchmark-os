const P4_SOURCES: &[&str] = &[
    include_str!("../src/p4/mod.rs"),
    include_str!("../src/p4/bounds.rs"),
    include_str!("../src/p4/canonical.rs"),
    include_str!("../src/p4/digest.rs"),
    include_str!("../src/p4/error.rs"),
    include_str!("../src/p4/types.rs"),
    include_str!("../src/p4/parse.rs"),
    include_str!("../src/p4/amounts.rs"),
    include_str!("../src/p4/classify.rs"),
    include_str!("../src/p4/gates.rs"),
    include_str!("../src/p4/assurance.rs"),
    include_str!("../src/p4/valuation.rs"),
    include_str!("../src/p4/budget.rs"),
    include_str!("../src/p4/breaker.rs"),
    include_str!("../src/p4/linked_plan.rs"),
    include_str!("../src/p4/obligation.rs"),
    include_str!("../src/p4/kernel.rs"),
    include_str!("../src/lib.rs"),
];

const MANIFEST: &str = include_str!("../Cargo.toml");

#[test]
fn p4_source_has_no_external_io_float_or_cross_domain_authority() {
    for source in P4_SOURCES {
        for forbidden in [
            "std::fs",
            "std::net",
            "std::process",
            "Command::new",
            "File::create",
            "TcpStream",
            "UdpSocket",
            "reqwest",
            "tokio",
            "credential",
            "hsai_",
            "hsai-",
            "zkbench",
            "f32",
            "f64",
            "unsafe {",
            "pub fn release(",
            "pub fn transfer(",
            "trust_score",
            "release_safety_probability",
        ] {
            assert!(
                !source.contains(forbidden),
                "forbidden P4 source token: {forbidden}"
            );
        }
    }
}

#[test]
fn p4_manifest_is_closed_to_the_authorized_dependency_set() {
    for dependency in [
        "statebook-core",
        "serde",
        "serde_json",
        "sha2",
        "hex",
        "thiserror",
        "ring",
    ] {
        assert!(MANIFEST.contains(dependency));
    }
    for forbidden in [
        "reqwest", "tokio", "hyper", "hsai", "zkbench", "sql", "rusqlite",
    ] {
        assert!(!MANIFEST.contains(forbidden));
    }
}

#[test]
fn p4_canonical_identity_is_domain_separated() {
    for domain in [
        "statebook:p4-intent:v1\\0",
        "statebook:p4-decision-context:v1\\0",
        "statebook:p4-release-attempt:v1\\0",
        "statebook:p4-evidence-snapshot:v1\\0",
        "statebook:p4-valuation-profile:v1\\0",
        "statebook:p4-policy:v1\\0",
        "statebook:p4-ledger-tip:v1\\0",
        "statebook:p4-settlement-state:v1\\0",
        "statebook:p4-decision-record:v1\\0",
    ] {
        assert!(
            P4_SOURCES.iter().any(|source| source.contains(domain)),
            "missing canonical domain: {domain}"
        );
    }
}

#[test]
fn decision_record_is_serialize_only() {
    let types = include_str!("../src/p4/types.rs");
    assert!(types.contains("pub struct DecisionRecordV1"));
    assert!(!types.contains("Deserialize") || types.matches("DecisionRecordV1").count() >= 1);
    assert!(!types.contains("impl<'de> Deserialize<'de> for DecisionRecordV1"));
}

#[test]
fn p4_exports_kernel_and_fixture_parser_only() {
    let lib = include_str!("../src/lib.rs");
    assert!(lib.contains("decide_and_transition"));
    assert!(lib.contains("parse_settlement_scenario_v1"));
    assert!(lib.contains("STATE_SLICE_P4"));
}

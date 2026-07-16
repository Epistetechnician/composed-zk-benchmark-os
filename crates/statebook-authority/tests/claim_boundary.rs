const P7_SOURCES: &[&str] = &[
    include_str!("../src/lib.rs"),
    include_str!("../src/attach.rs"),
    include_str!("../src/bounds.rs"),
    include_str!("../src/canonical.rs"),
    include_str!("../src/error.rs"),
    include_str!("../src/json_util.rs"),
    include_str!("../src/registry.rs"),
    include_str!("../src/types.rs"),
];

const MANIFEST: &str = include_str!("../Cargo.toml");

#[test]
fn p7_source_has_no_network_process_or_live_authority_surfaces() {
    for source in P7_SOURCES {
        for forbidden in [
            "std::net",
            "std::process",
            "Command::new",
            "TcpStream",
            "UdpSocket",
            "reqwest",
            "tokio",
            "hyper",
            "zkbench",
            "f32",
            "f64",
            "unsafe {",
            "pub fn release(",
            "pub fn transfer(",
            "pub fn trade(",
            "pub fn sign(",
            "pub fn pause(",
            "trust_score",
            "grants_authority: true",
            "grants_execution_authority: true",
            "trait AuthorityAdapter",
            "trait ClearingAdapter",
        ] {
            assert!(
                !source.contains(forbidden),
                "forbidden P7 source token: {forbidden}"
            );
        }
    }
}

#[test]
fn p7_manifest_is_closed_to_authorized_dependencies() {
    for dependency in ["serde", "serde_json", "sha2", "hex", "thiserror"] {
        assert!(MANIFEST.contains(dependency));
    }
    let production = MANIFEST
        .split("[dev-dependencies]")
        .next()
        .expect("production section");
    for forbidden in [
        "reqwest",
        "tokio",
        "hyper",
        "hsai",
        "zkbench",
        "sql",
        "rusqlite",
        "statebook-core",
        "statebook-settlement",
        "statebook-report",
        "statebook-source",
    ] {
        assert!(
            !production.contains(forbidden),
            "forbidden production dependency token: {forbidden}"
        );
    }
}

#[test]
fn p7_canonical_identity_is_domain_separated() {
    for domain in [
        "statebook:p7-authority-statement:v1\\0",
        "statebook:p7-attach-receipt:v1\\0",
        "statebook:p7-capital-overlay:v1\\0",
        "statebook:p7-authority-registration:v1\\0",
    ] {
        assert!(
            P7_SOURCES.iter().any(|source| source.contains(domain)),
            "missing canonical domain: {domain}"
        );
    }
}

#[test]
fn p7_exports_no_generic_adapter_trait() {
    assert!(!P7_SOURCES
        .iter()
        .any(|source| source.contains("pub trait") && source.contains("Adapter")));
}

#[test]
fn p7_legal_ops_gate_constants_remain_present() {
    let bounds = include_str!("../src/bounds.rs");
    for token in [
        "LEGAL_OPS_GATE_THREAT_MODEL_V1",
        "LEGAL_OPS_GATE_LEGAL_REVIEW_V1",
        "LEGAL_OPS_GATE_OPERATIONAL_EVIDENCE_V1",
        "LEGAL_OPS_GATE_LOSS_LIMITS_V1",
        "LEGAL_OPS_GATE_AUTHORITY_OWNER_V1",
        "LEGAL_OPS_GATE_LIVE_PRODUCTS_DEFERRED_V1",
        "live-execution-custody-signing-pause-margin-settlement-deferred",
    ] {
        assert!(
            bounds.contains(token),
            "missing legal/ops gate token: {token}"
        );
    }
}

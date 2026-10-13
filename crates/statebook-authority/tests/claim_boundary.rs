const P7_SOURCES: &[&str] = &[
    include_str!("../src/lib.rs"),
    include_str!("../src/bounds.rs"),
    include_str!("../src/canonical.rs"),
    include_str!("../src/error.rs"),
    include_str!("../src/json_util.rs"),
    include_str!("../src/preflight.rs"),
    include_str!("../src/types.rs"),
];

const MANIFEST: &str = include_str!("../Cargo.toml");

#[test]
fn p7_source_has_no_controller_network_or_authority_grant_surfaces() {
    for source in P7_SOURCES {
        for forbidden in [
            "std::net",
            "std::process",
            "Command::new",
            "TcpStream",
            "reqwest",
            "tokio",
            "zkbench",
            "f32",
            "f64",
            "unsafe {",
            "pub fn connect_",
            "pub fn execute_",
            "pub fn sign_",
            "pub fn transfer(",
            "pub fn trade(",
            "grants_authority: true",
            "PreflightOutcomeV1::Authorized",
            "ProductionGateV1::Authorized",
        ] {
            assert!(
                !source.contains(forbidden),
                "forbidden P7 source token: {forbidden}"
            );
        }
    }
}

#[test]
fn p7_manifest_is_closed() {
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
        "hsai",
        "zkbench",
        "statebook-core",
        "statebook-settlement",
        "statebook-source",
    ] {
        assert!(
            !production.contains(forbidden),
            "forbidden production dependency: {forbidden}"
        );
    }
}

#[test]
fn p7_canonical_domains_present() {
    for domain in [
        "statebook:p7-authority-package:v1\\0",
        "statebook:p7-preflight-receipt:v1\\0",
        "statebook:p7-loss-bound:v1\\0",
        "statebook:p7-nonclaim-set:v1\\0",
    ] {
        assert!(
            P7_SOURCES.iter().any(|source| source.contains(domain)),
            "missing domain: {domain}"
        );
    }
}

#[test]
fn p7_always_preserves_grants_authority_false() {
    assert!(P7_SOURCES
        .iter()
        .any(|source| source.contains("grants_authority: false")));
}

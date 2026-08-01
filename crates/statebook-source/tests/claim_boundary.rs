const P6_SOURCES: &[&str] = &[
    include_str!("../src/lib.rs"),
    include_str!("../src/bounds.rs"),
    include_str!("../src/canonical.rs"),
    include_str!("../src/error.rs"),
    include_str!("../src/import.rs"),
    include_str!("../src/json_util.rs"),
    include_str!("../src/registry.rs"),
    include_str!("../src/types.rs"),
];

const MANIFEST: &str = include_str!("../Cargo.toml");

#[test]
fn p6_source_has_no_network_process_or_authority_surfaces() {
    for source in P6_SOURCES {
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
            "trust_score",
            "grants_authority: true",
            "trait SourceAdapter",
            "trait VenueAdapter",
        ] {
            assert!(
                !source.contains(forbidden),
                "forbidden P6 source token: {forbidden}"
            );
        }
    }
}

#[test]
fn p6_manifest_is_closed_to_authorized_dependencies() {
    for dependency in [
        "serde",
        "serde_json",
        "sha2",
        "hex",
        "thiserror",
        "statebook-core",
    ] {
        assert!(MANIFEST.contains(dependency));
    }
    let production = MANIFEST
        .split("[dev-dependencies]")
        .next()
        .expect("production section");
    for forbidden in [
        "reqwest", "tokio", "hyper", "hsai", "zkbench", "sql", "rusqlite",
    ] {
        assert!(
            !production.contains(forbidden),
            "forbidden production dependency token: {forbidden}"
        );
    }
}

#[test]
fn p6_canonical_identity_is_domain_separated() {
    for domain in [
        "statebook:p6-source-registration:v1\\0",
        "statebook:p6-import-receipt:v1\\0",
        "statebook:p6-captured-artifact:v1\\0",
        "statebook:p6-provenance-set:v1\\0",
    ] {
        assert!(
            P6_SOURCES.iter().any(|source| source.contains(domain)),
            "missing canonical domain: {domain}"
        );
    }
}

#[test]
fn p6_exports_no_generic_adapter_trait() {
    assert!(!P6_SOURCES
        .iter()
        .any(|source| source.contains("pub trait") && source.contains("Adapter")));
}

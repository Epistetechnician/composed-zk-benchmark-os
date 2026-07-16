const P5_SOURCES: &[&str] = &[
    include_str!("../src/lib.rs"),
    include_str!("../src/adapter.rs"),
    include_str!("../src/bounds.rs"),
    include_str!("../src/bundle.rs"),
    include_str!("../src/canonical.rs"),
    include_str!("../src/error.rs"),
    include_str!("../src/json_util.rs"),
    include_str!("../src/types.rs"),
];

const MANIFEST: &str = include_str!("../Cargo.toml");

#[test]
fn p5_source_has_no_external_io_float_or_cross_domain_authority() {
    for source in P5_SOURCES {
        for forbidden in [
            "std::net",
            "std::process",
            "Command::new",
            "TcpStream",
            "UdpSocket",
            "reqwest",
            "tokio",
            "hsai_claim_envelope",
            "hsai_agent",
            "hsai-claim-envelope",
            "hsai-agent",
            "zkbench",
            "f32",
            "f64",
            "unsafe {",
            "pub fn release(",
            "pub fn transfer(",
            "trust_score",
            "release_safety_probability",
            "grants_authority: true",
        ] {
            assert!(
                !source.contains(forbidden),
                "forbidden P5 source token: {forbidden}"
            );
        }
    }
}

#[test]
fn p5_manifest_is_closed_to_the_authorized_dependency_set() {
    for dependency in ["serde", "serde_json", "sha2", "hex", "thiserror"] {
        assert!(MANIFEST.contains(dependency));
    }
    // Production deps stay closed; settlement is authorized only as a consumer
    // for hermetic fixture regression (dev-dependency).
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
        "statebook-core",
        "sql",
        "rusqlite",
    ] {
        assert!(
            !production.contains(forbidden),
            "forbidden production dependency token: {forbidden}"
        );
    }
    assert!(MANIFEST.contains("statebook-settlement"));
}

#[test]
fn p5_canonical_identity_is_domain_separated() {
    for domain in [
        "statebook:p5-bundle-manifest:v1\\0",
        "statebook:p5-bundle-member:v1\\0",
        "statebook:p5-audit-trace:v1\\0",
        "statebook:p5-nonclaim-set:v1\\0",
    ] {
        assert!(
            P5_SOURCES.iter().any(|source| source.contains(domain)),
            "missing canonical domain: {domain}"
        );
    }
}

#[test]
fn handoff_envelope_always_preserves_grants_authority_false() {
    assert!(P5_SOURCES
        .iter()
        .any(|source| source.contains("grants_authority: false")));
}

const P8_SOURCES: &[&str] = &[
    include_str!("../src/lib.rs"),
    include_str!("../src/bounds.rs"),
    include_str!("../src/error.rs"),
    include_str!("../src/golden.rs"),
    include_str!("../src/types.rs"),
];

const MANIFEST: &str = include_str!("../Cargo.toml");

#[test]
fn p8_source_has_no_network_process_or_live_authority_surfaces() {
    for source in P8_SOURCES {
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
            "trait EvaluationAdapter",
            "statebook-sim",
        ] {
            assert!(
                !source.contains(forbidden),
                "forbidden P8 source token: {forbidden}"
            );
        }
    }
}

#[test]
fn p8_manifest_depends_only_on_statebook_public_crates() {
    for dependency in [
        "statebook-core",
        "statebook-settlement",
        "statebook-report",
        "statebook-source",
        "statebook-authority",
        "serde",
        "serde_json",
        "thiserror",
        "hex",
    ] {
        assert!(
            MANIFEST.contains(dependency),
            "missing dependency {dependency}"
        );
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
fn p8_claim_boundary_constants_remain_present() {
    let bounds = include_str!("../src/bounds.rs");
    for token in [
        "STATE_SLICE_P8",
        "CLAIM_BOUNDARY_P8",
        "hermetic P1-P7 composed evaluation",
        "without live authority or value movement",
    ] {
        assert!(
            bounds.contains(token),
            "missing claim-boundary token: {token}"
        );
    }
}

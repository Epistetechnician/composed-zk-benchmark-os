#[test]
fn statebook_p2_source_stays_inside_the_authorized_claim_boundary() {
    let sources = [
        include_str!("../src/lib.rs"),
        include_str!("../src/exact.rs"),
        include_str!("../src/model.rs"),
        include_str!("../src/normalization.rs"),
        include_str!("../src/payoff.rs"),
        include_str!("../src/state_key.rs"),
    ]
    .join("\n");
    for forbidden in [
        "std::net",
        "std::process",
        "std::fs",
        "std::fs::write",
        "Command::",
        "TcpStream",
        "reqwest",
        "tokio",
        "hsai_",
        "zkbench",
        "unsafe {",
    ] {
        assert!(
            !sources.contains(forbidden),
            "forbidden P2 surface: {forbidden}"
        );
    }

    let financial_types = [
        include_str!("../src/exact.rs"),
        include_str!("../src/model.rs"),
        include_str!("../src/payoff.rs"),
    ]
    .join("\n");
    for forbidden in ["f32", "f64"] {
        assert!(
            !financial_types.contains(forbidden),
            "floating financial type: {forbidden}"
        );
    }
}

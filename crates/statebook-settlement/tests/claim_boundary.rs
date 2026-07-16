const LIB: &str = include_str!("../src/lib.rs");
const IMPLEMENTATION: &str = include_str!("../src/completeness.rs");
const MANIFEST: &str = include_str!("../Cargo.toml");

#[test]
fn p3_source_has_no_external_io_float_or_cross_domain_authority() {
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
    ] {
        assert!(
            !IMPLEMENTATION.contains(forbidden),
            "forbidden P3 source token: {forbidden}"
        );
        assert!(
            !LIB.contains(forbidden),
            "forbidden P3 public token: {forbidden}"
        );
    }
}

#[test]
fn p3_manifest_is_closed_to_the_authorized_dependency_set() {
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
fn public_reports_are_serialize_only_and_composition_has_no_aggregate_helper() {
    for generated_type in [
        "report_type!(\n    ExecutionCompletenessReportV1",
        "report_type!(\n    CapitalCompletenessReportV1",
        "report_type!(\n    SettlementCompletenessReportV1",
        "report_type!(\n    AssuranceCompletenessReportV1",
        "report_type!(\n    RecoveryCompletenessReportV1",
    ] {
        assert!(
            IMPLEMENTATION.contains(generated_type),
            "missing opaque report invocation: {generated_type}"
        );
    }
    assert!(IMPLEMENTATION.contains("pub struct SevenCompletenessReportsV1"));
    assert!(IMPLEMENTATION.contains("#[serde(rename = \"recognized_in_fixture\")]"));
    assert!(IMPLEMENTATION.contains("#[serde(rename = \"denied_in_fixture\")]"));
    assert!(IMPLEMENTATION
        .contains("#[derive(Clone, Debug, Eq, PartialEq, Serialize)]\n        pub struct $name"));
    assert!(
        !IMPLEMENTATION.contains("PartialEq, Deserialize, Serialize)]\n        pub struct $name")
    );
    for forbidden in [
        "pub fn complete(",
        "pub const fn complete(",
        "pub fn all_complete(",
        "pub fn weakest(",
        "pub fn score(",
        "pub fn rank(",
        "pub fn authorized(",
        "pub fn release(",
    ] {
        assert!(
            !IMPLEMENTATION.contains(forbidden),
            "aggregate helper escaped: {forbidden}"
        );
    }
}

#[test]
fn canonical_identity_is_domain_separated_and_not_json_derived() {
    for domain in [
        "statebook:p3-semantic-report:v1\\0",
        "statebook:p3-payoff-report:v1\\0",
        "statebook:p3-analysis-subject:v1\\0",
        "statebook:p3-execution-fixture:v1\\0",
        "statebook:p3-capital-fixture:v1\\0",
        "statebook:p3-capital-context:v1\\0",
        "statebook:p3-settlement-fixture:v1\\0",
        "statebook:p3-assurance-fixture:v1\\0",
        "statebook:p3-recovery-profile:v1\\0",
        "statebook:p3-recovery-fixture:v1\\0",
        "statebook:p3-execution-report:v1\\0",
        "statebook:p3-capital-report:v1\\0",
        "statebook:p3-settlement-report:v1\\0",
        "statebook:p3-assurance-report:v1\\0",
        "statebook:p3-recovery-report:v1\\0",
        "statebook:p3-seven-report-composition:v1\\0",
    ] {
        assert!(
            IMPLEMENTATION.contains(domain),
            "missing canonical domain: {domain}"
        );
    }
    assert!(!IMPLEMENTATION.contains("serde_json::to_vec"));
    assert!(!IMPLEMENTATION.contains("serde_json::to_string"));
}

const DCAP_PCCS_SOURCE: &str = include_str!("../examples/operator_live_dcap_pccs_artifact.rs");

#[test]
fn dcap_pccs_materializer_requires_explicit_operator_inputs() {
    for required in [
        "HSAI_PHALA_OPERATOR_ACK",
        "I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN",
        "HSAI_PHALA_DCAP_PCCS_INPUT_JSON",
        "phala_verify_response_path",
        "phala_collateral_response_path",
        "collateral_response_sha256",
        "raw-collateral-response.sha256",
    ] {
        assert!(
            DCAP_PCCS_SOURCE.contains(required),
            "DCAP/PCCS materializer must contain {required}"
        );
    }
}

#[test]
fn dcap_pccs_materializer_does_not_call_network_or_retain_raw_collateral() {
    let process_command = ["std::", "proc", "ess::Command"].concat();
    let ureq = ["ur", "eq::"].concat();
    let reqwest = ["req", "west::"].concat();
    let tcp_stream = ["Tcp", "Stream"].concat();
    for forbidden in [
        "collateral-raw.json",
        "verification-raw.json",
        "Authorization",
        "Bearer",
        &ureq,
        &reqwest,
        &tcp_stream,
        &process_command,
    ] {
        assert!(
            !DCAP_PCCS_SOURCE.contains(forbidden),
            "DCAP/PCCS materializer must not contain {forbidden}"
        );
    }
}

#[test]
fn dcap_pccs_materializer_keeps_non_claims_explicit() {
    for required in [
        "not proof",
        "not local DCAP quote verification",
        "not local PCCS service operation",
        "not TLS channel binding",
        "not benchmark evidence",
        "not accepted evidence",
    ] {
        assert!(
            DCAP_PCCS_SOURCE.contains(required),
            "DCAP/PCCS materializer must state {required}"
        );
    }
}

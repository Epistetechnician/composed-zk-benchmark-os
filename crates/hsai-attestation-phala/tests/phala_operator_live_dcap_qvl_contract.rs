const DCAP_QVL_SOURCE: &str = include_str!("../examples/operator_live_dcap_qvl_artifact.rs");

#[test]
fn dcap_qvl_materializer_requires_explicit_operator_inputs() {
    for required in [
        "HSAI_PHALA_OPERATOR_ACK",
        "I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN",
        "HSAI_PHALA_DCAP_QVL_INPUT_JSON",
        "raw_quote_path",
        "decoded_quote_path",
        "pck_info_path",
        "qvl_report_path",
        "qvl_tool_version",
        "pccs_url",
    ] {
        assert!(
            DCAP_QVL_SOURCE.contains(required),
            "DCAP/QVL materializer must contain {required}"
        );
    }
}

#[test]
fn dcap_qvl_materializer_does_not_invoke_network_process_or_retain_raw_outputs() {
    let process_command = ["std::", "proc", "ess::Command"].concat();
    let ureq = ["ur", "eq::"].concat();
    let reqwest = ["req", "west::"].concat();
    let tcp_stream = ["Tcp", "Stream"].concat();
    for forbidden in [
        "Authorization",
        "Bearer",
        "raw-quote.bin",
        "raw-quote-qvl-report.json",
        "raw-quote-pckinfo.json",
        "raw-quote-decoded.json",
        &ureq,
        &reqwest,
        &tcp_stream,
        &process_command,
    ] {
        assert!(
            !DCAP_QVL_SOURCE.contains(forbidden),
            "DCAP/QVL materializer must not contain {forbidden}"
        );
    }
}

#[test]
fn dcap_qvl_materializer_keeps_local_verification_claims_bounded() {
    for required in [
        "operator-local-dcap-qvl",
        "qvl_status",
        "qe_status",
        "platform_status",
        "not proof",
        "not repo-native DCAP verifier implementation",
        "not local PCCS service operation",
        "not managed-service signature/JWKS/JWT verification",
        "not TLS channel binding",
        "not benchmark evidence",
        "not accepted evidence",
    ] {
        assert!(
            DCAP_QVL_SOURCE.contains(required),
            "DCAP/QVL materializer must state {required}"
        );
    }
}

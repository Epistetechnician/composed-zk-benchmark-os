const LOCAL_PCCS_SOURCE: &str = include_str!("../examples/operator_live_local_pccs_artifact.rs");

#[test]
fn local_pccs_materializer_requires_explicit_operator_inputs() {
    for required in [
        "HSAI_PHALA_OPERATOR_ACK",
        "I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN",
        "HSAI_PHALA_LOCAL_PCCS_INPUT_JSON",
        "raw_quote_path",
        "pck_info_path",
        "qvl_report_path",
        "access_log_path",
        "pck_crl_response_path",
        "tcb_response_path",
        "qe_identity_response_path",
        "root_ca_crl_response_path",
        "qvl_tool_version",
        "pccs_url",
    ] {
        assert!(
            LOCAL_PCCS_SOURCE.contains(required),
            "local PCCS materializer must contain {required}"
        );
    }
}

#[test]
fn local_pccs_materializer_does_not_invoke_network_process_or_retain_raw_outputs() {
    let process_command = ["std::", "proc", "ess::Command"].concat();
    let ureq = ["ur", "eq::"].concat();
    let reqwest = ["req", "west::"].concat();
    let tcp_stream = ["Tcp", "Stream"].concat();
    for forbidden in [
        "Authorization",
        "Bearer",
        "raw-quote.bin",
        "local-pccs-qvl-report.json",
        "local-pccs-access-final.jsonl",
        &ureq,
        &reqwest,
        &tcp_stream,
        &process_command,
    ] {
        assert!(
            !LOCAL_PCCS_SOURCE.contains(forbidden),
            "local PCCS materializer must not contain {forbidden}"
        );
    }
}

#[test]
fn local_pccs_materializer_keeps_claims_bounded() {
    for required in [
        "operator-local-pccs-replay-qvl",
        "local-pccs",
        "http://127.0.0.1:",
        "http://localhost:",
        "not proof",
        "not production Intel PCS/PCCS operation",
        "not fresh collateral authority",
        "not repo-native DCAP verifier implementation",
        "not managed-service signature/JWKS/JWT verification",
        "not TLS channel binding",
        "not benchmark evidence",
        "not accepted evidence",
    ] {
        assert!(
            LOCAL_PCCS_SOURCE.contains(required),
            "local PCCS materializer must state {required}"
        );
    }
}

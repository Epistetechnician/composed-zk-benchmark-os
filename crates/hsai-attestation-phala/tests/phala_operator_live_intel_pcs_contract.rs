const INTEL_PCS_SOURCE: &str = include_str!("../examples/operator_live_intel_pcs_artifact.rs");

#[test]
fn intel_pcs_materializer_requires_explicit_operator_inputs() {
    for required in [
        "HSAI_PHALA_OPERATOR_ACK",
        "I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN",
        "HSAI_PHALA_INTEL_PCS_INPUT_JSON",
        "raw_quote_path",
        "pck_info_path",
        "qvl_report_path",
        "qvl_stderr_path",
        "qvl_tool_version",
        "pccs_url",
        "https://api.trustedservices.intel.com",
    ] {
        assert!(
            INTEL_PCS_SOURCE.contains(required),
            "Intel PCS materializer must contain {required}"
        );
    }
}

#[test]
fn intel_pcs_materializer_does_not_invoke_network_process_or_retain_raw_outputs() {
    let process_command = ["std::", "proc", "ess::Command"].concat();
    let ureq = ["ur", "eq::"].concat();
    let reqwest = ["req", "west::"].concat();
    let tcp_stream = ["Tcp", "Stream"].concat();
    for forbidden in [
        "Authorization",
        "Bearer",
        "raw-quote.bin",
        "intel-pcs-qvl-report.json",
        "intel-pcs-qvl.stderr",
        &ureq,
        &reqwest,
        &tcp_stream,
        &process_command,
    ] {
        assert!(
            !INTEL_PCS_SOURCE.contains(forbidden),
            "Intel PCS materializer must not contain {forbidden}"
        );
    }
}

#[test]
fn intel_pcs_materializer_keeps_claims_bounded() {
    for required in [
        "operator-direct-intel-pcs-qvl",
        "intel-pcs",
        "not proof",
        "not repo-native DCAP verifier implementation",
        "not managed-service signature/JWKS/JWT verification",
        "not TLS channel binding",
        "not benchmark evidence",
        "not accepted evidence",
    ] {
        assert!(
            INTEL_PCS_SOURCE.contains(required),
            "Intel PCS materializer must state {required}"
        );
    }
}

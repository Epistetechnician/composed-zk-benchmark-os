const MANAGED_JWKS_SOURCE: &str = include_str!("../examples/operator_live_jwks_artifact.rs");

#[test]
fn managed_jwks_materializer_requires_explicit_operator_inputs() {
    for required in [
        "HSAI_MANAGED_JWKS_OPERATOR_ACK",
        "I_ACKNOWLEDGE_OPERATOR_LIVE_JWKS_FETCH",
        "HSAI_MANAGED_JWKS_INPUT_JSON",
        "openid_response_path",
        "jwks_response_path",
        "openid_configuration_url",
        "jwks_uri",
        "operator-live-jwks-fetch",
    ] {
        assert!(
            MANAGED_JWKS_SOURCE.contains(required),
            "managed JWKS materializer must contain {required}"
        );
    }
}

#[test]
fn managed_jwks_materializer_does_not_call_network_process_or_retain_raw_responses() {
    let process_command = ["std::", "proc", "ess::Command"].concat();
    let ureq = ["ur", "eq::"].concat();
    let reqwest = ["req", "west::"].concat();
    let tcp_stream = ["Tcp", "Stream"].concat();
    for forbidden in [
        "Authorization",
        "Bearer",
        "openid.json",
        "certs.json",
        "raw-jwks",
        "raw-openid",
        &ureq,
        &reqwest,
        &tcp_stream,
        &process_command,
    ] {
        assert!(
            !MANAGED_JWKS_SOURCE.contains(forbidden),
            "managed JWKS materializer must not contain {forbidden}"
        );
    }
}

#[test]
fn managed_jwks_materializer_keeps_claims_bounded() {
    for required in [
        "not proof",
        "not token acceptance",
        "not managed-JWT signature verification",
        "not DCAP quote verification",
        "not PCCS service operation",
        "not TLS channel binding",
        "not benchmark evidence",
        "not accepted evidence",
    ] {
        assert!(
            MANAGED_JWKS_SOURCE.contains(required),
            "managed JWKS materializer must state {required}"
        );
    }
}

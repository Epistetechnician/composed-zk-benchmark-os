const API_ARTIFACT_SOURCE: &str = include_str!("../examples/operator_live_phala_api_artifact.rs");

#[test]
fn phala_api_artifact_runner_requires_explicit_operator_inputs() {
    for required in [
        "HSAI_PHALA_OPERATOR_ACK",
        "I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN",
        "HSAI_PHALA_API_ARTIFACT_INPUT_JSON",
        "artifact_bundle_path",
        "phala_verify_response_path",
        "write_phala_operator_live_artifact_output_root",
        "read_phala_operator_live_artifact_output_root",
    ] {
        assert!(
            API_ARTIFACT_SOURCE.contains(required),
            "Phala API artifact runner must contain {required}"
        );
    }
}

#[test]
fn phala_api_artifact_runner_does_not_call_network_or_retain_raw_body() {
    let process_command = ["std::", "proc", "ess::Command"].concat();
    let ureq = ["ur", "eq::"].concat();
    let reqwest = ["req", "west::"].concat();
    let tcp_stream = ["Tcp", "Stream"].concat();
    for forbidden in [
        "raw-response.json",
        "Authorization",
        "Bearer",
        &ureq,
        &reqwest,
        &tcp_stream,
        &process_command,
    ] {
        assert!(
            !API_ARTIFACT_SOURCE.contains(forbidden),
            "Phala API artifact runner must not contain {forbidden}"
        );
    }
}

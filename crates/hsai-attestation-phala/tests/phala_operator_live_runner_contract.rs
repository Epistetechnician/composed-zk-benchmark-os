const RUNNER_SOURCE: &str = include_str!("../examples/operator_live_run.rs");

#[test]
fn operator_live_runner_requires_explicit_operator_inputs() {
    for required in [
        "HSAI_PHALA_OPERATOR_ACK",
        "I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN",
        "HSAI_PHALA_OPERATOR_INPUT_JSON",
        "HSAI_PHALA_OPERATOR_CREDENTIAL_SOURCE",
        "PhalaOperatorLiveInvocation",
        "PhalaEnvCredentialProvider",
        "UreqPhalaOperatorLiveTransport",
    ] {
        assert!(
            RUNNER_SOURCE.contains(required),
            "operator live runner must contain {required}"
        );
    }
}

#[test]
fn operator_live_runner_has_no_default_endpoint_secret_or_raw_body_output() {
    let process_command = ["std::", "proc", "ess::Command"].concat();
    let process_exit = ["proc", "ess::exit"].concat();
    for forbidden in [
        "operator.example",
        "PHALA_OPERATOR_TOKEN",
        "phase-102-secret",
        "raw-response.json",
        &process_command,
        &process_exit,
    ] {
        assert!(
            !RUNNER_SOURCE.contains(forbidden),
            "operator live runner must not contain {forbidden}"
        );
    }
    assert!(
        !RUNNER_SOURCE.contains("https://"),
        "operator endpoint must be supplied by operator input, not hard-coded"
    );
}

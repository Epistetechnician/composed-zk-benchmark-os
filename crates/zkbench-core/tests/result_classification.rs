use zkbench_core::{classify_result, BackendOutcome, ExpectedVerdict, ResultClassification};

#[test]
fn expected_reject_accepted_is_unsound_candidate() {
    assert_eq!(
        classify_result(ExpectedVerdict::Reject, BackendOutcome::Accepted),
        ResultClassification::ExpectedRejectAcceptedUnsoundCandidate
    );
}

#[test]
fn expected_accept_accepted_is_expected_accept_accepted() {
    assert_eq!(
        classify_result(ExpectedVerdict::Accept, BackendOutcome::Accepted),
        ResultClassification::ExpectedAcceptAccepted
    );
}

#[test]
fn expected_reject_rejected_is_expected_reject_rejected() {
    assert_eq!(
        classify_result(ExpectedVerdict::Reject, BackendOutcome::Rejected),
        ResultClassification::ExpectedRejectRejected
    );
}

#[test]
fn timeout_is_distinguished() {
    assert_eq!(
        classify_result(ExpectedVerdict::Reject, BackendOutcome::Timeout),
        ResultClassification::Timeout
    );
}

#[test]
fn capability_gap_is_distinguished() {
    assert_eq!(
        classify_result(ExpectedVerdict::Reject, BackendOutcome::CapabilityGap),
        ResultClassification::CapabilityGap
    );
}

#[test]
fn malformed_artifact_is_not_semantic_rejection() {
    assert_eq!(
        classify_result(ExpectedVerdict::Reject, BackendOutcome::MalformedArtifact),
        ResultClassification::MalformedArtifact
    );
}

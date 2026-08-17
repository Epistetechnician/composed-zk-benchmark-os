//! Focused coverage for the pure-data OpaqueTraceReplay contract.
//!
//! State slice: `research-synthesis-trace-replay-v1-benchmark-adapter-contract`.

use zkbench_core::{
    build_opaque_trace_replay_case, expected_opaque_trace_replay_quarantine_status,
    expected_opaque_trace_replay_verdict, validate_opaque_trace_replay_adapter_result,
    validate_opaque_trace_replay_candidate, BackendOutcome, ClaimBoundary,
    OpaqueTraceReplayAdapterObservation, OpaqueTraceReplayAdapterResult,
    OpaqueTraceReplayValidationIssueKind, OpaqueTraceReplayVariant,
    OPAQUE_TRACE_REPLAY_CLAIM_BOUNDARY,
};

const NOW: u64 = 100;

#[test]
fn every_variant_has_a_frozen_oracle_and_bounded_candidate() {
    for variant in OpaqueTraceReplayVariant::ALL {
        let case = build_opaque_trace_replay_case(variant);
        assert_eq!(
            case.expected_verdict,
            expected_opaque_trace_replay_verdict(variant)
        );
        assert_eq!(
            case.expected_quarantine_status,
            expected_opaque_trace_replay_quarantine_status(variant)
        );
        assert_eq!(
            case.candidate.claim_boundary,
            OPAQUE_TRACE_REPLAY_CLAIM_BOUNDARY
        );
        assert!(!case.candidate.raw_payload_retained);

        let validation = validate_opaque_trace_replay_candidate(&case.candidate, NOW);
        if variant == OpaqueTraceReplayVariant::MalformedEnvelope {
            assert!(!validation.valid, "malformed envelope must fail validation");
        } else {
            assert!(
                validation.valid,
                "{variant:?} should satisfy its declared mutation: {:?}",
                validation.issues
            );
        }
    }
}

#[test]
fn context_mutations_are_distinguished_by_the_semantic_oracle() {
    for variant in [
        OpaqueTraceReplayVariant::WrongUserReplay,
        OpaqueTraceReplayVariant::WrongSessionReplay,
        OpaqueTraceReplayVariant::WrongModelReplay,
        OpaqueTraceReplayVariant::OutOfOrderBlock,
        OpaqueTraceReplayVariant::DuplicateBlock,
    ] {
        let case = build_opaque_trace_replay_case(variant);
        assert_eq!(case.expected_verdict, zkbench_core::ExpectedVerdict::Reject);
        assert!(validate_opaque_trace_replay_candidate(&case.candidate, NOW).valid);
    }
}

#[test]
fn raw_payload_retention_and_claim_escalation_fail_closed() {
    let mut candidate =
        build_opaque_trace_replay_case(OpaqueTraceReplayVariant::ValidSameSession).candidate;
    candidate.raw_payload_retained = true;
    candidate.claim_boundary = ClaimBoundary::Level1LocalReplay;

    let validation = validate_opaque_trace_replay_candidate(&candidate, NOW);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.kind == OpaqueTraceReplayValidationIssueKind::RawPayloadRetained));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.kind == OpaqueTraceReplayValidationIssueKind::ClaimBoundaryTooHigh));
}

#[test]
fn adapter_result_is_digest_bound_and_cannot_grant_authority() {
    let case = build_opaque_trace_replay_case(OpaqueTraceReplayVariant::ValidSameSession);
    let result = OpaqueTraceReplayAdapterResult {
        candidate_digest: case
            .candidate
            .digest()
            .expect("candidate digest is deterministic"),
        observation: OpaqueTraceReplayAdapterObservation::Accepted,
        backend_outcome: BackendOutcome::Accepted,
        quarantine_status: case.expected_quarantine_status,
        claim_boundary: OPAQUE_TRACE_REPLAY_CLAIM_BOUNDARY,
        authority_granted: false,
    };
    assert!(validate_opaque_trace_replay_adapter_result(&case, &result).valid);

    let wrong_case = build_opaque_trace_replay_case(OpaqueTraceReplayVariant::WrongModelReplay);
    let wrong_result = OpaqueTraceReplayAdapterResult {
        candidate_digest: wrong_case
            .candidate
            .digest()
            .expect("candidate digest is deterministic"),
        observation: OpaqueTraceReplayAdapterObservation::Accepted,
        backend_outcome: BackendOutcome::Accepted,
        quarantine_status: wrong_case.expected_quarantine_status,
        claim_boundary: OPAQUE_TRACE_REPLAY_CLAIM_BOUNDARY,
        authority_granted: false,
    };
    let validation = validate_opaque_trace_replay_adapter_result(&wrong_case, &wrong_result);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.kind == OpaqueTraceReplayValidationIssueKind::UnexpectedObservation));

    let mut unauthorized = result;
    unauthorized.authority_granted = true;
    let validation = validate_opaque_trace_replay_adapter_result(&case, &unauthorized);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.kind == OpaqueTraceReplayValidationIssueKind::AuthorityGranted));

    let mut forged_case = case;
    forged_case.expected_verdict = zkbench_core::ExpectedVerdict::Reject;
    let validation = validate_opaque_trace_replay_adapter_result(&forged_case, &unauthorized);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.kind == OpaqueTraceReplayValidationIssueKind::UnexpectedObservation));
}

#[test]
fn serialization_contains_metadata_only() {
    let case = build_opaque_trace_replay_case(OpaqueTraceReplayVariant::HiddenInjection);
    let json = serde_json::to_string(&case).expect("typed case should serialize");
    assert!(json.contains("hidden_injection"));
    assert!(json.contains("raw_payload_retained"));
    assert!(!json.contains("instruction text"));
    assert!(!json.contains("credential"));
    assert!(!json.contains("opaque trace bytes"));
}

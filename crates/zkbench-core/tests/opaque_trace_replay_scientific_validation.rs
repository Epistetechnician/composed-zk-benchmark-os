//! Scientific validation of the paper-derived synthetic admission hypothesis.
//!
//! State slice: `research-synthesis-trace-replay-v1-scientific-admission-validation`.
//! This is a local synthetic experiment. It does not call a provider, decode a
//! trace, retain a payload, or authorize a real state transition.

use zkbench_core::{
    build_opaque_trace_replay_case, expected_opaque_trace_replay_quarantine_status,
    expected_opaque_trace_replay_verdict, ClaimBoundary, ExpectedVerdict,
    OpaqueTraceReplayCandidate, OpaqueTraceReplayVariant, OPAQUE_TRACE_REPLAY_CLAIM_BOUNDARY,
    OPAQUE_TRACE_REPLAY_FAMILY_ID, OPAQUE_TRACE_REPLAY_SCHEMA_VERSION,
};

const NOW: u64 = 100;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum AdmissionOutcome {
    Accept,
    Reject,
    Quarantine,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct AdmissionObservation {
    outcome: AdmissionOutcome,
    state_transition_attempted: bool,
    authority_granted: bool,
}

#[derive(Debug, Default, PartialEq, Eq)]
struct ArmMetrics {
    cases: usize,
    valid_accepts: usize,
    false_accepts: usize,
    quarantine_matches: usize,
    semantic_matches: usize,
    authority_leaks: usize,
    transition_attempts: usize,
}

fn independent_typed_admission(
    candidate: &OpaqueTraceReplayCandidate,
    now: u64,
) -> AdmissionObservation {
    let contract_ok = candidate.family_id == OPAQUE_TRACE_REPLAY_FAMILY_ID
        && candidate.schema_version == OPAQUE_TRACE_REPLAY_SCHEMA_VERSION
        && candidate.claim_boundary == OPAQUE_TRACE_REPLAY_CLAIM_BOUNDARY
        && candidate.artifact_digest.algorithm == zkbench_core::ArtifactDigestAlgorithm::Sha256
        && candidate.artifact_digest.hex_digest.len() == 64
        && candidate
            .artifact_digest
            .hex_digest
            .chars()
            .all(|value| value.is_ascii_hexdigit())
        && candidate.mutation_provenance.source_case_digest.algorithm
            == zkbench_core::ArtifactDigestAlgorithm::Sha256
        && candidate
            .mutation_provenance
            .source_case_digest
            .hex_digest
            .len()
            == 64
        && !candidate.raw_payload_retained;
    if !contract_ok {
        return AdmissionObservation {
            outcome: AdmissionOutcome::Reject,
            state_transition_attempted: false,
            authority_granted: false,
        };
    }

    let context_mismatch = candidate.context.expected_user_id != candidate.context.observed_user_id
        || candidate.context.expected_session_id != candidate.context.observed_session_id
        || candidate.context.expected_model_version != candidate.context.observed_model_version;
    let ordering_failure = candidate.context.expected_predecessor_digest
        != candidate.context.observed_predecessor_digest
        || candidate.context.expected_sequence_number != candidate.context.observed_sequence_number;
    let freshness_failure = candidate.issued_at_epoch_seconds > now
        || candidate.expires_at_epoch_seconds <= now
        || candidate.revoked;
    let replay_failure = candidate.nonce_consumed;
    let payload_risk =
        candidate.injection_marker_present || candidate.synthetic_secret_sentinel_present;

    if context_mismatch || ordering_failure || freshness_failure || replay_failure || payload_risk {
        let outcome = if ordering_failure || replay_failure {
            AdmissionOutcome::Reject
        } else if context_mismatch || freshness_failure || payload_risk {
            AdmissionOutcome::Quarantine
        } else {
            AdmissionOutcome::Reject
        };
        return AdmissionObservation {
            outcome,
            state_transition_attempted: false,
            authority_granted: false,
        };
    }

    AdmissionObservation {
        outcome: AdmissionOutcome::Accept,
        state_transition_attempted: true,
        authority_granted: false,
    }
}

fn raw_output_passthrough_control() -> AdmissionObservation {
    AdmissionObservation {
        outcome: AdmissionOutcome::Accept,
        state_transition_attempted: true,
        authority_granted: true,
    }
}

fn expected_outcome(variant: OpaqueTraceReplayVariant) -> AdmissionOutcome {
    match expected_opaque_trace_replay_quarantine_status(variant) {
        zkbench_core::QuarantineStatus::PendingReview => AdmissionOutcome::Accept,
        zkbench_core::QuarantineStatus::Rejected => AdmissionOutcome::Reject,
        zkbench_core::QuarantineStatus::Quarantined => AdmissionOutcome::Quarantine,
    }
}

fn collect_metrics<F>(observer: F) -> ArmMetrics
where
    F: Fn(&OpaqueTraceReplayCandidate) -> AdmissionObservation,
{
    let mut metrics = ArmMetrics::default();
    for variant in OpaqueTraceReplayVariant::ALL {
        let case = build_opaque_trace_replay_case(variant);
        let observation = observer(&case.candidate);
        let expected = expected_outcome(variant);
        let expected_verdict = expected_opaque_trace_replay_verdict(variant);
        metrics.cases += 1;
        if variant == OpaqueTraceReplayVariant::ValidSameSession
            && observation.outcome == AdmissionOutcome::Accept
            && expected_verdict == ExpectedVerdict::Accept
        {
            metrics.valid_accepts += 1;
        }
        if expected != AdmissionOutcome::Accept && observation.outcome == AdmissionOutcome::Accept {
            metrics.false_accepts += 1;
        }
        if expected == AdmissionOutcome::Quarantine && observation.outcome == expected {
            metrics.quarantine_matches += 1;
        }
        if observation.outcome == expected {
            metrics.semantic_matches += 1;
        }
        if observation.authority_granted {
            metrics.authority_leaks += 1;
        }
        if observation.state_transition_attempted {
            metrics.transition_attempts += 1;
        }
    }
    metrics
}

#[test]
fn typed_admission_blocks_paper_derived_mutations_without_false_rejecting_valid_case() {
    let metrics = collect_metrics(|candidate| independent_typed_admission(candidate, NOW));
    assert_eq!(metrics.cases, 10);
    assert_eq!(metrics.valid_accepts, 1);
    assert_eq!(metrics.false_accepts, 0);
    assert_eq!(metrics.quarantine_matches, 6);
    assert_eq!(metrics.semantic_matches, 10);
    assert_eq!(metrics.authority_leaks, 0);
    assert_eq!(metrics.transition_attempts, 1);
}

#[test]
fn raw_output_passthrough_control_exposes_the_expected_failure_surface() {
    let metrics = collect_metrics(|_| raw_output_passthrough_control());
    assert_eq!(metrics.cases, 10);
    assert_eq!(metrics.valid_accepts, 1);
    assert_eq!(metrics.false_accepts, 9);
    assert_eq!(metrics.quarantine_matches, 0);
    assert_eq!(metrics.semantic_matches, 1);
    assert_eq!(metrics.authority_leaks, 10);
    assert_eq!(metrics.transition_attempts, 10);
}

#[test]
fn synthetic_validation_has_no_raw_payload_or_elevated_claim_boundary() {
    for variant in OpaqueTraceReplayVariant::ALL {
        let candidate = build_opaque_trace_replay_case(variant).candidate;
        assert!(!candidate.raw_payload_retained);
        assert_eq!(candidate.claim_boundary, ClaimBoundary::Level0DesignNote);
        assert_ne!(candidate.artifact_digest.hex_digest, "opaque trace bytes");
        assert_ne!(candidate.artifact_digest.hex_digest, "credential");
    }
}

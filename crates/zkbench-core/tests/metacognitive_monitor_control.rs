//! Focused coverage for the synthetic metacognitive monitoring/control contract.
//!
//! State slice: `research-synthesis-metacognition-v1-benchmark-contract`.

use std::fs;
use std::path::Path;

use zkbench_core::{
    build_metacognitive_monitor_control_case, expected_metacognitive_monitor_control_verdict,
    validate_metacognitive_monitor_control_candidate,
    validate_metacognitive_monitor_control_result, BackendOutcome, ClaimBoundary,
    MetacognitiveMonitorControlObservation, MetacognitiveMonitorControlResult,
    MetacognitiveMonitorControlValidationIssueKind, MetacognitiveMonitorControlVariant,
    METACOGNITIVE_MONITOR_CONTROL_CLAIM_BOUNDARY,
};

#[test]
fn every_variant_has_a_frozen_verdict_and_bounded_candidate() {
    for variant in MetacognitiveMonitorControlVariant::ALL {
        let case = build_metacognitive_monitor_control_case(variant);
        assert_eq!(
            case.expected_verdict,
            expected_metacognitive_monitor_control_verdict(variant)
        );

        let validation = validate_metacognitive_monitor_control_candidate(&case.candidate);
        if variant == MetacognitiveMonitorControlVariant::MalformedRecord {
            assert!(!validation.valid, "malformed record must fail validation");
        } else {
            assert!(
                validation.valid,
                "{variant:?} should satisfy its frozen semantics: {:?}",
                validation.issues
            );
            assert!(!case.candidate.raw_reasoning_retained);
        }
        if variant != MetacognitiveMonitorControlVariant::MalformedRecord {
            assert_eq!(
                case.candidate.claim_boundary,
                METACOGNITIVE_MONITOR_CONTROL_CLAIM_BOUNDARY
            );
        }
    }
}

#[test]
fn monitoring_reporting_and_control_are_distinct_cases() {
    let detected = build_metacognitive_monitor_control_case(
        MetacognitiveMonitorControlVariant::DetectsErrorRevises,
    );
    let no_control = build_metacognitive_monitor_control_case(
        MetacognitiveMonitorControlVariant::DetectsErrorNoControl,
    );
    let no_monitor = build_metacognitive_monitor_control_case(
        MetacognitiveMonitorControlVariant::ControlWithoutMonitor,
    );

    assert_eq!(
        detected.expected_verdict,
        zkbench_core::ExpectedVerdict::Accept
    );
    assert_eq!(
        no_control.expected_verdict,
        zkbench_core::ExpectedVerdict::Reject
    );
    assert_eq!(
        no_monitor.expected_verdict,
        zkbench_core::ExpectedVerdict::CapabilityGap
    );
    assert_ne!(
        detected.candidate.observed_control,
        no_control.candidate.observed_control
    );
    assert_ne!(
        detected.candidate.signal_source,
        no_monitor.candidate.signal_source
    );
}

#[test]
fn retention_lock_and_claim_escalation_fail_closed() {
    let mut candidate = build_metacognitive_monitor_control_case(
        MetacognitiveMonitorControlVariant::CalibratedProceed,
    )
    .candidate;
    candidate.raw_reasoning_retained = true;
    candidate.prediction_locked_before_assessment = false;
    candidate.claim_boundary = ClaimBoundary::Level1LocalReplay;

    let validation = validate_metacognitive_monitor_control_candidate(&candidate);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.kind
            == MetacognitiveMonitorControlValidationIssueKind::RawReasoningRetained));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.kind
            == MetacognitiveMonitorControlValidationIssueKind::PredictionNotLocked));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.kind
            == MetacognitiveMonitorControlValidationIssueKind::ClaimBoundaryTooHigh));
}

#[test]
fn result_is_digest_bound_and_cannot_grant_authority() {
    let case = build_metacognitive_monitor_control_case(
        MetacognitiveMonitorControlVariant::CalibratedProceed,
    );
    let result = MetacognitiveMonitorControlResult {
        candidate_digest: case.candidate.digest().expect("digest is deterministic"),
        observation: MetacognitiveMonitorControlObservation::Passed,
        backend_outcome: BackendOutcome::Accepted,
        claim_boundary: METACOGNITIVE_MONITOR_CONTROL_CLAIM_BOUNDARY,
        authority_granted: false,
    };
    assert!(validate_metacognitive_monitor_control_result(&case, &result).valid);

    let mut unauthorized = result;
    unauthorized.authority_granted = true;
    let validation = validate_metacognitive_monitor_control_result(&case, &unauthorized);
    assert!(!validation.valid);
    assert!(validation.issues.iter().any(
        |issue| issue.kind == MetacognitiveMonitorControlValidationIssueKind::AuthorityGranted
    ));

    let mut wrong_observation = unauthorized;
    wrong_observation.authority_granted = false;
    wrong_observation.observation = MetacognitiveMonitorControlObservation::Failed;
    wrong_observation.backend_outcome = BackendOutcome::Rejected;
    let validation = validate_metacognitive_monitor_control_result(&case, &wrong_observation);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.kind
            == MetacognitiveMonitorControlValidationIssueKind::UnexpectedObservation));
}

#[test]
fn serialization_is_metadata_only() {
    let case = build_metacognitive_monitor_control_case(
        MetacognitiveMonitorControlVariant::DomainShiftOverconfidence,
    );
    let json = serde_json::to_string(&case).expect("typed case should serialize");
    assert!(json.contains("domain_shift_overconfidence"));
    assert!(json.contains("prediction_locked_before_assessment"));
    assert!(!json.contains("chain of thought"));
    assert!(!json.contains("private reasoning"));
}

#[test]
fn taxonomy_registers_the_family_as_a_level0_synthetic_contract() {
    let taxonomy_path =
        Path::new(env!("CARGO_MANIFEST_DIR")).join("../../docs/08-benchmark-taxonomy.md");
    let taxonomy =
        fs::read_to_string(taxonomy_path).expect("benchmark taxonomy should be readable");

    for required in [
        "MetacognitiveMonitorControl",
        "Level 0 design note",
        "calibrated_proceed",
        "control-without-monitor",
        "domain-shift degradation",
        "synthetic evaluation contract",
    ] {
        assert!(
            taxonomy.contains(required),
            "benchmark taxonomy is missing required metacognition registration: {required}"
        );
    }
}

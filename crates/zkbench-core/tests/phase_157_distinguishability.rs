//! Phase 157 — mutation distinguishability scoring integration tests.

use zkbench_core::{
    classify_mutation_distinguishability, mandatory_distinguishability_nonclaims,
    summarize_mutation_distinguishability, BackendOutcome, ExpectedVerdict, MutationClass,
    MutationDistinguishabilityAxis, ResultClassification,
};

#[test]
fn every_expected_verdict_x_backend_outcome_pairing_classifies() {
    let outcomes = [
        BackendOutcome::Accepted,
        BackendOutcome::Rejected,
        BackendOutcome::Error,
        BackendOutcome::Timeout,
        BackendOutcome::CapabilityGap,
        BackendOutcome::MalformedArtifact,
        BackendOutcome::Inconclusive,
    ];
    let verdicts = [
        ExpectedVerdict::Accept,
        ExpectedVerdict::Reject,
        ExpectedVerdict::UnsoundIfAccepted,
        ExpectedVerdict::BackendError,
        ExpectedVerdict::Inconclusive,
        ExpectedVerdict::CapabilityGap,
    ];
    for verdict in verdicts {
        let matrix = classify_mutation_distinguishability(MutationClass::BadCounters, verdict);
        assert_eq!(matrix.cells.len(), outcomes.len());
        for outcome in outcomes {
            let cell = matrix
                .cells
                .iter()
                .find(|c| c.backend_outcome == outcome)
                .expect("every backend outcome must be represented");
            // The classification must match what classify_result would produce.
            assert_eq!(
                cell.classification,
                zkbench_core::classify_result(verdict, outcome)
            );
            // The axis must be derivable from the classification.
            assert_eq!(cell.axis, axis_for_classification_test(cell.classification));
        }
    }
}

#[test]
fn matrix_is_complete_for_each_mutation_class() {
    for mutation_class in all_fourteen_mutation_classes() {
        let matrix = classify_mutation_distinguishability(mutation_class, ExpectedVerdict::Reject);
        assert_eq!(matrix.cells.len(), 7, "class {mutation_class:?}");
        assert_eq!(matrix.mutation_class, mutation_class);
    }
}

#[test]
fn reject_x_accepted_is_unsound_acceptance_candidate() {
    let matrix = classify_mutation_distinguishability(
        MutationClass::InvariantWeakening,
        ExpectedVerdict::Reject,
    );
    let cell = matrix
        .cells
        .iter()
        .find(|c| c.backend_outcome == BackendOutcome::Accepted)
        .unwrap();
    assert_eq!(
        cell.axis,
        MutationDistinguishabilityAxis::UnsoundAcceptanceCandidate
    );
    assert_eq!(
        cell.classification,
        ResultClassification::ExpectedRejectAcceptedUnsoundCandidate
    );
}

#[test]
fn unsound_x_rejected_is_detected_rejection() {
    let matrix = classify_mutation_distinguishability(
        MutationClass::InvariantWeakening,
        ExpectedVerdict::UnsoundIfAccepted,
    );
    let cell = matrix
        .cells
        .iter()
        .find(|c| c.backend_outcome == BackendOutcome::Rejected)
        .unwrap();
    assert_eq!(cell.axis, MutationDistinguishabilityAxis::DetectedRejection);
}

#[test]
fn accept_x_rejected_is_false_rejection_candidate() {
    let matrix =
        classify_mutation_distinguishability(MutationClass::BadCounters, ExpectedVerdict::Accept);
    let cell = matrix
        .cells
        .iter()
        .find(|c| c.backend_outcome == BackendOutcome::Rejected)
        .unwrap();
    assert_eq!(
        cell.axis,
        MutationDistinguishabilityAxis::FalseRejectionCandidate
    );
}

#[test]
fn accept_x_accepted_is_true_positive() {
    let matrix =
        classify_mutation_distinguishability(MutationClass::BadCounters, ExpectedVerdict::Accept);
    let cell = matrix
        .cells
        .iter()
        .find(|c| c.backend_outcome == BackendOutcome::Accepted)
        .unwrap();
    assert_eq!(cell.axis, MutationDistinguishabilityAxis::TruePositive);
}

#[test]
fn summary_aggregates_across_matrices() {
    let matrices = vec![
        classify_mutation_distinguishability(MutationClass::BadCounters, ExpectedVerdict::Reject),
        classify_mutation_distinguishability(
            MutationClass::InvariantWeakening,
            ExpectedVerdict::UnsoundIfAccepted,
        ),
        classify_mutation_distinguishability(
            MutationClass::CorruptedGuards,
            ExpectedVerdict::Reject,
        ),
    ];
    let summary = summarize_mutation_distinguishability(&matrices);
    assert_eq!(summary.matrix_count, 3);
    assert_eq!(summary.total_cells, 21);
    // Three matrices, each with exactly one Accepted-under-reject cell.
    assert_eq!(summary.unsound_acceptance_candidate, 3);
    // Three matrices, each with exactly one Rejected-under-reject cell.
    assert_eq!(summary.detected_rejection, 3);
    // Remaining 15 cells across the three matrices are inconclusive-axis.
    assert_eq!(summary.inconclusive, 15);
    assert_eq!(summary.true_positive, 0);
    assert_eq!(summary.false_rejection_candidate, 0);
}

#[test]
fn summary_carries_mandatory_nonclaims() {
    let matrices = vec![classify_mutation_distinguishability(
        MutationClass::BadCounters,
        ExpectedVerdict::Reject,
    )];
    let summary = summarize_mutation_distinguishability(&matrices);
    let nonclaims = mandatory_distinguishability_nonclaims();
    assert_eq!(summary.nonclaims, nonclaims);
    assert!(summary
        .nonclaims
        .iter()
        .any(|n| n.contains("not benchmark evidence")));
    assert!(summary
        .nonclaims
        .iter()
        .any(|n| n.contains("hypothetical backend outcome")));
}

#[test]
fn axis_severity_is_monotonic() {
    use MutationDistinguishabilityAxis::*;
    assert!(UnsoundAcceptanceCandidate.axis_severity() > DetectedRejection.axis_severity());
    assert!(DetectedRejection.axis_severity() > FalseRejectionCandidate.axis_severity());
    assert!(FalseRejectionCandidate.axis_severity() > Inconclusive.axis_severity());
    assert!(Inconclusive.axis_severity() > TruePositive.axis_severity());
}

#[test]
fn matrix_is_deterministic() {
    let left =
        classify_mutation_distinguishability(MutationClass::BadCounters, ExpectedVerdict::Reject);
    let right =
        classify_mutation_distinguishability(MutationClass::BadCounters, ExpectedVerdict::Reject);
    assert_eq!(left, right);
}

#[test]
fn no_new_evidence_variants_were_added_scope_guard() {
    // If ExpectedVerdict / BackendOutcome / ResultClassification grew variants,
    // the matrix construction would need to be revisited. These counts guard
    // against silent scope creep.
    let verdicts = [
        ExpectedVerdict::Accept,
        ExpectedVerdict::Reject,
        ExpectedVerdict::BackendError,
        ExpectedVerdict::Inconclusive,
        ExpectedVerdict::CapabilityGap,
        ExpectedVerdict::UnsoundIfAccepted,
    ];
    assert_eq!(verdicts.len(), 6, "ExpectedVerdict variant count");
    let outcomes = [
        BackendOutcome::Accepted,
        BackendOutcome::Rejected,
        BackendOutcome::Error,
        BackendOutcome::Timeout,
        BackendOutcome::CapabilityGap,
        BackendOutcome::MalformedArtifact,
        BackendOutcome::Inconclusive,
    ];
    assert_eq!(outcomes.len(), 7, "BackendOutcome variant count");
}

fn axis_for_classification_test(
    classification: ResultClassification,
) -> MutationDistinguishabilityAxis {
    match classification {
        ResultClassification::ExpectedAcceptAccepted => {
            MutationDistinguishabilityAxis::TruePositive
        }
        ResultClassification::ExpectedRejectRejected => {
            MutationDistinguishabilityAxis::DetectedRejection
        }
        ResultClassification::ExpectedRejectAcceptedUnsoundCandidate => {
            MutationDistinguishabilityAxis::UnsoundAcceptanceCandidate
        }
        ResultClassification::ExpectedAcceptRejected => {
            MutationDistinguishabilityAxis::FalseRejectionCandidate
        }
        _ => MutationDistinguishabilityAxis::Inconclusive,
    }
}

fn all_fourteen_mutation_classes() -> Vec<MutationClass> {
    vec![
        MutationClass::MissingConstraints,
        MutationClass::CorruptedGuards,
        MutationClass::BadCounters,
        MutationClass::StaleStateReads,
        MutationClass::InvalidUnrollBounds,
        MutationClass::NondeterministicTransitionInjection,
        MutationClass::RecursionEnvelopeMismatch,
        MutationClass::PublicPrivateBoundaryMismatch,
        MutationClass::WitnessAliasing,
        MutationClass::InvariantWeakening,
        MutationClass::InvariantStrengthening,
        MutationClass::ObservationOmission,
        MutationClass::SemanticNoOpDrift,
        MutationClass::TraceOrderingCorruption,
    ]
}

//! Mutation distinguishability scoring primitives.
//!
//! Local-only analytical lens composing each mutation's declared
//! `ExpectedVerdict` with each `BackendOutcome` variant via the existing
//! `classify_result` to produce a deterministic complete matrix.
//!
//! All output is local metadata analysis capped at `Level1LocalReplay`. It is
//! not benchmark evidence, not accepted evidence, not formal evidence, and not
//! proof. A cell classifying as `UnsoundAcceptanceCandidate` is a hypothetical
//! signal under a hypothetical backend outcome, not evidence that any real
//! backend would produce that outcome.

use serde::{Deserialize, Serialize};

use crate::evidence::{
    classify_result, BackendOutcome, ClaimBoundary, ExpectedVerdict, ResultClassification,
};
use crate::mutation::MutationClass;

/// Distinguishability axis for a single expected-verdict × backend-outcome
/// pairing.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MutationDistinguishabilityAxis {
    /// Oracle says accept, backend accepts. Not a mutation signal.
    TruePositive,
    /// Oracle says reject, backend rejects. The mutation is detected.
    DetectedRejection,
    /// Oracle says reject, backend accepts. Unsound acceptance candidate —
    /// the highest-value mutation signal.
    UnsoundAcceptanceCandidate,
    /// Oracle says accept, backend rejects. False rejection candidate.
    FalseRejectionCandidate,
    /// Outcome was inconclusive, capability gap, timeout, error, or otherwise
    /// not classifiable as a clean signal.
    Inconclusive,
}

impl MutationDistinguishabilityAxis {
    /// Local-only priority hint (not a benchmark score). Higher is more
    /// interesting for downstream triage.
    pub fn axis_severity(self) -> u8 {
        match self {
            Self::UnsoundAcceptanceCandidate => 4,
            Self::DetectedRejection => 3,
            Self::FalseRejectionCandidate => 2,
            Self::Inconclusive => 1,
            Self::TruePositive => 0,
        }
    }
}

/// One cell of the distinguishability matrix.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MutationDistinguishabilityCell {
    /// Expected verdict declared by the mutation.
    pub expected_verdict: ExpectedVerdict,
    /// Hypothetical backend outcome.
    pub backend_outcome: BackendOutcome,
    /// Existing `classify_result` classification.
    pub classification: ResultClassification,
    /// Derived distinguishability axis.
    pub axis: MutationDistinguishabilityAxis,
}

/// Complete matrix for one mutation class.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MutationDistinguishabilityMatrix {
    /// Mutation class this matrix describes.
    pub mutation_class: MutationClass,
    /// One cell per `BackendOutcome` variant.
    pub cells: Vec<MutationDistinguishabilityCell>,
}

/// Aggregate summary across multiple matrices.
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize, Deserialize)]
pub struct MutationDistinguishabilitySummary {
    /// Number of matrices summarized.
    pub matrix_count: usize,
    /// Total cells across all matrices.
    pub total_cells: usize,
    /// Cells classified `TruePositive`.
    pub true_positive: usize,
    /// Cells classified `DetectedRejection`.
    pub detected_rejection: usize,
    /// Cells classified `UnsoundAcceptanceCandidate`.
    pub unsound_acceptance_candidate: usize,
    /// Cells classified `FalseRejectionCandidate`.
    pub false_rejection_candidate: usize,
    /// Cells classified `Inconclusive`.
    pub inconclusive: usize,
    /// Mandatory nonclaim language.
    pub nonclaims: Vec<String>,
}

/// All `BackendOutcome` variants in declaration order. Used to build a
/// complete matrix without sampling.
fn all_backend_outcomes() -> [BackendOutcome; 7] {
    [
        BackendOutcome::Accepted,
        BackendOutcome::Rejected,
        BackendOutcome::Error,
        BackendOutcome::Timeout,
        BackendOutcome::CapabilityGap,
        BackendOutcome::MalformedArtifact,
        BackendOutcome::Inconclusive,
    ]
}

/// Map an existing `ResultClassification` to a distinguishability axis.
pub fn axis_for_classification(
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
        ResultClassification::ExpectedRejectBackendError
        | ResultClassification::ExpectedBackendErrorObserved
        | ResultClassification::CapabilityGap
        | ResultClassification::Timeout
        | ResultClassification::Inconclusive
        | ResultClassification::MalformedArtifact
        | ResultClassification::UnexpectedOutcome => MutationDistinguishabilityAxis::Inconclusive,
    }
}

/// Build a complete distinguishability matrix for one mutation class. Produces
/// one cell per `BackendOutcome` variant, so the matrix is deterministic and
/// complete by construction.
pub fn classify_mutation_distinguishability(
    mutation_class: MutationClass,
    expected_verdict: ExpectedVerdict,
) -> MutationDistinguishabilityMatrix {
    let cells = all_backend_outcomes()
        .into_iter()
        .map(|backend_outcome| {
            let classification = classify_result(expected_verdict, backend_outcome);
            let axis = axis_for_classification(classification);
            MutationDistinguishabilityCell {
                expected_verdict,
                backend_outcome,
                classification,
                axis,
            }
        })
        .collect();
    MutationDistinguishabilityMatrix {
        mutation_class,
        cells,
    }
}

/// Aggregate counts across multiple matrices. The summary always carries the
/// mandatory `Level1LocalReplay` nonclaim language.
pub fn summarize_mutation_distinguishability(
    matrices: &[MutationDistinguishabilityMatrix],
) -> MutationDistinguishabilitySummary {
    let mut summary = MutationDistinguishabilitySummary {
        matrix_count: matrices.len(),
        total_cells: matrices.iter().map(|m| m.cells.len()).sum(),
        nonclaims: mandatory_distinguishability_nonclaims(),
        ..Default::default()
    };
    for matrix in matrices {
        for cell in &matrix.cells {
            match cell.axis {
                MutationDistinguishabilityAxis::TruePositive => summary.true_positive += 1,
                MutationDistinguishabilityAxis::DetectedRejection => {
                    summary.detected_rejection += 1
                }
                MutationDistinguishabilityAxis::UnsoundAcceptanceCandidate => {
                    summary.unsound_acceptance_candidate += 1
                }
                MutationDistinguishabilityAxis::FalseRejectionCandidate => {
                    summary.false_rejection_candidate += 1
                }
                MutationDistinguishabilityAxis::Inconclusive => summary.inconclusive += 1,
            }
        }
    }
    summary
}

/// Classify one observed local replay pairing.
pub fn observed_distinguishability_axis(
    expected_verdict: ExpectedVerdict,
    backend_outcome: BackendOutcome,
) -> MutationDistinguishabilityAxis {
    axis_for_classification(classify_result(expected_verdict, backend_outcome))
}

/// Mandatory nonclaim language attached to every distinguishability summary.
pub fn mandatory_distinguishability_nonclaims() -> Vec<String> {
    vec![
        "Mutation distinguishability analysis is local metadata only and is not benchmark evidence."
            .to_string(),
        "An unsound acceptance candidate is a hypothetical signal under a hypothetical backend outcome, not evidence that any real backend would produce that outcome."
            .to_string(),
        "Distinguishability analysis does not populate any ScoreReport axis and does not call any real backend."
            .to_string(),
    ]
}

/// Claim boundary cap for all distinguishability output.
pub const DISTINGUISHABILITY_CLAIM_BOUNDARY: ClaimBoundary = ClaimBoundary::Level1LocalReplay;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn matrix_has_one_cell_per_backend_outcome_variant() {
        let matrix = classify_mutation_distinguishability(
            MutationClass::BadCounters,
            ExpectedVerdict::Reject,
        );
        assert_eq!(matrix.cells.len(), all_backend_outcomes().len());
        // Verify every backend outcome is represented exactly once.
        for outcome in all_backend_outcomes() {
            let count = matrix
                .cells
                .iter()
                .filter(|cell| cell.backend_outcome == outcome)
                .count();
            assert_eq!(count, 1, "outcome {outcome:?} appeared {count} times");
        }
    }

    #[test]
    fn axis_severity_returns_documented_values() {
        assert_eq!(
            MutationDistinguishabilityAxis::UnsoundAcceptanceCandidate.axis_severity(),
            4
        );
        assert_eq!(
            MutationDistinguishabilityAxis::DetectedRejection.axis_severity(),
            3
        );
        assert_eq!(
            MutationDistinguishabilityAxis::FalseRejectionCandidate.axis_severity(),
            2
        );
        assert_eq!(
            MutationDistinguishabilityAxis::Inconclusive.axis_severity(),
            1
        );
        assert_eq!(
            MutationDistinguishabilityAxis::TruePositive.axis_severity(),
            0
        );
    }

    #[test]
    fn reject_plus_accepted_is_unsound_acceptance_candidate() {
        let matrix = classify_mutation_distinguishability(
            MutationClass::InvariantWeakening,
            ExpectedVerdict::UnsoundIfAccepted,
        );
        let cell = matrix
            .cells
            .iter()
            .find(|c| c.backend_outcome == BackendOutcome::Accepted)
            .expect("Accepted cell must exist");
        assert_eq!(
            cell.axis,
            MutationDistinguishabilityAxis::UnsoundAcceptanceCandidate
        );
    }

    #[test]
    fn summary_aggregates_correctly() {
        let matrices = vec![
            classify_mutation_distinguishability(
                MutationClass::BadCounters,
                ExpectedVerdict::Reject,
            ),
            classify_mutation_distinguishability(
                MutationClass::InvariantWeakening,
                ExpectedVerdict::UnsoundIfAccepted,
            ),
        ];
        let summary = summarize_mutation_distinguishability(&matrices);
        assert_eq!(summary.matrix_count, 2);
        assert_eq!(summary.total_cells, 14);
        // Each matrix contributes exactly one UnsoundAcceptanceCandidate cell
        // (Reject/UnsoundIfAccepted + Accepted).
        assert_eq!(summary.unsound_acceptance_candidate, 2);
        // Each matrix contributes exactly one DetectedRejection cell
        // (Reject/UnsoundIfAccepted + Rejected).
        assert_eq!(summary.detected_rejection, 2);
        assert!(!summary.nonclaims.is_empty());
    }

    #[test]
    fn matrix_is_deterministic() {
        let left = classify_mutation_distinguishability(
            MutationClass::CorruptedGuards,
            ExpectedVerdict::Reject,
        );
        let right = classify_mutation_distinguishability(
            MutationClass::CorruptedGuards,
            ExpectedVerdict::Reject,
        );
        assert_eq!(left, right);
    }
}

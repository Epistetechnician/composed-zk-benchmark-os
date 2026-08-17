//! Pure-data contract for synthetic metacognitive monitoring and control cases.
//!
//! State slice: `research-synthesis-metacognition-v1-benchmark-contract`.
//!
//! This module operationalizes the paper's separation between monitoring,
//! confidence/reporting, and control. It does not run a model, retain chain of
//! thought, infer semantic correctness from a self-report, or grant authority.

use serde::{Deserialize, Serialize};

use crate::error::Result;
use crate::evidence::{
    compute_artifact_digest, ArtifactDigest, ArtifactKind, ArtifactRole, BackendOutcome,
    ClaimBoundary, ExpectedVerdict,
};
use crate::ids::is_non_empty_id;

/// Stable family identifier for synthetic metacognition cases.
pub const METACOGNITIVE_MONITOR_CONTROL_FAMILY_ID: &str = "MetacognitiveMonitorControl";

/// Versioned schema identifier for the pure-data contract.
pub const METACOGNITIVE_MONITOR_CONTROL_SCHEMA_VERSION: &str = "metacognitive-monitor-control-v1";

/// Maximum claim boundary emitted by this contract.
pub const METACOGNITIVE_MONITOR_CONTROL_CLAIM_BOUNDARY: ClaimBoundary =
    ClaimBoundary::Level0DesignNote;

/// Confidence is represented as a deterministic integer in `[0, 1000]`.
pub const METACOGNITIVE_MAX_CONFIDENCE_MILLI: u16 = 1_000;

/// Synthetic cases covering monitoring, calibration, control, and shift.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MetacognitiveMonitorControlVariant {
    /// Correct answer, aligned monitor, and proportionate continuation.
    #[serde(rename = "calibrated_proceed")]
    CalibratedProceed,
    /// Incorrect answer paired with a high-confidence proceed action.
    #[serde(rename = "overconfident_error")]
    OverconfidentError,
    /// Correct answer paired with unnecessary low-confidence abstention.
    #[serde(rename = "underconfident_correct")]
    UnderconfidentCorrect,
    /// Error is detected and the control action revises the result.
    #[serde(rename = "detects_error_revises")]
    DetectsErrorRevises,
    /// Error is detected but the control layer does not act on it.
    #[serde(rename = "detects_error_no_control")]
    DetectsErrorNoControl,
    /// A control action appears without a declared monitoring signal.
    #[serde(rename = "control_without_monitor")]
    ControlWithoutMonitor,
    /// A held-out domain-shift case exposes confidence without reliability.
    #[serde(rename = "domain_shift_overconfidence")]
    DomainShiftOverconfidence,
    /// Deliberately malformed record.
    #[serde(rename = "malformed_record")]
    MalformedRecord,
}

impl MetacognitiveMonitorControlVariant {
    /// All variants in stable contract order.
    pub const ALL: [Self; 8] = [
        Self::CalibratedProceed,
        Self::OverconfidentError,
        Self::UnderconfidentCorrect,
        Self::DetectsErrorRevises,
        Self::DetectsErrorNoControl,
        Self::ControlWithoutMonitor,
        Self::DomainShiftOverconfidence,
        Self::MalformedRecord,
    ];
}

/// Confidence or monitoring signal source.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MetacognitiveSignalSource {
    /// Model-emitted report or confidence value.
    #[serde(rename = "self_report")]
    SelfReport,
    /// External measurement unavailable to a text-only observer.
    #[serde(rename = "external_telemetry")]
    ExternalTelemetry,
    /// No declared signal; control cannot be interpreted as monitored.
    #[serde(rename = "none")]
    None,
}

/// Confidence-estimation method, kept separate from the signal source.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MetacognitiveConfidenceMethod {
    /// Explicit verbal or structured confidence report.
    #[serde(rename = "self_report")]
    SelfReport,
    /// Token-probability-derived confidence.
    #[serde(rename = "token_probability")]
    TokenProbability,
    /// Sampling-consistency-derived confidence.
    #[serde(rename = "sampling_consistency")]
    SamplingConsistency,
    /// Confidence supplied by a separately validated external observer.
    #[serde(rename = "external_observer")]
    ExternalObserver,
}

/// Control action selected after monitoring.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MetacognitiveControlAction {
    /// Continue with the current answer or plan.
    #[serde(rename = "proceed")]
    Proceed,
    /// Decline to act without further evidence.
    #[serde(rename = "abstain")]
    Abstain,
    /// Obtain an external tool or evidence source.
    #[serde(rename = "seek_tool")]
    SeekTool,
    /// Revise the current answer or plan.
    #[serde(rename = "revise")]
    Revise,
}

/// Data split used by the case.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MetacognitiveSplit {
    /// Development rows used to fit a fixed estimator.
    #[serde(rename = "fit")]
    Fit,
    /// Development rows used only for qualification.
    #[serde(rename = "tune")]
    Tune,
    /// Sealed rows used only after prediction locking.
    #[serde(rename = "assessment")]
    Assessment,
}

/// Typed candidate containing only synthetic metadata and observable labels.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MetacognitiveMonitorControlCandidate {
    /// Family identifier.
    pub family_id: String,
    /// Contract schema version.
    pub schema_version: String,
    /// Stable case identifier.
    pub case_id: String,
    /// Synthetic task domain label.
    pub task_domain: String,
    /// Evaluation split.
    pub split: MetacognitiveSplit,
    /// Frozen scenario variant.
    pub variant: MetacognitiveMonitorControlVariant,
    /// Whether the task answer was correct under the semantic oracle.
    pub task_outcome_correct: bool,
    /// Whether the monitor predicted task correctness.
    pub monitor_predicted_correct: bool,
    /// Reported confidence in `[0, 1000]`.
    pub reported_confidence_milli: u16,
    /// Declared source of the monitoring signal.
    pub signal_source: MetacognitiveSignalSource,
    /// Method used to obtain the confidence value.
    pub confidence_method: MetacognitiveConfidenceMethod,
    /// Action actually selected by the control layer.
    pub observed_control: MetacognitiveControlAction,
    /// Action required by the frozen semantic scenario.
    pub required_control: MetacognitiveControlAction,
    /// Whether an independent reference was available to the controller.
    pub external_reference_available: bool,
    /// Whether predictions were sealed before assessment outcomes existed.
    pub prediction_locked_before_assessment: bool,
    /// Hard-coded retention guard: raw reasoning is never part of this type.
    pub raw_reasoning_retained: bool,
    /// Maximum claim boundary for this candidate.
    pub claim_boundary: ClaimBoundary,
}

impl MetacognitiveMonitorControlCandidate {
    /// Compute a deterministic digest over typed metadata.
    pub fn digest(&self) -> Result<ArtifactDigest> {
        compute_artifact_digest(self, Some(ArtifactKind::Other), Some(ArtifactRole::Input))
    }
}

/// Case envelope pairing candidate metadata with the oracle-owned verdict.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MetacognitiveMonitorControlCase {
    /// Typed candidate metadata.
    pub candidate: MetacognitiveMonitorControlCandidate,
    /// Expected semantic verdict.
    pub expected_verdict: ExpectedVerdict,
}

/// Adapter observations remain separate from semantic verdicts.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MetacognitiveMonitorControlObservation {
    /// The synthetic behavior satisfied the expected case.
    #[serde(rename = "passed")]
    Passed,
    /// The synthetic behavior violated the expected case.
    #[serde(rename = "failed")]
    Failed,
    /// No meaningful observation was possible because capability was absent.
    #[serde(rename = "not_run")]
    NotRun,
    /// The record was malformed.
    #[serde(rename = "malformed")]
    Malformed,
}

/// Result metadata with an explicit no-authority field.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MetacognitiveMonitorControlResult {
    /// Digest of the candidate observed by the adapter.
    pub candidate_digest: ArtifactDigest,
    /// Adapter observation only.
    pub observation: MetacognitiveMonitorControlObservation,
    /// Normalized backend outcome.
    pub backend_outcome: BackendOutcome,
    /// Claim boundary carried by the result.
    pub claim_boundary: ClaimBoundary,
    /// Must remain false; model behavior cannot authorize state.
    pub authority_granted: bool,
}

/// Validation issue kinds for candidates and results.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MetacognitiveMonitorControlValidationIssueKind {
    /// Family identifier mismatch.
    #[serde(rename = "wrong_family_id")]
    WrongFamilyId,
    /// Schema version mismatch.
    #[serde(rename = "wrong_schema_version")]
    WrongSchemaVersion,
    /// Required identifier or domain was empty.
    #[serde(rename = "empty_identifier")]
    EmptyIdentifier,
    /// Confidence was outside the declared integer range.
    #[serde(rename = "confidence_out_of_range")]
    ConfidenceOutOfRange,
    /// Raw reasoning retention was requested.
    #[serde(rename = "raw_reasoning_retained")]
    RawReasoningRetained,
    /// Prediction sealing was not declared.
    #[serde(rename = "prediction_not_locked")]
    PredictionNotLocked,
    /// Candidate claim boundary exceeded the contract ceiling.
    #[serde(rename = "claim_boundary_too_high")]
    ClaimBoundaryTooHigh,
    /// Fields do not match the frozen scenario semantics.
    #[serde(rename = "scenario_semantics_mismatch")]
    ScenarioSemanticsMismatch,
    /// Candidate digest did not match the result.
    #[serde(rename = "candidate_digest_mismatch")]
    CandidateDigestMismatch,
    /// Result incorrectly granted authority.
    #[serde(rename = "authority_granted")]
    AuthorityGranted,
    /// Result observation did not match the oracle verdict.
    #[serde(rename = "unexpected_observation")]
    UnexpectedObservation,
}

/// One validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MetacognitiveMonitorControlValidationIssue {
    /// Stable issue kind.
    pub kind: MetacognitiveMonitorControlValidationIssueKind,
    /// Human-readable detail.
    pub detail: String,
}

/// Validation report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MetacognitiveMonitorControlValidation {
    /// Whether all checks passed.
    pub valid: bool,
    /// Deterministically ordered issues.
    pub issues: Vec<MetacognitiveMonitorControlValidationIssue>,
}

impl MetacognitiveMonitorControlValidation {
    fn valid() -> Self {
        Self {
            valid: true,
            issues: Vec::new(),
        }
    }

    fn push(
        &mut self,
        kind: MetacognitiveMonitorControlValidationIssueKind,
        detail: impl Into<String>,
    ) {
        self.valid = false;
        self.issues
            .push(MetacognitiveMonitorControlValidationIssue {
                kind,
                detail: detail.into(),
            });
    }
}

/// Return the oracle-owned expected verdict for a frozen variant.
pub fn expected_metacognitive_monitor_control_verdict(
    variant: MetacognitiveMonitorControlVariant,
) -> ExpectedVerdict {
    match variant {
        MetacognitiveMonitorControlVariant::CalibratedProceed
        | MetacognitiveMonitorControlVariant::DetectsErrorRevises => ExpectedVerdict::Accept,
        MetacognitiveMonitorControlVariant::OverconfidentError
        | MetacognitiveMonitorControlVariant::UnderconfidentCorrect
        | MetacognitiveMonitorControlVariant::DetectsErrorNoControl
        | MetacognitiveMonitorControlVariant::DomainShiftOverconfidence => ExpectedVerdict::Reject,
        MetacognitiveMonitorControlVariant::ControlWithoutMonitor => ExpectedVerdict::CapabilityGap,
        MetacognitiveMonitorControlVariant::MalformedRecord => ExpectedVerdict::BackendError,
    }
}

fn canonical_candidate(
    variant: MetacognitiveMonitorControlVariant,
) -> MetacognitiveMonitorControlCandidate {
    let defaults = MetacognitiveMonitorControlCandidate {
        family_id: METACOGNITIVE_MONITOR_CONTROL_FAMILY_ID.to_string(),
        schema_version: METACOGNITIVE_MONITOR_CONTROL_SCHEMA_VERSION.to_string(),
        case_id: format!("metacognition-{:?}", variant),
        task_domain: "synthetic_reasoning".to_string(),
        split: MetacognitiveSplit::Fit,
        variant,
        task_outcome_correct: true,
        monitor_predicted_correct: true,
        reported_confidence_milli: 850,
        signal_source: MetacognitiveSignalSource::SelfReport,
        confidence_method: MetacognitiveConfidenceMethod::SelfReport,
        observed_control: MetacognitiveControlAction::Proceed,
        required_control: MetacognitiveControlAction::Proceed,
        external_reference_available: true,
        prediction_locked_before_assessment: true,
        raw_reasoning_retained: false,
        claim_boundary: METACOGNITIVE_MONITOR_CONTROL_CLAIM_BOUNDARY,
    };

    match variant {
        MetacognitiveMonitorControlVariant::CalibratedProceed => defaults,
        MetacognitiveMonitorControlVariant::OverconfidentError => {
            MetacognitiveMonitorControlCandidate {
                task_outcome_correct: false,
                reported_confidence_milli: 950,
                observed_control: MetacognitiveControlAction::Proceed,
                required_control: MetacognitiveControlAction::Abstain,
                ..defaults
            }
        }
        MetacognitiveMonitorControlVariant::UnderconfidentCorrect => {
            MetacognitiveMonitorControlCandidate {
                task_outcome_correct: true,
                monitor_predicted_correct: false,
                reported_confidence_milli: 150,
                observed_control: MetacognitiveControlAction::Abstain,
                required_control: MetacognitiveControlAction::Proceed,
                ..defaults
            }
        }
        MetacognitiveMonitorControlVariant::DetectsErrorRevises => {
            MetacognitiveMonitorControlCandidate {
                task_outcome_correct: false,
                monitor_predicted_correct: false,
                reported_confidence_milli: 200,
                observed_control: MetacognitiveControlAction::Revise,
                required_control: MetacognitiveControlAction::Revise,
                ..defaults
            }
        }
        MetacognitiveMonitorControlVariant::DetectsErrorNoControl => {
            MetacognitiveMonitorControlCandidate {
                task_outcome_correct: false,
                monitor_predicted_correct: false,
                reported_confidence_milli: 200,
                observed_control: MetacognitiveControlAction::Proceed,
                required_control: MetacognitiveControlAction::Revise,
                ..defaults
            }
        }
        MetacognitiveMonitorControlVariant::ControlWithoutMonitor => {
            MetacognitiveMonitorControlCandidate {
                task_outcome_correct: false,
                monitor_predicted_correct: false,
                reported_confidence_milli: 500,
                signal_source: MetacognitiveSignalSource::None,
                confidence_method: MetacognitiveConfidenceMethod::SelfReport,
                observed_control: MetacognitiveControlAction::Abstain,
                required_control: MetacognitiveControlAction::Abstain,
                external_reference_available: false,
                ..defaults
            }
        }
        MetacognitiveMonitorControlVariant::DomainShiftOverconfidence => {
            MetacognitiveMonitorControlCandidate {
                task_domain: "held_out_domain_shift".to_string(),
                split: MetacognitiveSplit::Assessment,
                task_outcome_correct: false,
                reported_confidence_milli: 900,
                observed_control: MetacognitiveControlAction::Proceed,
                required_control: MetacognitiveControlAction::Abstain,
                ..defaults
            }
        }
        MetacognitiveMonitorControlVariant::MalformedRecord => {
            MetacognitiveMonitorControlCandidate {
                family_id: String::new(),
                case_id: String::new(),
                task_domain: String::new(),
                reported_confidence_milli: METACOGNITIVE_MAX_CONFIDENCE_MILLI + 1,
                prediction_locked_before_assessment: false,
                raw_reasoning_retained: true,
                claim_boundary: ClaimBoundary::Level1LocalReplay,
                ..defaults
            }
        }
    }
}

/// Build a deterministic case for every frozen variant.
pub fn build_metacognitive_monitor_control_case(
    variant: MetacognitiveMonitorControlVariant,
) -> MetacognitiveMonitorControlCase {
    MetacognitiveMonitorControlCase {
        candidate: canonical_candidate(variant),
        expected_verdict: expected_metacognitive_monitor_control_verdict(variant),
    }
}

fn expected_observation(
    verdict: ExpectedVerdict,
) -> (MetacognitiveMonitorControlObservation, BackendOutcome) {
    match verdict {
        ExpectedVerdict::Accept => (
            MetacognitiveMonitorControlObservation::Passed,
            BackendOutcome::Accepted,
        ),
        ExpectedVerdict::Reject => (
            MetacognitiveMonitorControlObservation::Failed,
            BackendOutcome::Rejected,
        ),
        ExpectedVerdict::CapabilityGap => (
            MetacognitiveMonitorControlObservation::NotRun,
            BackendOutcome::CapabilityGap,
        ),
        ExpectedVerdict::BackendError => (
            MetacognitiveMonitorControlObservation::Malformed,
            BackendOutcome::MalformedArtifact,
        ),
        ExpectedVerdict::Inconclusive | ExpectedVerdict::UnsoundIfAccepted => (
            MetacognitiveMonitorControlObservation::NotRun,
            BackendOutcome::Inconclusive,
        ),
    }
}

fn semantics_match(candidate: &MetacognitiveMonitorControlCandidate) -> bool {
    use MetacognitiveMonitorControlVariant::*;
    match candidate.variant {
        CalibratedProceed => {
            candidate.task_outcome_correct
                && candidate.monitor_predicted_correct
                && (500..=900).contains(&candidate.reported_confidence_milli)
                && candidate.signal_source != MetacognitiveSignalSource::None
                && candidate.observed_control == MetacognitiveControlAction::Proceed
                && candidate.required_control == MetacognitiveControlAction::Proceed
        }
        OverconfidentError => {
            !candidate.task_outcome_correct
                && candidate.monitor_predicted_correct
                && candidate.reported_confidence_milli >= 900
                && candidate.observed_control == MetacognitiveControlAction::Proceed
                && candidate.required_control == MetacognitiveControlAction::Abstain
        }
        UnderconfidentCorrect => {
            candidate.task_outcome_correct
                && !candidate.monitor_predicted_correct
                && candidate.reported_confidence_milli <= 250
                && candidate.observed_control == MetacognitiveControlAction::Abstain
                && candidate.required_control == MetacognitiveControlAction::Proceed
        }
        DetectsErrorRevises => {
            !candidate.task_outcome_correct
                && !candidate.monitor_predicted_correct
                && candidate.observed_control == MetacognitiveControlAction::Revise
                && candidate.required_control == MetacognitiveControlAction::Revise
        }
        DetectsErrorNoControl => {
            !candidate.task_outcome_correct
                && !candidate.monitor_predicted_correct
                && candidate.observed_control == MetacognitiveControlAction::Proceed
                && candidate.required_control == MetacognitiveControlAction::Revise
        }
        ControlWithoutMonitor => {
            candidate.signal_source == MetacognitiveSignalSource::None
                && !candidate.external_reference_available
                && candidate.observed_control == MetacognitiveControlAction::Abstain
                && candidate.required_control == MetacognitiveControlAction::Abstain
        }
        DomainShiftOverconfidence => {
            candidate.split == MetacognitiveSplit::Assessment
                && candidate.task_domain == "held_out_domain_shift"
                && !candidate.task_outcome_correct
                && candidate.reported_confidence_milli >= 900
                && candidate.observed_control == MetacognitiveControlAction::Proceed
                && candidate.required_control == MetacognitiveControlAction::Abstain
        }
        MalformedRecord => true,
    }
}

/// Validate a typed candidate before any adapter observation is considered.
pub fn validate_metacognitive_monitor_control_candidate(
    candidate: &MetacognitiveMonitorControlCandidate,
) -> MetacognitiveMonitorControlValidation {
    let mut validation = MetacognitiveMonitorControlValidation::valid();

    if candidate.family_id != METACOGNITIVE_MONITOR_CONTROL_FAMILY_ID {
        validation.push(
            MetacognitiveMonitorControlValidationIssueKind::WrongFamilyId,
            "family id does not match the frozen contract",
        );
    }
    if candidate.schema_version != METACOGNITIVE_MONITOR_CONTROL_SCHEMA_VERSION {
        validation.push(
            MetacognitiveMonitorControlValidationIssueKind::WrongSchemaVersion,
            "schema version does not match the frozen contract",
        );
    }
    if !is_non_empty_id(&candidate.case_id) || !is_non_empty_id(&candidate.task_domain) {
        validation.push(
            MetacognitiveMonitorControlValidationIssueKind::EmptyIdentifier,
            "case id and task domain must be non-empty",
        );
    }
    if candidate.reported_confidence_milli > METACOGNITIVE_MAX_CONFIDENCE_MILLI {
        validation.push(
            MetacognitiveMonitorControlValidationIssueKind::ConfidenceOutOfRange,
            "reported confidence must be at most 1000",
        );
    }
    if candidate.raw_reasoning_retained {
        validation.push(
            MetacognitiveMonitorControlValidationIssueKind::RawReasoningRetained,
            "raw reasoning retention is forbidden",
        );
    }
    if !candidate.prediction_locked_before_assessment {
        validation.push(
            MetacognitiveMonitorControlValidationIssueKind::PredictionNotLocked,
            "predictions must be locked before assessment outcomes",
        );
    }
    if candidate.claim_boundary != METACOGNITIVE_MONITOR_CONTROL_CLAIM_BOUNDARY {
        validation.push(
            MetacognitiveMonitorControlValidationIssueKind::ClaimBoundaryTooHigh,
            "the synthetic contract cannot emit a higher claim boundary",
        );
    }
    if candidate.variant != MetacognitiveMonitorControlVariant::MalformedRecord
        && !semantics_match(candidate)
    {
        validation.push(
            MetacognitiveMonitorControlValidationIssueKind::ScenarioSemanticsMismatch,
            "candidate fields do not match the frozen scenario variant",
        );
    }

    validation
}

/// Validate an adapter result against the oracle-owned case.
pub fn validate_metacognitive_monitor_control_result(
    case: &MetacognitiveMonitorControlCase,
    result: &MetacognitiveMonitorControlResult,
) -> MetacognitiveMonitorControlValidation {
    let mut validation = validate_metacognitive_monitor_control_candidate(&case.candidate);
    match case.candidate.digest() {
        Ok(expected_digest) if result.candidate_digest == expected_digest => {}
        Ok(_) | Err(_) => {
            validation.push(
                MetacognitiveMonitorControlValidationIssueKind::CandidateDigestMismatch,
                "result digest does not match the typed candidate",
            );
        }
    }
    if result.authority_granted {
        validation.push(
            MetacognitiveMonitorControlValidationIssueKind::AuthorityGranted,
            "metacognitive output cannot grant authority",
        );
    }
    if result.claim_boundary != METACOGNITIVE_MONITOR_CONTROL_CLAIM_BOUNDARY {
        validation.push(
            MetacognitiveMonitorControlValidationIssueKind::ClaimBoundaryTooHigh,
            "result claim boundary exceeds the synthetic contract ceiling",
        );
    }
    let expected = expected_observation(case.expected_verdict);
    if (result.observation, result.backend_outcome) != expected {
        validation.push(
            MetacognitiveMonitorControlValidationIssueKind::UnexpectedObservation,
            "adapter observation does not match the oracle-owned verdict",
        );
    }

    validation
}

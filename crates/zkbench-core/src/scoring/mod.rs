//! Score Report primitives.
//!
//! The current implementation intentionally avoids fake performance or formal
//! scores. It can produce a low-confidence report that records missing evidence.

pub mod distinguishability;

use serde::{Deserialize, Serialize};

use crate::evidence::{ClaimBoundary, EvidenceRecord};

pub use distinguishability::{
    classify_mutation_distinguishability, mandatory_distinguishability_nonclaims,
    observed_distinguishability_axis, summarize_mutation_distinguishability,
    MutationDistinguishabilityAxis, MutationDistinguishabilityCell,
    MutationDistinguishabilityMatrix, MutationDistinguishabilitySummary,
    DISTINGUISHABILITY_CLAIM_BOUNDARY,
};

/// Multi-axis Score Report primitive.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ScoreReport {
    /// Evidence records considered.
    pub evidence_count: usize,
    /// Maximum claim boundary observed in evidence records.
    pub claim_boundary_max: ClaimBoundary,
    /// Overall confidence.
    pub confidence: ScoreConfidence,
    /// Performance score.
    #[serde(default)]
    pub performance: Option<PerformanceScore>,
    /// Correctness score.
    #[serde(default)]
    pub correctness: Option<CorrectnessScore>,
    /// Soundness-failure detection score.
    #[serde(default)]
    pub soundness_failure_detection: Option<SoundnessFailureDetectionScore>,
    /// Recursion stress score.
    #[serde(default)]
    pub recursion_stress: Option<RecursionStressScore>,
    /// Formal evidence score.
    #[serde(default)]
    pub formal_evidence: Option<FormalEvidenceScore>,
    /// Reproducibility score.
    #[serde(default)]
    pub reproducibility: Option<ReproducibilityScore>,
    /// Adapter portability score.
    #[serde(default)]
    pub adapter_portability: Option<AdapterPortabilityScore>,
    /// Risk penalties.
    #[serde(default)]
    pub risk_penalties: Vec<RiskPenalty>,
    /// Missing data notes.
    #[serde(default)]
    pub missing_data: Vec<String>,
    /// Report notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Score report validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ScoreReportValidationIssue {
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
}

/// Score report validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ScoreReportValidation {
    /// True when validation found no issues.
    pub valid: bool,
    /// Validation issues.
    pub issues: Vec<ScoreReportValidationIssue>,
}

/// Score confidence.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ScoreConfidence {
    /// Design-only or incomplete evidence.
    Low,
    /// Local replay with artifacts.
    Medium,
    /// Reproducible benchmark artifact and deterministic replay.
    High,
    /// Machine-checked property for a scoped layer.
    ScopedProof,
    /// Independently reproduced evidence.
    Independent,
}

/// Performance score primitive.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PerformanceScore {
    /// Optional normalized score. None means not enough evidence.
    #[serde(default)]
    pub normalized_score: Option<f64>,
    /// Confidence.
    pub confidence: ScoreConfidence,
    /// Missing metrics.
    #[serde(default)]
    pub missing_metrics: Vec<String>,
}

/// Correctness score primitive.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CorrectnessScore {
    /// Optional alignment score.
    #[serde(default)]
    pub alignment_score: Option<f64>,
    /// Confidence.
    pub confidence: ScoreConfidence,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Soundness-failure detection score primitive.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SoundnessFailureDetectionScore {
    /// Optional negative-test coverage score.
    #[serde(default)]
    pub negative_test_coverage: Option<f64>,
    /// Confidence.
    pub confidence: ScoreConfidence,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Recursion stress score primitive.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct RecursionStressScore {
    /// Optional recursion depth score.
    #[serde(default)]
    pub recursion_depth_score: Option<f64>,
    /// Confidence.
    pub confidence: ScoreConfidence,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Formal evidence score primitive.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FormalEvidenceScore {
    /// Optional scoped proof score.
    #[serde(default)]
    pub scoped_proof_score: Option<f64>,
    /// Confidence.
    pub confidence: ScoreConfidence,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Reproducibility score primitive.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ReproducibilityScore {
    /// Optional reproducibility score.
    #[serde(default)]
    pub reproducibility_score: Option<f64>,
    /// Confidence.
    pub confidence: ScoreConfidence,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Adapter portability score primitive.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AdapterPortabilityScore {
    /// Optional portability score.
    #[serde(default)]
    pub portability_score: Option<f64>,
    /// Confidence.
    pub confidence: ScoreConfidence,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Risk penalty primitive.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum RiskPenalty {
    /// Evidence is missing.
    MissingEvidence { reason: String },
    /// A capability gap limits interpretation.
    CapabilityGap { capability: String },
    /// Claim boundary would be overclaimed if promoted.
    OverclaimRisk { reason: String },
    /// Outcome was inconclusive.
    Inconclusive { reason: String },
}

/// Local mutation/oracle evidence summary. Counts are local semantic evidence
/// only and must not be interpreted as benchmark performance or formal proof.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct LocalMutationEvidenceSummary {
    /// Local accepted traces observed.
    pub local_accepted_traces: usize,
    /// Local rejected traces observed.
    pub local_rejected_traces: usize,
    /// Mutation variants generated.
    pub mutation_variants_generated: usize,
    /// Outcome changes observed under local oracle evaluation.
    pub outcome_changes_observed: usize,
    /// Unsound acceptance candidates under mock classification.
    pub unsound_acceptance_candidates: usize,
}

/// Build a conservative Score Report from evidence records.
pub fn score_report_from_evidence(evidence: &[EvidenceRecord]) -> ScoreReport {
    let claim_boundary_max = evidence
        .iter()
        .map(|record| record.claim_boundary)
        .max()
        .unwrap_or(ClaimBoundary::Level0DesignNote);

    let confidence = match claim_boundary_max {
        ClaimBoundary::Level0DesignNote | ClaimBoundary::Level1LocalReplay => ScoreConfidence::Low,
        ClaimBoundary::Level2ReproducibleBenchmarkArtifact
        | ClaimBoundary::Level3CrossBackendReplay => ScoreConfidence::High,
        ClaimBoundary::Level4FormalPropertyStatement
        | ClaimBoundary::Level5MachineCheckedScopedProof => ScoreConfidence::ScopedProof,
        ClaimBoundary::Level6IndependentlyReproducedEvidence => ScoreConfidence::Independent,
    };

    ScoreReport {
        evidence_count: evidence.len(),
        claim_boundary_max,
        confidence,
        performance: None,
        correctness: None,
        soundness_failure_detection: None,
        recursion_stress: None,
        formal_evidence: None,
        reproducibility: None,
        adapter_portability: None,
        risk_penalties: vec![RiskPenalty::MissingEvidence {
            reason: "score axes require backend evidence from future phases".to_string(),
        }],
        missing_data: vec![
            "prover time".to_string(),
            "verifier latency".to_string(),
            "proof size".to_string(),
            "constraint count".to_string(),
            "formal proof status".to_string(),
        ],
        notes: vec![
            "ScoreReport is a primitive container in this phase; no meaningful benchmark score is calculated.".to_string(),
        ],
    }
}

/// Build a conservative Score Report from local mutation/oracle evidence.
pub fn score_report_from_local_mutation_evidence(
    summary: LocalMutationEvidenceSummary,
) -> ScoreReport {
    let mut report = score_report_from_evidence(&[]);
    report.claim_boundary_max = ClaimBoundary::Level1LocalReplay;
    report.confidence = ScoreConfidence::Low;
    report.risk_penalties.push(RiskPenalty::OverclaimRisk {
        reason: "local mutation/oracle counts are not official benchmark evidence".to_string(),
    });
    report.notes.push(format!(
        "local accepted traces: {}; local rejected traces: {}; mutation variants: {}; local outcome changes: {}; unsound acceptance candidates: {}",
        summary.local_accepted_traces,
        summary.local_rejected_traces,
        summary.mutation_variants_generated,
        summary.outcome_changes_observed,
        summary.unsound_acceptance_candidates
    ));
    report
}

/// Validate that a score report stays within current local claim boundaries.
pub fn validate_score_report(report: &ScoreReport) -> ScoreReportValidation {
    let mut issues = Vec::new();
    if report.claim_boundary_max <= ClaimBoundary::Level1LocalReplay {
        push_local_axis_issue("performance", report.performance.is_some(), &mut issues);
        push_local_axis_issue("correctness", report.correctness.is_some(), &mut issues);
        push_local_axis_issue(
            "soundness_failure_detection",
            report.soundness_failure_detection.is_some(),
            &mut issues,
        );
        push_local_axis_issue(
            "recursion_stress",
            report.recursion_stress.is_some(),
            &mut issues,
        );
        push_local_axis_issue(
            "formal_evidence",
            report.formal_evidence.is_some(),
            &mut issues,
        );
        push_local_axis_issue(
            "reproducibility",
            report.reproducibility.is_some(),
            &mut issues,
        );
        push_local_axis_issue(
            "adapter_portability",
            report.adapter_portability.is_some(),
            &mut issues,
        );
    }

    for (index, note) in report.notes.iter().enumerate() {
        push_forbidden_claim_text_issue(format!("notes[{index}]"), note, &mut issues);
    }
    for (index, penalty) in report.risk_penalties.iter().enumerate() {
        match penalty {
            RiskPenalty::MissingEvidence { reason }
            | RiskPenalty::OverclaimRisk { reason }
            | RiskPenalty::Inconclusive { reason } => {
                push_forbidden_claim_text_issue(
                    format!("risk_penalties[{index}].reason"),
                    reason,
                    &mut issues,
                );
            }
            RiskPenalty::CapabilityGap { capability } => {
                push_forbidden_claim_text_issue(
                    format!("risk_penalties[{index}].capability"),
                    capability,
                    &mut issues,
                );
            }
        }
    }
    if let Some(score) = &report.performance {
        push_score_value_issue(
            "performance.normalized_score",
            score.normalized_score,
            &mut issues,
        );
    }
    if let Some(score) = &report.correctness {
        push_score_value_issue(
            "correctness.alignment_score",
            score.alignment_score,
            &mut issues,
        );
        for (index, note) in score.notes.iter().enumerate() {
            push_forbidden_claim_text_issue(
                format!("correctness.notes[{index}]"),
                note,
                &mut issues,
            );
        }
    }
    if let Some(score) = &report.soundness_failure_detection {
        push_score_value_issue(
            "soundness_failure_detection.negative_test_coverage",
            score.negative_test_coverage,
            &mut issues,
        );
        for (index, note) in score.notes.iter().enumerate() {
            push_forbidden_claim_text_issue(
                format!("soundness_failure_detection.notes[{index}]"),
                note,
                &mut issues,
            );
        }
    }
    if let Some(score) = &report.recursion_stress {
        push_score_value_issue(
            "recursion_stress.recursion_depth_score",
            score.recursion_depth_score,
            &mut issues,
        );
        for (index, note) in score.notes.iter().enumerate() {
            push_forbidden_claim_text_issue(
                format!("recursion_stress.notes[{index}]"),
                note,
                &mut issues,
            );
        }
    }
    if let Some(score) = &report.formal_evidence {
        push_score_value_issue(
            "formal_evidence.scoped_proof_score",
            score.scoped_proof_score,
            &mut issues,
        );
        for (index, note) in score.notes.iter().enumerate() {
            push_forbidden_claim_text_issue(
                format!("formal_evidence.notes[{index}]"),
                note,
                &mut issues,
            );
        }
    }
    if let Some(score) = &report.reproducibility {
        push_score_value_issue(
            "reproducibility.reproducibility_score",
            score.reproducibility_score,
            &mut issues,
        );
        for (index, note) in score.notes.iter().enumerate() {
            push_forbidden_claim_text_issue(
                format!("reproducibility.notes[{index}]"),
                note,
                &mut issues,
            );
        }
    }
    if let Some(score) = &report.adapter_portability {
        push_score_value_issue(
            "adapter_portability.portability_score",
            score.portability_score,
            &mut issues,
        );
        for (index, note) in score.notes.iter().enumerate() {
            push_forbidden_claim_text_issue(
                format!("adapter_portability.notes[{index}]"),
                note,
                &mut issues,
            );
        }
    }

    ScoreReportValidation {
        valid: issues.is_empty(),
        issues,
    }
}

fn push_local_axis_issue(
    path: &'static str,
    present: bool,
    issues: &mut Vec<ScoreReportValidationIssue>,
) {
    if present {
        issues.push(ScoreReportValidationIssue {
            path: path.to_string(),
            message: "local score reports must leave score axes unpopulated".to_string(),
        });
    }
}

fn push_score_value_issue(
    path: &'static str,
    value: Option<f64>,
    issues: &mut Vec<ScoreReportValidationIssue>,
) {
    let Some(value) = value else {
        return;
    };
    if !value.is_finite() || !(0.0..=1.0).contains(&value) {
        issues.push(ScoreReportValidationIssue {
            path: path.to_string(),
            message: "score value must be finite and between 0.0 and 1.0".to_string(),
        });
    }
}

fn push_forbidden_claim_text_issue(
    path: String,
    text: &str,
    issues: &mut Vec<ScoreReportValidationIssue>,
) {
    if contains_forbidden_score_report_claim_text(text) {
        issues.push(ScoreReportValidationIssue {
            path,
            message: "score report text contains forbidden claim language".to_string(),
        });
    }
}

fn contains_forbidden_score_report_claim_text(text: &str) -> bool {
    let lowered = text.to_ascii_lowercase();
    if lowered.contains("not official benchmark evidence")
        || lowered.contains("not official benchmark result")
        || lowered.contains("no official benchmark evidence")
        || lowered.contains("no official benchmark result")
        || lowered.contains("does not create official benchmark evidence")
        || lowered.contains("does not create official benchmark result")
    {
        return false;
    }
    crate::external_runner::contains_forbidden_claim_text(text)
}

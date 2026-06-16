//! Level2 eligibility checker primitives.
//!
//! Eligibility reports are review artifacts. They can identify whether a
//! candidate has enough metadata for a future Level2 review, but they never
//! create Level2 evidence.

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};

use super::candidate::{validate_evidence_record_candidate, EvidenceRecordCandidate};
use super::review::EvidenceReviewFindingSeverity;
use super::ClaimBoundary;

/// Level2 eligibility status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum Level2EligibilityStatus {
    /// Candidate is not eligible for future Level2 review.
    NotEligible,
    /// Candidate has enough local metadata for future human Level2 review.
    EligibleForFutureReview,
    /// Candidate is blocked.
    Blocked,
    /// Candidate lacks information needed for an eligibility decision.
    InsufficientInformation,
}

/// Level2 eligibility blocking reason.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum Level2EligibilityBlockingReason {
    /// Candidate validation failed.
    CandidateInvalid,
    /// External artifact capture is missing.
    MissingExternalArtifactCapture,
    /// Replay manifest is missing.
    MissingReplayManifest,
    /// Provenance is missing.
    MissingProvenance,
    /// Artifact digest is missing.
    MissingArtifactDigest,
    /// Forbidden official claim language or flags were detected.
    OfficialClaimDetected,
    /// Formal claim language or flags were detected.
    FormalClaimDetected,
    /// Proof-system soundness claim language or flags were detected.
    SoundnessClaimDetected,
    /// Candidate attempted to become Level2 actual evidence.
    Level2ActualEvidenceBlocked,
}

/// Level2 eligibility requirement.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Level2EligibilityRequirement {
    /// Requirement id.
    pub id: String,
    /// Requirement description.
    pub description: String,
    /// Whether this requirement is required.
    pub required: bool,
    /// Whether this requirement is satisfied.
    pub satisfied: bool,
}

/// Level2 eligibility finding.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Level2EligibilityFinding {
    /// Finding id.
    pub id: String,
    /// Finding message.
    pub message: String,
    /// Finding severity.
    pub severity: EvidenceReviewFindingSeverity,
    /// Optional blocking reason.
    #[serde(default)]
    pub blocking_reason: Option<Level2EligibilityBlockingReason>,
}

/// Level2 eligibility report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Level2EligibilityReport {
    /// Report id.
    pub id: String,
    /// Source candidate id.
    pub source_candidate_id: String,
    /// Eligibility status.
    pub status: Level2EligibilityStatus,
    /// Requirements.
    pub requirements: Vec<Level2EligibilityRequirement>,
    /// Findings.
    #[serde(default)]
    pub findings: Vec<Level2EligibilityFinding>,
    /// Blocking reasons.
    #[serde(default)]
    pub blocking_reasons: Vec<Level2EligibilityBlockingReason>,
    /// Claim boundary of this report artifact.
    pub claim_boundary: ClaimBoundary,
    /// This is always false in Phase J.
    pub creates_level2_evidence: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Level2EligibilityReport {
    /// Eligibility reports do not create Level2 evidence in Phase J.
    pub fn creates_level2_evidence(&self) -> bool {
        false
    }
}

/// Local checker configuration.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Level2EligibilityChecker {
    /// Require an external artifact capture marker for eligibility.
    pub require_external_artifact_capture: bool,
    /// Require a replay manifest marker for eligibility.
    pub require_replay_manifest: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for Level2EligibilityChecker {
    fn default() -> Self {
        Self {
            require_external_artifact_capture: false,
            require_replay_manifest: false,
            notes: vec![
                "Eligibility checks are review metadata only.".to_string(),
                "Future artifacts and human review would be required before Level2 evidence."
                    .to_string(),
            ],
        }
    }
}

impl Level2EligibilityChecker {
    /// Check whether a candidate is eligible for future Level2 review.
    pub fn check(&self, candidate: &EvidenceRecordCandidate) -> Result<Level2EligibilityReport> {
        let mut requirements = Vec::new();
        let mut findings = Vec::new();
        let mut blocking_reasons = Vec::new();

        let candidate_validation = validate_evidence_record_candidate(candidate);
        add_requirement(
            &mut requirements,
            "candidate_valid",
            "candidate validates locally",
            candidate_validation.valid,
        );
        if !candidate_validation.valid {
            blocking_reasons.push(Level2EligibilityBlockingReason::CandidateInvalid);
            findings.push(finding(
                "candidate_invalid",
                format!(
                    "candidate validation failed: {:?}",
                    candidate_validation.issues
                ),
                EvidenceReviewFindingSeverity::Blocking,
                Some(Level2EligibilityBlockingReason::CandidateInvalid),
            ));
        }

        let has_artifact_digest = !candidate.proposed_artifact_refs.is_empty()
            || candidate.validation_report_digest.is_some();
        add_requirement(
            &mut requirements,
            "artifact_digests_present",
            "artifact digest metadata is present",
            has_artifact_digest,
        );
        if !has_artifact_digest {
            blocking_reasons.push(Level2EligibilityBlockingReason::MissingArtifactDigest);
        }

        let has_provenance = !candidate.proposed_provenance_summary.is_empty();
        add_requirement(
            &mut requirements,
            "provenance_present",
            "provenance summary is present",
            has_provenance,
        );
        if !has_provenance {
            blocking_reasons.push(Level2EligibilityBlockingReason::MissingProvenance);
        }

        let has_external_capture_marker = candidate.notes.iter().any(|note| {
            note.to_ascii_lowercase()
                .contains("external artifact capture reviewed")
        });
        add_requirement(
            &mut requirements,
            "external_artifact_capture_marker",
            "external artifact capture marker is present when required",
            !self.require_external_artifact_capture || has_external_capture_marker,
        );
        if self.require_external_artifact_capture && !has_external_capture_marker {
            blocking_reasons.push(Level2EligibilityBlockingReason::MissingExternalArtifactCapture);
        }

        let has_replay_manifest_marker = candidate.notes.iter().any(|note| {
            note.to_ascii_lowercase()
                .contains("replay manifest reviewed")
        });
        add_requirement(
            &mut requirements,
            "replay_manifest_marker",
            "replay manifest marker is present when required",
            !self.require_replay_manifest || has_replay_manifest_marker,
        );
        if self.require_replay_manifest && !has_replay_manifest_marker {
            blocking_reasons.push(Level2EligibilityBlockingReason::MissingReplayManifest);
        }

        if candidate.claims_official_benchmark_evidence {
            blocking_reasons.push(Level2EligibilityBlockingReason::OfficialClaimDetected);
        }
        if candidate.claims_formal_evidence {
            blocking_reasons.push(Level2EligibilityBlockingReason::FormalClaimDetected);
        }
        if candidate.claims_proof_system_soundness {
            blocking_reasons.push(Level2EligibilityBlockingReason::SoundnessClaimDetected);
        }
        if candidate.proposed_claim_boundary >= ClaimBoundary::Level2ReproducibleBenchmarkArtifact {
            blocking_reasons.push(Level2EligibilityBlockingReason::Level2ActualEvidenceBlocked);
        }

        let status = if blocking_reasons.iter().any(|reason| {
            matches!(
                reason,
                Level2EligibilityBlockingReason::CandidateInvalid
                    | Level2EligibilityBlockingReason::OfficialClaimDetected
                    | Level2EligibilityBlockingReason::FormalClaimDetected
                    | Level2EligibilityBlockingReason::SoundnessClaimDetected
                    | Level2EligibilityBlockingReason::Level2ActualEvidenceBlocked
            )
        }) {
            Level2EligibilityStatus::Blocked
        } else if blocking_reasons.is_empty() {
            Level2EligibilityStatus::EligibleForFutureReview
        } else if blocking_reasons.iter().any(|reason| {
            matches!(
                reason,
                Level2EligibilityBlockingReason::MissingArtifactDigest
                    | Level2EligibilityBlockingReason::MissingProvenance
                    | Level2EligibilityBlockingReason::MissingExternalArtifactCapture
                    | Level2EligibilityBlockingReason::MissingReplayManifest
            )
        }) {
            Level2EligibilityStatus::InsufficientInformation
        } else {
            Level2EligibilityStatus::NotEligible
        };

        Ok(Level2EligibilityReport {
            id: format!("level2_eligibility_{}", candidate.id),
            source_candidate_id: candidate.id.clone(),
            status,
            requirements,
            findings,
            blocking_reasons,
            claim_boundary: ClaimBoundary::Level0DesignNote,
            creates_level2_evidence: false,
            notes: vec![
                "Level2 eligibility is not Level2 evidence.".to_string(),
                "Eligibility reports do not append accepted evidence.".to_string(),
            ],
        })
    }
}

/// Check Level2 eligibility with the default checker.
pub fn check_level2_eligibility(
    candidate: &EvidenceRecordCandidate,
) -> Result<Level2EligibilityReport> {
    Level2EligibilityChecker::default().check(candidate)
}

/// Serialize a Level2 eligibility report to pretty JSON.
pub fn serialize_level2_eligibility_report_json(
    report: &Level2EligibilityReport,
) -> Result<String> {
    serde_json::to_string_pretty(report).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_level2_eligibility_report_json",
            error.to_string(),
        )
    })
}

/// Deserialize a Level2 eligibility report from JSON.
pub fn deserialize_level2_eligibility_report_json(json: &str) -> Result<Level2EligibilityReport> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_level2_eligibility_report_json",
            error.to_string(),
        )
    })
}

fn add_requirement(
    requirements: &mut Vec<Level2EligibilityRequirement>,
    id: impl Into<String>,
    description: impl Into<String>,
    satisfied: bool,
) {
    requirements.push(Level2EligibilityRequirement {
        id: id.into(),
        description: description.into(),
        required: true,
        satisfied,
    });
}

fn finding(
    id: impl Into<String>,
    message: impl Into<String>,
    severity: EvidenceReviewFindingSeverity,
    blocking_reason: Option<Level2EligibilityBlockingReason>,
) -> Level2EligibilityFinding {
    Level2EligibilityFinding {
        id: id.into(),
        message: message.into(),
        severity,
        blocking_reason,
    }
}

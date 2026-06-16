//! Level2 eligibility evaluation for reproduction metadata.

use serde::{Deserialize, Serialize};

use crate::evidence::ClaimBoundary;
use crate::pack::BenchmarkPackReader;

use super::metadata::BenchmarkPackReproductionMetadata;

/// Level2 eligibility report schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Level2EligibilityReportVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for Level2EligibilityReportVersion {
    fn default() -> Self {
        Self {
            value: "phase-m-level2-eligibility-report-v0".to_string(),
        }
    }
}

/// Level2 eligibility status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum Level2EligibilityStatus {
    /// Metadata only; not eligible for Level2 promotion.
    MetadataOnly,
    /// Prerequisites missing for scoped Level2 promotion.
    Blocked,
    /// Future reviewed promotion may be possible after H-J artifacts exist.
    FutureReviewRequired,
}

/// Blocking reason for Level2 eligibility.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum Level2EligibilityBlockingReason {
    /// External replay plans are inert only.
    ExternalPlansInertOnly,
    /// No reviewed external result candidate exists.
    MissingReviewedExternalResultCandidate,
    /// No reproducible external artifact digests exist.
    MissingReproducibleExternalArtifacts,
    /// Source pack remains Level1 local replay only.
    SourcePackRemainsLevel1LocalReplay,
    /// Phase J blocks Level2 actual evidence.
    PhaseJBlocksLevel2ActualEvidence,
    /// Reproduction metadata is design-note only.
    ReproductionMetadataDesignNoteOnly,
}

/// Level2 eligibility report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Level2EligibilityReport {
    /// Report version.
    pub version: Level2EligibilityReportVersion,
    /// Eligibility status.
    pub status: Level2EligibilityStatus,
    /// Whether scoped Level2 promotion is currently eligible.
    pub eligible: bool,
    /// Blocking reasons.
    pub blocking_reasons: Vec<Level2EligibilityBlockingReason>,
    /// Claim boundary for this report.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Evaluate Level2 eligibility for a pack with reproduction metadata.
pub fn evaluate_level2_eligibility(
    reader: &BenchmarkPackReader,
    metadata: &BenchmarkPackReproductionMetadata,
) -> Level2EligibilityReport {
    let mut blocking_reasons = vec![
        Level2EligibilityBlockingReason::ExternalPlansInertOnly,
        Level2EligibilityBlockingReason::MissingReviewedExternalResultCandidate,
        Level2EligibilityBlockingReason::MissingReproducibleExternalArtifacts,
        Level2EligibilityBlockingReason::PhaseJBlocksLevel2ActualEvidence,
        Level2EligibilityBlockingReason::ReproductionMetadataDesignNoteOnly,
    ];
    if reader.manifest().claim_boundary == ClaimBoundary::Level1LocalReplay {
        blocking_reasons.push(Level2EligibilityBlockingReason::SourcePackRemainsLevel1LocalReplay);
    }
    if !metadata.attachments_are_inert() {
        blocking_reasons.push(Level2EligibilityBlockingReason::ExternalPlansInertOnly);
    }
    Level2EligibilityReport {
        version: Level2EligibilityReportVersion::default(),
        status: Level2EligibilityStatus::Blocked,
        eligible: false,
        blocking_reasons,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec![
            "Level2 eligibility is not Level2 evidence.".to_string(),
            "Reviewed external result candidates and reproducible artifacts are required before scoped promotion.".to_string(),
        ],
    }
}

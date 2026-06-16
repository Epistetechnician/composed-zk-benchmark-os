//! Reproduction metadata schema for Phase M benchmark packs.

use serde::{Deserialize, Serialize};

use crate::evidence::{ArtifactDigest, ClaimBoundary};

use super::eligibility::Level2EligibilityReport;

/// Reproduction metadata schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BenchmarkPackReproductionMetadataVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for BenchmarkPackReproductionMetadataVersion {
    fn default() -> Self {
        Self {
            value: "phase-m-reproduction-metadata-v0".to_string(),
        }
    }
}

/// Kind of inert external replay plan attached to a local pack.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ExternalReplayPlanKind {
    /// zk-Harness dry-run plan.
    ZkHarnessDryRun,
    /// gnark recursion envelope plan.
    GnarkRecursionEnvelope,
    /// Narrow zkML workload plan.
    ZkmlNarrowWorkload,
}

/// Attachment record for one inert external replay plan.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalReplayPlanAttachment {
    /// Plan kind.
    pub kind: ExternalReplayPlanKind,
    /// Plan id.
    pub plan_id: String,
    /// Relative path inside the pack root.
    pub relative_path: String,
    /// Digest over plan bytes as written.
    pub plan_digest: ArtifactDigest,
    /// Execution policy label.
    pub execution_policy: String,
    /// True because Phase M attachments are inert only.
    pub inert: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Reproduction metadata attached to a local benchmark pack.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BenchmarkPackReproductionMetadata {
    /// Metadata id.
    pub id: String,
    /// Schema version.
    pub version: BenchmarkPackReproductionMetadataVersion,
    /// Source local pack id.
    pub source_pack_id: String,
    /// Digest of the source pack manifest before reproduction attachments.
    pub source_pack_manifest_digest: ArtifactDigest,
    /// Claim boundary for reproduction metadata.
    pub claim_boundary: ClaimBoundary,
    /// Attached inert external replay plans.
    pub attachments: Vec<ExternalReplayPlanAttachment>,
    /// Level2 eligibility report.
    pub level2_eligibility: Level2EligibilityReport,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl BenchmarkPackReproductionMetadata {
    /// Return true when every attachment is inert.
    pub fn attachments_are_inert(&self) -> bool {
        self.attachments.iter().all(|attachment| attachment.inert)
    }

    /// Return true when metadata remains a design note only.
    pub fn is_design_note_only(&self) -> bool {
        self.claim_boundary == ClaimBoundary::Level0DesignNote
    }
}

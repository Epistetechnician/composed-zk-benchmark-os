//! Replay Result schema for local oracle replay.

use serde::{Deserialize, Serialize};

use crate::evidence::{
    ArtifactRef, BackendOutcome, ClaimBoundary, EvidenceRecord, ResultClassification,
};

use super::manifest::{ReplayArtifactRef, ReplayMode, ReplayProvenance};

/// Replay Result id.
pub type ReplayResultId = String;

/// Replay status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ReplayStatus {
    /// All local trace evaluations completed without rejected traces.
    Completed,
    /// Local trace evaluations completed and at least one trace was rejected.
    CompletedWithRejectedTraces,
    /// At least one trace hit a capability gap.
    CapabilityGap,
    /// At least one trace was inconclusive.
    Inconclusive,
    /// Manifest was malformed.
    MalformedManifest,
    /// Adapter failed locally.
    AdapterError,
}

/// Replay failure mode.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ReplayFailureMode {
    /// No failure.
    None,
    /// Malformed manifest.
    MalformedManifest,
    /// Unsupported replay mode.
    UnsupportedReplayMode,
    /// Replay subject missing.
    ReplaySubjectMissing,
    /// Replay trace missing.
    ReplayTraceMissing,
    /// Local adapter error.
    AdapterError,
}

/// Per-trace replay result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReplayTraceResult {
    /// Trace id.
    pub trace_id: String,
    /// Expected verdict.
    pub expected_verdict: crate::evidence::ExpectedVerdict,
    /// Local oracle outcome.
    pub local_oracle_outcome: crate::dsl::OracleOutcome,
    /// Backend outcome representation in local adapter context only.
    pub backend_outcome: BackendOutcome,
    /// Result classification.
    pub result_classification: ResultClassification,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Replay result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReplayResult {
    /// Replay result id.
    pub id: ReplayResultId,
    /// Manifest id.
    pub manifest_id: String,
    /// Adapter id.
    pub adapter_id: String,
    /// Replay mode.
    pub replay_mode: ReplayMode,
    /// Status.
    pub status: ReplayStatus,
    /// Failure mode.
    pub failure_mode: ReplayFailureMode,
    /// Per-trace results.
    pub trace_results: Vec<ReplayTraceResult>,
    /// Evidence records.
    pub evidence_records: Vec<EvidenceRecord>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Artifact references.
    #[serde(default)]
    pub artifact_refs: Vec<ReplayArtifactRef>,
    /// Provenance.
    pub provenance: ReplayProvenance,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl ReplayResult {
    /// Return output artifacts only.
    pub fn output_artifacts(&self) -> Vec<&ArtifactRef> {
        self.artifact_refs.iter().collect()
    }
}

//! Benchmark pack manifest schema.

use serde::{Deserialize, Serialize};

use crate::evidence::{ArtifactDigest, ArtifactKind, ArtifactRole, ClaimBoundary};

/// Benchmark pack id.
pub type BenchmarkPackId = String;

/// Benchmark pack schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BenchmarkPackVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for BenchmarkPackVersion {
    fn default() -> Self {
        Self {
            value: "phase-f-local-pack-v0".to_string(),
        }
    }
}

/// Role of a file inside a local benchmark pack.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum BenchmarkPackFileRole {
    /// Generated Benchmark Instance payload.
    GeneratedInstance,
    /// Mutated Benchmark Instance payload.
    MutatedInstance,
    /// Replay Manifest payload.
    ReplayManifest,
    /// Replay Result payload.
    ReplayResult,
    /// Evidence Ledger payload.
    EvidenceLedger,
    /// Conservative Score Report payload.
    ScoreReport,
    /// Pack README.
    Readme,
    /// Inert external replay plan JSON.
    ExternalReplayPlan,
    /// Reproduction metadata JSON.
    ReproductionMetadata,
}

impl BenchmarkPackFileRole {
    /// Convert to the generic artifact kind.
    pub fn artifact_kind(self) -> ArtifactKind {
        match self {
            Self::GeneratedInstance => ArtifactKind::GeneratedInstance,
            Self::MutatedInstance => ArtifactKind::MutatedInstance,
            Self::ReplayManifest => ArtifactKind::ReplayManifest,
            Self::ReplayResult => ArtifactKind::ReplayResult,
            Self::EvidenceLedger => ArtifactKind::EvidenceLedger,
            Self::ScoreReport => ArtifactKind::ScoreReport,
            Self::Readme => ArtifactKind::Readme,
            Self::ExternalReplayPlan | Self::ReproductionMetadata => ArtifactKind::Other,
        }
    }

    /// Convert to the generic artifact role.
    pub fn artifact_role(self) -> ArtifactRole {
        match self {
            Self::GeneratedInstance | Self::MutatedInstance | Self::ReplayManifest => {
                ArtifactRole::Input
            }
            Self::ReplayResult => ArtifactRole::Output,
            Self::EvidenceLedger => ArtifactRole::Evidence,
            Self::ScoreReport => ArtifactRole::Report,
            Self::Readme => ArtifactRole::Documentation,
            Self::ExternalReplayPlan => ArtifactRole::Manifest,
            Self::ReproductionMetadata => ArtifactRole::Manifest,
        }
    }
}

/// File entry in a benchmark pack.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BenchmarkPackFile {
    /// Relative path inside the pack root.
    pub relative_path: String,
    /// File role.
    pub role: BenchmarkPackFileRole,
    /// File digest over bytes as written.
    pub digest: ArtifactDigest,
    /// Whether validation should require the file.
    pub required: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Summary of local benchmark pack contents.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct BenchmarkPackSummary {
    /// Generated instance count.
    pub generated_instance_count: usize,
    /// Mutated instance count.
    pub mutated_instance_count: usize,
    /// Replay manifest count.
    pub replay_manifest_count: usize,
    /// Replay result count.
    pub replay_result_count: usize,
    /// Evidence record count.
    pub evidence_record_count: usize,
    /// Score report count.
    pub score_report_count: usize,
    /// External replay plan count.
    #[serde(default)]
    pub external_replay_plan_count: usize,
    /// Reproduction metadata count.
    #[serde(default)]
    pub reproduction_metadata_count: usize,
    /// True because Phase F packs are local-only artifacts.
    pub local_only: bool,
}

/// Manifest for a local benchmark pack.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BenchmarkPackManifest {
    /// Pack id.
    pub id: BenchmarkPackId,
    /// Schema version.
    pub version: BenchmarkPackVersion,
    /// Maximum claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Local generator version when generated artifacts are included.
    #[serde(default)]
    pub local_generator_version: Option<String>,
    /// Local adapter version when replay artifacts are included.
    #[serde(default)]
    pub local_adapter_version: Option<String>,
    /// Included generated instance ids.
    #[serde(default)]
    pub generated_instance_ids: Vec<String>,
    /// Included mutation ids.
    #[serde(default)]
    pub mutation_ids: Vec<String>,
    /// Included replay manifest ids.
    #[serde(default)]
    pub replay_manifest_ids: Vec<String>,
    /// Included replay result ids.
    #[serde(default)]
    pub replay_result_ids: Vec<String>,
    /// Evidence ledger file reference.
    #[serde(default)]
    pub evidence_ledger_ref: Option<String>,
    /// Reproduction metadata file reference.
    #[serde(default)]
    pub reproduction_metadata_ref: Option<String>,
    /// File entries. The manifest file itself is excluded to avoid circular
    /// digesting.
    pub files: Vec<BenchmarkPackFile>,
    /// Summary.
    pub summary: BenchmarkPackSummary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl BenchmarkPackManifest {
    /// Return true when all file paths are relative and local.
    pub fn uses_relative_paths_only(&self) -> bool {
        self.files.iter().all(|file| {
            !file.relative_path.starts_with('/')
                && !file.relative_path.contains("..")
                && !file.relative_path.contains('\\')
        })
    }
}

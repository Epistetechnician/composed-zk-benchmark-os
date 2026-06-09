//! Artifact reference and deterministic digest types.

use serde::{Deserialize, Serialize};

/// Artifact digest algorithm.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ArtifactDigestAlgorithm {
    /// SHA-256 over deterministic local bytes.
    Sha256,
    /// Unsupported or future digest algorithm. Validation rejects this for
    /// Phase I synthetic imports.
    Unsupported,
}

/// Artifact kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ArtifactKind {
    /// Generated Benchmark Instance JSON.
    GeneratedInstance,
    /// Mutated Benchmark Instance JSON.
    MutatedInstance,
    /// Replay Manifest JSON.
    ReplayManifest,
    /// Replay Result JSON.
    ReplayResult,
    /// Evidence Ledger JSON.
    EvidenceLedger,
    /// Score Report JSON.
    ScoreReport,
    /// Benchmark Pack Manifest JSON.
    BenchmarkPackManifest,
    /// Pack README.
    Readme,
    /// Other local-only artifact.
    Other,
}

/// Artifact role.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ArtifactRole {
    /// Replay input.
    Input,
    /// Replay output.
    Output,
    /// Evidence record.
    Evidence,
    /// Manifest or metadata.
    Manifest,
    /// Digest or integrity metadata.
    Digest,
    /// Human-readable note.
    Documentation,
    /// Conservative local report.
    Report,
}

/// Artifact digest metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ArtifactDigest {
    /// Digest algorithm.
    pub algorithm: ArtifactDigestAlgorithm,
    /// Lowercase hexadecimal digest.
    pub hex_digest: String,
    /// Byte length of the digested payload.
    pub byte_len: usize,
    /// Artifact kind when known.
    #[serde(default)]
    pub kind: Option<ArtifactKind>,
    /// Artifact role when known.
    #[serde(default)]
    pub role: Option<ArtifactRole>,
}

/// Relative artifact reference with digest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ArtifactRef {
    /// Relative path or logical artifact id. Do not store absolute paths in pack manifests.
    pub uri: String,
    /// Artifact kind.
    pub kind: ArtifactKind,
    /// Artifact role.
    pub role: ArtifactRole,
    /// Deterministic digest.
    pub digest: ArtifactDigest,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

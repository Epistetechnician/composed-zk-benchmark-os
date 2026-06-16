//! Error types used by the local foundation crate.

use thiserror::Error;

/// Crate-local result type.
pub type Result<T> = std::result::Result<T, ZkBenchError>;

/// Errors distinguish parse failures, static validation failures, lowering
/// failures, oracle execution failures, and claim-boundary violations.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum ZkBenchError {
    /// YAML or structured input parsing failed.
    #[error("parse error: {message}")]
    Parse { message: String },

    /// A Surface DSL or Parsed AST validation rule failed.
    #[error("validation error at {path}: {message}")]
    Validation { path: String, message: String },

    /// Lowering from Parsed AST to canonical Semantic IR failed.
    #[error("lowering error at {path}: {message}")]
    Lowering { path: String, message: String },

    /// Local oracle evaluation could not proceed because the input is malformed.
    #[error("oracle error at {path}: {message}")]
    Oracle { path: String, message: String },

    /// Deterministic generation failed.
    #[error("generation error at {path}: {message}")]
    Generation { path: String, message: String },

    /// Mutation planning or application failed.
    #[error("mutation error at {path}: {message}")]
    Mutation { path: String, message: String },

    /// Replay manifest or result handling failed.
    #[error("replay error at {path}: {message}")]
    Replay { path: String, message: String },

    /// Evidence ledger operation failed.
    #[error("evidence ledger error at {path}: {message}")]
    EvidenceLedger { path: String, message: String },

    /// Artifact digest or reference operation failed.
    #[error("artifact error at {path}: {message}")]
    Artifact { path: String, message: String },

    /// Benchmark pack operation failed.
    #[error("benchmark pack error at {path}: {message}")]
    BenchmarkPack { path: String, message: String },

    /// zk-Harness dry-run adapter preparation failed.
    #[error("zk-Harness dry-run error at {path}: {message}")]
    ZkHarness { path: String, message: String },

    /// External-runner boundary validation failed.
    #[error("external-runner boundary error at {path}: {message}")]
    ExternalRunner { path: String, message: String },

    /// Synthetic result import failed.
    #[error("synthetic result import error at {path}: {message}")]
    SyntheticImport { path: String, message: String },

    /// Evidence append proposal validation failed.
    #[error("evidence append proposal error at {path}: {message}")]
    EvidenceAppendProposal { path: String, message: String },

    /// Evidence review validation failed.
    #[error("evidence review error at {path}: {message}")]
    EvidenceReview { path: String, message: String },

    /// Evidence acceptance policy validation failed.
    #[error("evidence acceptance policy error at {path}: {message}")]
    EvidenceAcceptancePolicy { path: String, message: String },

    /// Evidence record candidate validation failed.
    #[error("evidence record candidate error at {path}: {message}")]
    EvidenceRecordCandidate { path: String, message: String },

    /// Evidence append preview validation failed.
    #[error("evidence append preview error at {path}: {message}")]
    EvidenceAppendPreview { path: String, message: String },

    /// Level2 eligibility validation failed.
    #[error("Level2 eligibility error at {path}: {message}")]
    Level2Eligibility { path: String, message: String },

    /// Evidence review ledger validation failed.
    #[error("evidence review ledger error at {path}: {message}")]
    EvidenceReviewLedger { path: String, message: String },

    /// Serialization failed.
    #[error("serialization error at {path}: {message}")]
    Serialization { path: String, message: String },

    /// Deserialization failed.
    #[error("deserialization error at {path}: {message}")]
    Deserialization { path: String, message: String },

    /// A claim boundary exceeds the evidence available in this phase.
    #[error("claim boundary error: {message}")]
    ClaimBoundary { message: String },
}

impl ZkBenchError {
    /// Construct a validation error.
    pub fn validation(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::Validation {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct a lowering error.
    pub fn lowering(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::Lowering {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct an oracle error.
    pub fn oracle(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::Oracle {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct a generation error.
    pub fn generation(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::Generation {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct a mutation error.
    pub fn mutation(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::Mutation {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct a replay error.
    pub fn replay(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::Replay {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct an evidence ledger error.
    pub fn evidence_ledger(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::EvidenceLedger {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct an artifact error.
    pub fn artifact(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::Artifact {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct a benchmark pack error.
    pub fn benchmark_pack(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::BenchmarkPack {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct a zk-Harness dry-run adapter preparation error.
    pub fn zk_harness(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::ZkHarness {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct an external-runner boundary error.
    pub fn external_runner(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::ExternalRunner {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct a synthetic result import error.
    pub fn synthetic_import(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::SyntheticImport {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct an evidence append proposal error.
    pub fn evidence_append_proposal(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::EvidenceAppendProposal {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct an evidence review error.
    pub fn evidence_review(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::EvidenceReview {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct an evidence acceptance policy error.
    pub fn evidence_acceptance_policy(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::EvidenceAcceptancePolicy {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct an evidence record candidate error.
    pub fn evidence_record_candidate(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::EvidenceRecordCandidate {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct an evidence append preview error.
    pub fn evidence_append_preview(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::EvidenceAppendPreview {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct a Level2 eligibility error.
    pub fn level2_eligibility(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::Level2Eligibility {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct an evidence review ledger error.
    pub fn evidence_review_ledger(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::EvidenceReviewLedger {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct a serialization error.
    pub fn serialization(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::Serialization {
            path: path.into(),
            message: message.into(),
        }
    }

    /// Construct a deserialization error.
    pub fn deserialization(path: impl Into<String>, message: impl Into<String>) -> Self {
        Self::Deserialization {
            path: path.into(),
            message: message.into(),
        }
    }
}

impl From<serde_yaml::Error> for ZkBenchError {
    fn from(error: serde_yaml::Error) -> Self {
        Self::Parse {
            message: error.to_string(),
        }
    }
}

impl From<serde_json::Error> for ZkBenchError {
    fn from(error: serde_json::Error) -> Self {
        Self::Parse {
            message: error.to_string(),
        }
    }
}

//! Resumable shard checkpoint support.

use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::ClaimBoundary;

use super::failure_corpus::{FailureArtifactRef, FailureCorpusEntryId};
use super::shard::{SoakCaseId, SoakShardId, SoakShardResumeToken};
use super::telemetry::SoakTelemetryCounters;

/// Resumable shard checkpoint.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakShardCheckpoint {
    /// Shard id.
    pub shard_id: SoakShardId,
    /// Config digest.
    pub config_digest: String,
    /// Completed case ids.
    #[serde(default)]
    pub completed_case_ids: Vec<SoakCaseId>,
    /// Failed case ids.
    #[serde(default)]
    pub failed_case_ids: Vec<SoakCaseId>,
    /// Skipped case ids.
    #[serde(default)]
    pub skipped_case_ids: Vec<SoakCaseId>,
    /// Last completed case index in the shard order.
    #[serde(default)]
    pub last_completed_case_index: Option<usize>,
    /// Artifact refs written so far.
    #[serde(default)]
    pub artifact_refs_written: Vec<FailureArtifactRef>,
    /// Telemetry counters so far.
    pub telemetry_counters: SoakTelemetryCounters,
    /// Failure corpus refs so far.
    #[serde(default)]
    pub failure_corpus_refs: Vec<FailureCorpusEntryId>,
    /// Resume token.
    pub resume_token: SoakShardResumeToken,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl SoakShardCheckpoint {
    /// Empty checkpoint.
    pub fn empty(
        shard_id: SoakShardId,
        config_digest: String,
        resume_token: SoakShardResumeToken,
    ) -> Self {
        Self {
            shard_id,
            config_digest,
            completed_case_ids: Vec::new(),
            failed_case_ids: Vec::new(),
            skipped_case_ids: Vec::new(),
            last_completed_case_index: None,
            artifact_refs_written: Vec::new(),
            telemetry_counters: SoakTelemetryCounters::default(),
            failure_corpus_refs: Vec::new(),
            resume_token,
            claim_boundary: ClaimBoundary::Level0DesignNote,
            notes: vec![
                "Shard checkpoint is resumable local state only.".to_string(),
                "Local soak telemetry is not official benchmark evidence.".to_string(),
            ],
        }
    }

    /// Return true when the case was completed already.
    pub fn completed_case(&self, case_id: &str) -> bool {
        self.completed_case_ids.iter().any(|id| id == case_id)
    }

    /// Mark a case completed.
    pub fn mark_completed(&mut self, case_id: SoakCaseId, index: usize) {
        if !self.completed_case(&case_id) {
            self.completed_case_ids.push(case_id);
            self.completed_case_ids.sort();
        }
        self.last_completed_case_index = Some(index);
    }

    /// Mark a case failed.
    pub fn mark_failed(&mut self, case_id: SoakCaseId) {
        if !self.failed_case_ids.iter().any(|id| id == &case_id) {
            self.failed_case_ids.push(case_id);
            self.failed_case_ids.sort();
        }
    }

    /// Mark a case skipped.
    pub fn mark_skipped(&mut self, case_id: SoakCaseId) {
        if !self.skipped_case_ids.iter().any(|id| id == &case_id) {
            self.skipped_case_ids.push(case_id);
            self.skipped_case_ids.sort();
        }
    }
}

/// Validate checkpoint against expected digest and token.
pub fn validate_soak_shard_checkpoint(
    checkpoint: &SoakShardCheckpoint,
    expected_config_digest: &str,
    expected_resume_token: &SoakShardResumeToken,
) -> Result<()> {
    if checkpoint.claim_boundary != ClaimBoundary::Level0DesignNote {
        return Err(ZkBenchError::soak(
            "soak.checkpoint.claim_boundary",
            "shard checkpoints must remain Level0DesignNote",
        ));
    }
    if checkpoint.config_digest != expected_config_digest {
        return Err(ZkBenchError::soak(
            "soak.checkpoint.config_digest",
            "config digest mismatch",
        ));
    }
    if checkpoint.resume_token != *expected_resume_token {
        return Err(ZkBenchError::soak(
            "soak.checkpoint.resume_token",
            "resume token mismatch",
        ));
    }
    Ok(())
}

/// Write a checkpoint as deterministic JSON.
pub fn write_soak_shard_checkpoint(
    path: impl AsRef<Path>,
    checkpoint: &SoakShardCheckpoint,
) -> Result<()> {
    let path = path.as_ref();
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|error| ZkBenchError::soak(parent.display().to_string(), error.to_string()))?;
    }
    let bytes = serde_json::to_vec_pretty(checkpoint).map_err(|error| {
        ZkBenchError::serialization("write_soak_shard_checkpoint", error.to_string())
    })?;
    fs::write(path, bytes)
        .map_err(|error| ZkBenchError::soak(path.display().to_string(), error.to_string()))
}

/// Read a checkpoint from JSON.
pub fn read_soak_shard_checkpoint(path: impl AsRef<Path>) -> Result<SoakShardCheckpoint> {
    let path = path.as_ref();
    let bytes = fs::read(path)
        .map_err(|error| ZkBenchError::soak(path.display().to_string(), error.to_string()))?;
    serde_json::from_slice(&bytes).map_err(|error| {
        ZkBenchError::deserialization("read_soak_shard_checkpoint", error.to_string())
    })
}

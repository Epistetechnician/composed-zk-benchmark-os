//! Regression corpus curated from Phase L soak campaign failures.

use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::ClaimBoundary;
use crate::generator::FamilyKind;
use crate::pack::ReportBundleReviewFinding;

/// Regression corpus schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RegressionCorpusVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for RegressionCorpusVersion {
    fn default() -> Self {
        Self {
            value: "phase-l-regression-corpus-v0".to_string(),
        }
    }
}

/// Kind of failure captured in the regression corpus.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum RegressionFailureKind {
    /// Soak failed to write a pack for a family/seed cell.
    SoakWriteFailed,
    /// Report-bundle review reported errors for the pack.
    ReviewFailed,
    /// Mutation pass was skipped for an otherwise written pack.
    MutationPassSkipped,
}

/// One regression corpus entry referencing a stored failure artifact.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RegressionCorpusEntry {
    /// Stable entry id.
    pub id: String,
    /// Campaign that produced this entry.
    pub campaign_id: String,
    /// Pack id when a pack exists.
    #[serde(default)]
    pub pack_id: Option<String>,
    /// Family kind.
    pub family_kind: FamilyKind,
    /// Seed used for generation.
    pub seed: u64,
    /// Failure kind.
    pub failure_kind: RegressionFailureKind,
    /// Stable finding or failure codes.
    #[serde(default)]
    pub codes: Vec<String>,
    /// Relative path from the corpus root to the stored artifact.
    pub artifact_relative_path: String,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Persistent regression corpus manifest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RegressionCorpus {
    /// Schema version.
    pub version: RegressionCorpusVersion,
    /// Claim boundary for corpus metadata.
    pub claim_boundary: ClaimBoundary,
    /// Corpus entries.
    #[serde(default)]
    pub entries: Vec<RegressionCorpusEntry>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for RegressionCorpus {
    fn default() -> Self {
        Self {
            version: RegressionCorpusVersion::default(),
            claim_boundary: ClaimBoundary::Level0DesignNote,
            entries: Vec::new(),
            notes: vec![
                "Regression corpus entries are local failure artifacts only.".to_string(),
                "Corpus metadata is not official benchmark evidence.".to_string(),
            ],
        }
    }
}

/// Load an existing corpus or return an empty corpus.
pub fn load_regression_corpus(path: impl AsRef<Path>) -> Result<RegressionCorpus> {
    let path = path.as_ref();
    if !path.is_file() {
        return Ok(RegressionCorpus::default());
    }
    let json = fs::read_to_string(path).map_err(|error| {
        ZkBenchError::benchmark_pack(path.display().to_string(), error.to_string())
    })?;
    serde_json::from_str(&json)
        .map_err(|error| ZkBenchError::deserialization("regression_corpus.load", error.to_string()))
}

/// Save a regression corpus manifest.
pub fn save_regression_corpus(corpus: &RegressionCorpus, path: impl AsRef<Path>) -> Result<()> {
    let path = path.as_ref();
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|error| {
            ZkBenchError::benchmark_pack(parent.display().to_string(), error.to_string())
        })?;
    }
    let bytes = serde_json::to_vec_pretty(corpus).map_err(|error| {
        ZkBenchError::serialization("regression_corpus.save", error.to_string())
    })?;
    fs::write(path, bytes).map_err(|error| {
        ZkBenchError::benchmark_pack(path.display().to_string(), error.to_string())
    })
}

/// Append entries to a corpus, skipping duplicate ids.
pub fn append_regression_entries(
    corpus: &mut RegressionCorpus,
    entries: Vec<RegressionCorpusEntry>,
) -> usize {
    let mut added = 0usize;
    for entry in entries {
        if corpus
            .entries
            .iter()
            .any(|existing| existing.id == entry.id)
        {
            continue;
        }
        corpus.entries.push(entry);
        added += 1;
    }
    added
}

/// Build corpus entries from review findings grouped by pack id.
pub fn entries_from_review_findings(
    campaign_id: &str,
    pack_id: &str,
    family_kind: FamilyKind,
    seed: u64,
    artifact_relative_path: impl Into<String>,
    findings: &[ReportBundleReviewFinding],
) -> Vec<RegressionCorpusEntry> {
    let error_findings: Vec<_> = findings
        .iter()
        .filter(|finding| finding.severity == crate::pack::ReportBundleReviewFindingSeverity::Error)
        .collect();
    if error_findings.is_empty() {
        return Vec::new();
    }
    let codes = error_findings
        .iter()
        .map(|finding| finding.code.clone())
        .collect::<Vec<_>>();
    vec![RegressionCorpusEntry {
        id: format!("{campaign_id}__{pack_id}__review_failed"),
        campaign_id: campaign_id.to_string(),
        pack_id: Some(pack_id.to_string()),
        family_kind,
        seed,
        failure_kind: RegressionFailureKind::ReviewFailed,
        codes,
        artifact_relative_path: artifact_relative_path.into(),
        notes: error_findings
            .iter()
            .map(|finding| finding.message.clone())
            .collect(),
    }]
}

/// Serialize a regression corpus to pretty JSON.
pub fn serialize_regression_corpus_json(corpus: &RegressionCorpus) -> Result<String> {
    serde_json::to_string_pretty(corpus)
        .map_err(|error| ZkBenchError::serialization("regression_corpus.json", error.to_string()))
}

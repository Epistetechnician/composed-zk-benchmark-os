//! Local failure corpus for soak reproducibility.

use std::collections::BTreeSet;

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::ClaimBoundary;
use crate::generator::{FamilyKind, GeneratorTunables};
use crate::mutation::MutationClass;

use super::shard::{SoakCaseId, SoakShardId};

/// Failure corpus entry id.
pub type FailureCorpusEntryId = String;

/// Failure corpus kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum FailureCorpusKind {
    /// Generation failed.
    GenerationFailure,
    /// Mutation failed.
    MutationFailure,
    /// Local oracle mismatch.
    OracleMismatch,
    /// Replay failed.
    ReplayFailure,
    /// Pack validation failed.
    PackValidationFailure,
    /// Proposal preview failed.
    ProposalPreviewFailure,
    /// Claim-boundary violation.
    ClaimBoundaryViolation,
    /// Serialization failed.
    SerializationFailure,
    /// Determinism failed.
    DeterminismFailure,
    /// Test-only panic capture marker.
    UnexpectedPanicCaughtInTestOnly,
}

/// Failure artifact reference.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FailureArtifactRef {
    /// Relative artifact ref.
    pub relative_path: String,
    /// Artifact role.
    pub role: String,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Failure minimization hint.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FailureMinimizationHint {
    /// Reduce seed range.
    pub reduce_seed_range: bool,
    /// Isolate family.
    pub isolate_family: bool,
    /// Isolate mutation pass.
    pub isolate_mutation_pass: bool,
    /// Isolate trace.
    pub isolate_trace: bool,
    /// Write failure pack.
    pub write_failure_pack: bool,
    /// Preserve serialized instance.
    pub preserve_serialized_instance: bool,
    /// Preserve replay manifest.
    pub preserve_replay_manifest: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for FailureMinimizationHint {
    fn default() -> Self {
        Self {
            reduce_seed_range: true,
            isolate_family: true,
            isolate_mutation_pass: true,
            isolate_trace: true,
            write_failure_pack: true,
            preserve_serialized_instance: true,
            preserve_replay_manifest: true,
            notes: vec!["Phase K records minimization metadata only; no reducer runs.".to_string()],
        }
    }
}

/// Failure triage status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum FailureTriageStatus {
    /// New entry.
    New,
    /// Needs review.
    NeedsReview,
    /// Reproduced locally.
    ReproducedLocally,
    /// Quarantined.
    Quarantined,
    /// Superseded.
    Superseded,
}

/// Reproduction manifest for a failure corpus entry.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FailureReproductionManifest {
    /// Family kind.
    pub family_kind: FamilyKind,
    /// Generator seed.
    pub seed: u64,
    /// Tunables.
    pub tunables: GeneratorTunables,
    /// Mutation selection.
    pub mutation_selection: Vec<MutationClass>,
    /// Trace selection.
    pub trace_selection: String,
    /// Shard id.
    pub shard_id: SoakShardId,
    /// Case id.
    pub case_id: SoakCaseId,
    /// Fixture or artifact refs.
    #[serde(default)]
    pub artifact_refs: Vec<FailureArtifactRef>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Failure corpus entry.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FailureCorpusEntry {
    /// Entry id.
    pub entry_id: FailureCorpusEntryId,
    /// Failure kind.
    pub failure_kind: FailureCorpusKind,
    /// Source soak case id.
    pub source_soak_case_id: SoakCaseId,
    /// Family kind.
    pub family_kind: FamilyKind,
    /// Generator seed.
    pub generator_seed: u64,
    /// Tunables.
    pub tunables: GeneratorTunables,
    /// Mutation class, when applicable.
    #[serde(default)]
    pub mutation_class: Option<MutationClass>,
    /// Trace id, when applicable.
    #[serde(default)]
    pub trace_id: Option<String>,
    /// Local error summary.
    pub local_error_summary: String,
    /// Reproduction manifest.
    pub reproduction_manifest: FailureReproductionManifest,
    /// Artifact refs.
    #[serde(default)]
    pub artifact_refs: Vec<FailureArtifactRef>,
    /// Minimization hints.
    #[serde(default)]
    pub minimization_hints: Vec<FailureMinimizationHint>,
    /// Triage status.
    pub triage_status: FailureTriageStatus,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Input for building a failure corpus entry.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FailureCorpusEntryInput {
    /// Shard id.
    pub shard_id: SoakShardId,
    /// Case id.
    pub case_id: SoakCaseId,
    /// Family kind.
    pub family_kind: FamilyKind,
    /// Generator seed.
    pub generator_seed: u64,
    /// Tunables.
    pub tunables: GeneratorTunables,
    /// Mutation class, when applicable.
    #[serde(default)]
    pub mutation_class: Option<MutationClass>,
    /// Trace id, when applicable.
    #[serde(default)]
    pub trace_id: Option<String>,
    /// Failure kind.
    pub failure_kind: FailureCorpusKind,
    /// Local error summary.
    pub local_error_summary: String,
}

/// Failure corpus index summary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct FailureCorpusSummary {
    /// Entry count.
    pub entry_count: usize,
    /// Claim boundary violation count.
    pub claim_boundary_violation_count: usize,
    /// Replay failure count.
    pub replay_failure_count: usize,
    /// Mutation failure count.
    pub mutation_failure_count: usize,
}

/// Failure corpus index.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FailureCorpusIndex {
    /// Corpus id.
    pub corpus_id: String,
    /// Corpus version.
    pub corpus_version: String,
    /// Entries.
    pub entries: Vec<FailureCorpusEntry>,
    /// Summary.
    pub summary: FailureCorpusSummary,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Failure corpus wrapper.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FailureCorpus {
    /// Corpus index.
    pub index: FailureCorpusIndex,
}

impl FailureCorpus {
    /// Empty corpus.
    pub fn empty(corpus_id: impl Into<String>) -> Self {
        let index = FailureCorpusIndex {
            corpus_id: corpus_id.into(),
            corpus_version: "phase-k-failure-corpus-v0".to_string(),
            entries: Vec::new(),
            summary: FailureCorpusSummary::default(),
            claim_boundary: ClaimBoundary::Level0DesignNote,
            notes: vec![
                "Failure corpus entries are reproduction aids, not accepted evidence.".to_string(),
            ],
        };
        Self { index }
    }

    /// Push an entry.
    pub fn push(&mut self, entry: FailureCorpusEntry) {
        self.index.entries.push(entry);
        self.recompute_summary();
    }

    /// Recompute summary.
    pub fn recompute_summary(&mut self) {
        self.index.summary = summarize_failure_corpus_entries(&self.index.entries);
    }
}

/// Validate a failure corpus index.
pub fn validate_failure_corpus_index(index: &FailureCorpusIndex) -> Result<()> {
    if index.claim_boundary != ClaimBoundary::Level0DesignNote {
        return Err(ZkBenchError::soak(
            "soak.failure_corpus.claim_boundary",
            "failure corpus indexes must remain Level0DesignNote",
        ));
    }
    let expected_summary = summarize_failure_corpus_entries(&index.entries);
    if index.summary != expected_summary {
        return Err(ZkBenchError::soak(
            "soak.failure_corpus.summary",
            "failure corpus summary does not match entries",
        ));
    }
    let mut seen_entry_ids = BTreeSet::new();
    for (entry_index, entry) in index.entries.iter().enumerate() {
        if entry.entry_id.trim().is_empty() {
            return Err(ZkBenchError::soak(
                format!("soak.failure_corpus.entries[{entry_index}].entry_id"),
                "failure corpus entry id is empty",
            ));
        }
        if !seen_entry_ids.insert(entry.entry_id.clone()) {
            return Err(ZkBenchError::soak(
                format!("soak.failure_corpus.entries[{entry_index}].entry_id"),
                "failure corpus entry id is duplicated",
            ));
        }
        if entry.claim_boundary != ClaimBoundary::Level0DesignNote {
            return Err(ZkBenchError::soak(
                format!("soak.failure_corpus.entries[{entry_index}].claim_boundary"),
                "failure corpus entries must remain Level0DesignNote",
            ));
        }
        if entry.reproduction_manifest.claim_boundary != ClaimBoundary::Level0DesignNote {
            return Err(ZkBenchError::soak(
                format!(
                    "soak.failure_corpus.entries[{entry_index}].reproduction_manifest.claim_boundary"
                ),
                "failure reproduction manifests must remain Level0DesignNote",
            ));
        }
        if entry.reproduction_manifest.case_id != entry.source_soak_case_id {
            return Err(ZkBenchError::soak(
                format!("soak.failure_corpus.entries[{entry_index}].reproduction_manifest.case_id"),
                "failure reproduction manifest case id does not match entry source case id",
            ));
        }
        if entry.reproduction_manifest.family_kind != entry.family_kind {
            return Err(ZkBenchError::soak(
                format!(
                    "soak.failure_corpus.entries[{entry_index}].reproduction_manifest.family_kind"
                ),
                "failure reproduction manifest family kind does not match entry family kind",
            ));
        }
        if entry.reproduction_manifest.seed != entry.generator_seed {
            return Err(ZkBenchError::soak(
                format!("soak.failure_corpus.entries[{entry_index}].reproduction_manifest.seed"),
                "failure reproduction manifest seed does not match entry generator seed",
            ));
        }
        if entry.reproduction_manifest.tunables != entry.tunables {
            return Err(ZkBenchError::soak(
                format!(
                    "soak.failure_corpus.entries[{entry_index}].reproduction_manifest.tunables"
                ),
                "failure reproduction manifest tunables do not match entry tunables",
            ));
        }
        let expected_mutation_selection: Vec<_> = entry.mutation_class.into_iter().collect();
        if entry.reproduction_manifest.mutation_selection != expected_mutation_selection {
            return Err(ZkBenchError::soak(
                format!(
                    "soak.failure_corpus.entries[{entry_index}].reproduction_manifest.mutation_selection"
                ),
                "failure reproduction manifest mutation selection does not match entry mutation class",
            ));
        }
        if let Some(trace_id) = &entry.trace_id {
            if entry.reproduction_manifest.trace_selection != *trace_id {
                return Err(ZkBenchError::soak(
                    format!(
                        "soak.failure_corpus.entries[{entry_index}].reproduction_manifest.trace_selection"
                    ),
                    "failure reproduction manifest trace selection does not match entry trace id",
                ));
            }
        }
        for artifact_ref in &entry.artifact_refs {
            validate_failure_artifact_ref(artifact_ref)?;
        }
        for artifact_ref in &entry.reproduction_manifest.artifact_refs {
            validate_failure_artifact_ref(artifact_ref)?;
        }
    }
    Ok(())
}

fn summarize_failure_corpus_entries(entries: &[FailureCorpusEntry]) -> FailureCorpusSummary {
    FailureCorpusSummary {
        entry_count: entries.len(),
        claim_boundary_violation_count: entries
            .iter()
            .filter(|entry| entry.failure_kind == FailureCorpusKind::ClaimBoundaryViolation)
            .count(),
        replay_failure_count: entries
            .iter()
            .filter(|entry| entry.failure_kind == FailureCorpusKind::ReplayFailure)
            .count(),
        mutation_failure_count: entries
            .iter()
            .filter(|entry| entry.failure_kind == FailureCorpusKind::MutationFailure)
            .count(),
    }
}

/// Build a failure corpus entry.
pub fn build_failure_corpus_entry(input: FailureCorpusEntryInput) -> FailureCorpusEntry {
    let entry_id = format!(
        "failure_{}_{}",
        input.case_id,
        match input.mutation_class {
            Some(class) => format!("{class:?}"),
            None => format!("{:?}", input.failure_kind),
        }
    );
    let artifact_refs = Vec::new();
    let reproduction_manifest = FailureReproductionManifest {
        family_kind: input.family_kind,
        seed: input.generator_seed,
        tunables: input.tunables.clone(),
        mutation_selection: input.mutation_class.into_iter().collect(),
        trace_selection: input
            .trace_id
            .clone()
            .unwrap_or_else(|| "case_default_trace_selection".to_string()),
        shard_id: input.shard_id,
        case_id: input.case_id.clone(),
        artifact_refs: artifact_refs.clone(),
        claim_boundary: ClaimBoundary::Level0DesignNote,
    };
    FailureCorpusEntry {
        entry_id,
        failure_kind: input.failure_kind,
        source_soak_case_id: input.case_id,
        family_kind: input.family_kind,
        generator_seed: input.generator_seed,
        tunables: input.tunables,
        mutation_class: input.mutation_class,
        trace_id: input.trace_id,
        local_error_summary: input.local_error_summary,
        reproduction_manifest,
        artifact_refs,
        minimization_hints: vec![FailureMinimizationHint::default()],
        triage_status: FailureTriageStatus::New,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec![
            "Failure corpus entries are reproduction aids, not accepted evidence.".to_string(),
        ],
    }
}

fn validate_failure_artifact_ref(artifact_ref: &FailureArtifactRef) -> Result<()> {
    if artifact_ref.relative_path.trim().is_empty() {
        return Err(ZkBenchError::soak(
            "soak.failure_corpus.artifact_ref.relative_path",
            "failure artifact refs must have a relative path",
        ));
    }
    if artifact_ref.role.trim().is_empty() {
        return Err(ZkBenchError::soak(
            "soak.failure_corpus.artifact_ref.role",
            "failure artifact refs must have a role",
        ));
    }
    if artifact_ref.relative_path.starts_with('/')
        || artifact_ref.relative_path.contains("..")
        || artifact_ref.relative_path.contains('\\')
    {
        return Err(ZkBenchError::soak(
            "soak.failure_corpus.artifact_ref",
            "failure artifact refs must be relative portable paths",
        ));
    }
    Ok(())
}

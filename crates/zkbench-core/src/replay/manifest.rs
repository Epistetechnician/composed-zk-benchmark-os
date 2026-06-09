//! Replay Manifest schema for deterministic local oracle replay.

use serde::{Deserialize, Serialize};

use crate::adapters::AdapterCapabilitySet;
use crate::error::Result;
use crate::evidence::{
    compute_artifact_digest, ArtifactKind, ArtifactRef, ArtifactRole, ClaimBoundary,
    ExpectedVerdict,
};
use crate::generator::{FamilyKind, GeneratedBenchmarkInstance, GenerationProvenance};
use crate::mutation::{MutatedBenchmarkInstance, MutationProvenance};

/// Replay Manifest id.
pub type ReplayManifestId = String;

/// Replay serialization version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReplaySerializationVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for ReplaySerializationVersion {
    fn default() -> Self {
        Self {
            value: "phase-f-local-replay-v0".to_string(),
        }
    }
}

/// Replay mode.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ReplayMode {
    /// Run the local semantic oracle.
    LocalOracle,
    /// Mock-only outcome path for classification tests.
    MockOutcome,
}

/// Replay subject kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ReplaySubjectKind {
    /// Generated Benchmark Instance.
    GeneratedInstance,
    /// Mutated Benchmark Instance.
    MutatedInstance,
}

/// Replay subject. Full local subjects are embedded to make local replay JSON
/// self-contained and reproducible without external paths.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ReplaySubject {
    /// Subject kind.
    pub kind: ReplaySubjectKind,
    /// Generated instance id.
    #[serde(default)]
    pub generated_instance_id: Option<String>,
    /// Mutated instance id.
    #[serde(default)]
    pub mutated_instance_id: Option<String>,
    /// Generated instance payload when applicable.
    #[serde(default)]
    pub generated_instance: Option<GeneratedBenchmarkInstance>,
    /// Mutated instance payload when applicable.
    #[serde(default)]
    pub mutated_instance: Option<MutatedBenchmarkInstance>,
}

/// Selected replay trace.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReplayTraceSelection {
    /// Trace id.
    pub trace_id: String,
    /// Expected verdict before replay.
    pub expected_verdict: ExpectedVerdict,
}

/// Expected replay outcome for a trace.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReplayExpectedOutcome {
    /// Trace id.
    pub trace_id: String,
    /// Expected verdict.
    pub expected_verdict: ExpectedVerdict,
}

/// Local replay command. This is not a shell command.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ReplayCommand {
    /// Run local oracle evaluation.
    LocalOracleEvaluation,
    /// Mock outcome evaluation for tests only.
    MockOutcomeEvaluation {
        /// Mock backend outcome.
        outcome: crate::evidence::BackendOutcome,
    },
}

/// Replay artifact reference alias.
pub type ReplayArtifactRef = ArtifactRef;

/// Replay provenance.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReplayProvenance {
    /// Replay version.
    pub replay_version: ReplaySerializationVersion,
    /// Adapter id.
    pub adapter_id: String,
    /// Logical creation marker, not wall-clock time.
    pub logical_created_at: String,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Replay Manifest for local deterministic replay.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ReplayManifest {
    /// Manifest id.
    pub id: ReplayManifestId,
    /// Schema version.
    pub schema_version: ReplaySerializationVersion,
    /// Replay mode.
    pub replay_mode: ReplayMode,
    /// Replay subject.
    pub subject: ReplaySubject,
    /// Family kind.
    #[serde(default)]
    pub family_kind: Option<FamilyKind>,
    /// Generator provenance when applicable.
    #[serde(default)]
    pub generation_provenance: Option<GenerationProvenance>,
    /// Mutation provenance when applicable.
    #[serde(default)]
    pub mutation_provenance: Option<MutationProvenance>,
    /// Selected traces.
    pub selected_traces: Vec<ReplayTraceSelection>,
    /// Expected outcomes.
    pub expected_outcomes: Vec<ReplayExpectedOutcome>,
    /// Local target id.
    pub local_target_id: String,
    /// Adapter id.
    pub adapter_id: String,
    /// Adapter capability set.
    pub adapter_capabilities: AdapterCapabilitySet,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Input artifact references.
    #[serde(default)]
    pub input_artifacts: Vec<ReplayArtifactRef>,
    /// Expected output artifact roles.
    #[serde(default)]
    pub expected_output_artifact_roles: Vec<ArtifactRole>,
    /// Local replay commands. These are not shell commands.
    pub commands: Vec<ReplayCommand>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Build a local replay manifest for a generated instance.
pub fn build_local_replay_manifest_for_instance(
    instance: &GeneratedBenchmarkInstance,
) -> Result<ReplayManifest> {
    let selected_traces = instance
        .accepted_traces
        .iter()
        .chain(instance.rejected_traces.iter())
        .map(|trace| ReplayTraceSelection {
            trace_id: trace.id.clone(),
            expected_verdict: trace
                .expected_verdict
                .unwrap_or(ExpectedVerdict::Inconclusive),
        })
        .collect::<Vec<_>>();
    let expected_outcomes = selected_traces
        .iter()
        .map(|trace| ReplayExpectedOutcome {
            trace_id: trace.trace_id.clone(),
            expected_verdict: trace.expected_verdict,
        })
        .collect();
    let artifact_digest = compute_artifact_digest(
        instance,
        Some(ArtifactKind::GeneratedInstance),
        Some(ArtifactRole::Input),
    )?;
    Ok(ReplayManifest {
        id: format!("manifest_{}_local_oracle", instance.id),
        schema_version: ReplaySerializationVersion::default(),
        replay_mode: ReplayMode::LocalOracle,
        subject: ReplaySubject {
            kind: ReplaySubjectKind::GeneratedInstance,
            generated_instance_id: Some(instance.id.clone()),
            mutated_instance_id: None,
            generated_instance: Some(instance.clone()),
            mutated_instance: None,
        },
        family_kind: Some(instance.family_kind),
        generation_provenance: Some(instance.generation_provenance.clone()),
        mutation_provenance: None,
        selected_traces,
        expected_outcomes,
        local_target_id: "local_oracle".to_string(),
        adapter_id: "local_json_adapter_v0".to_string(),
        adapter_capabilities: crate::adapters::local_json_capabilities(),
        claim_boundary: ClaimBoundary::Level1LocalReplay,
        input_artifacts: vec![ArtifactRef {
            uri: "specs/generated_instance.json".to_string(),
            kind: ArtifactKind::GeneratedInstance,
            role: ArtifactRole::Input,
            digest: artifact_digest,
            notes: vec!["embedded generated instance digest".to_string()],
        }],
        expected_output_artifact_roles: vec![ArtifactRole::Output, ArtifactRole::Evidence],
        commands: vec![ReplayCommand::LocalOracleEvaluation],
        notes: vec![
            "Local replay manifest only; no external backend command is represented.".to_string(),
        ],
    })
}

/// Build a local replay manifest for a mutated instance.
pub fn build_local_replay_manifest_for_mutation(
    mutation: &MutatedBenchmarkInstance,
) -> Result<ReplayManifest> {
    let expected_verdict = mutation
        .primary_trace
        .expected_verdict
        .unwrap_or(mutation.expected_verdict);
    let artifact_digest = compute_artifact_digest(
        mutation,
        Some(ArtifactKind::MutatedInstance),
        Some(ArtifactRole::Input),
    )?;
    Ok(ReplayManifest {
        id: format!("manifest_{}_local_oracle", mutation.id),
        schema_version: ReplaySerializationVersion::default(),
        replay_mode: ReplayMode::LocalOracle,
        subject: ReplaySubject {
            kind: ReplaySubjectKind::MutatedInstance,
            generated_instance_id: Some(mutation.source_instance_id.clone()),
            mutated_instance_id: Some(mutation.id.clone()),
            generated_instance: None,
            mutated_instance: Some(mutation.clone()),
        },
        family_kind: None,
        generation_provenance: None,
        mutation_provenance: Some(mutation.provenance.clone()),
        selected_traces: vec![ReplayTraceSelection {
            trace_id: mutation.primary_trace.id.clone(),
            expected_verdict,
        }],
        expected_outcomes: vec![ReplayExpectedOutcome {
            trace_id: mutation.primary_trace.id.clone(),
            expected_verdict,
        }],
        local_target_id: "local_oracle".to_string(),
        adapter_id: "local_json_adapter_v0".to_string(),
        adapter_capabilities: crate::adapters::local_json_capabilities(),
        claim_boundary: ClaimBoundary::Level1LocalReplay,
        input_artifacts: vec![ArtifactRef {
            uri: format!("specs/mutated_instances/{}.json", mutation.id),
            kind: ArtifactKind::MutatedInstance,
            role: ArtifactRole::Input,
            digest: artifact_digest,
            notes: vec!["embedded mutated instance digest".to_string()],
        }],
        expected_output_artifact_roles: vec![ArtifactRole::Output, ArtifactRole::Evidence],
        commands: vec![ReplayCommand::LocalOracleEvaluation],
        notes: vec![
            "Local replay manifest for mutation; no proof-system backend is represented."
                .to_string(),
        ],
    })
}

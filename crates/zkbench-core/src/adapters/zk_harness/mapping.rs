//! Mapping local benchmark packs into zk-Harness dry-run candidate labels.

use std::fs;

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{compute_artifact_digest, ArtifactDigest, ExpectedVerdict};
use crate::generator::{FamilyKind, GeneratedBenchmarkInstance};
use crate::mutation::{MutatedBenchmarkInstance, MutationClass};
use crate::pack::{BenchmarkPackFileRole, BenchmarkPackReader};

/// Unsupported feature recorded during candidate mapping.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessUnsupportedFeature {
    /// Feature id.
    pub id: String,
    /// Description.
    pub description: String,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl ZkHarnessUnsupportedFeature {
    /// Construct an unsupported feature.
    pub fn new(id: impl Into<String>, description: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            description: description.into(),
            notes: Vec::new(),
        }
    }
}

/// Mapping warning.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessMappingWarning {
    /// Logical path.
    pub path: String,
    /// Warning message.
    pub message: String,
}

/// Local pack artifact mapping.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessArtifactMapping {
    /// Source relative path in the local pack.
    pub source_relative_path: String,
    /// Local pack file role.
    pub source_role: BenchmarkPackFileRole,
    /// Preserved source file digest.
    pub source_digest: ArtifactDigest,
    /// True because this is a local source artifact reference.
    pub local_only: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Family mapping.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessFamilyMapping {
    /// Generated instance id.
    pub source_instance_id: String,
    /// Source family kind.
    pub source_family_kind: FamilyKind,
    /// Internal candidate zk-Harness workload label.
    pub candidate_workload_label: String,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Mutation mapping.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessMutationMapping {
    /// Mutated instance id.
    pub source_mutation_id: String,
    /// Source mutation class.
    pub source_mutation_class: MutationClass,
    /// Internal candidate negative-test label.
    pub candidate_negative_test_label: String,
    /// Expected verdict.
    pub expected_verdict: ExpectedVerdict,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Trace mapping.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessTraceMapping {
    /// Source instance or mutation id.
    pub source_subject_id: String,
    /// Source trace id.
    pub source_trace_id: String,
    /// Internal candidate trace label.
    pub candidate_trace_label: String,
    /// Expected verdict.
    pub expected_verdict: ExpectedVerdict,
    /// True because trace comes from local pack data.
    pub local_only: bool,
}

/// Expected outcome mapping.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessExpectedOutcomeMapping {
    /// Source trace id.
    pub source_trace_id: String,
    /// Expected verdict.
    pub expected_verdict: ExpectedVerdict,
    /// Internal candidate expected outcome label.
    pub candidate_expected_outcome_label: String,
}

/// Local pack export manifest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessPackExportManifest {
    /// Source pack id.
    pub source_pack_id: String,
    /// Dry-run plan id when known.
    #[serde(default)]
    pub dry_run_plan_id: Option<String>,
    /// Exported artifact count.
    pub exported_artifact_count: usize,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Mapping from one local benchmark pack into candidate zk-Harness dry-run data.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessPackMapping {
    /// Source local pack id.
    pub source_pack_id: String,
    /// Digest of the source pack manifest.
    pub source_pack_manifest_digest: ArtifactDigest,
    /// Preserved file mappings.
    pub artifact_mappings: Vec<ZkHarnessArtifactMapping>,
    /// Family mappings.
    pub family_mappings: Vec<ZkHarnessFamilyMapping>,
    /// Mutation mappings.
    pub mutation_mappings: Vec<ZkHarnessMutationMapping>,
    /// Trace mappings.
    pub trace_mappings: Vec<ZkHarnessTraceMapping>,
    /// Expected outcome mappings.
    pub expected_outcome_mappings: Vec<ZkHarnessExpectedOutcomeMapping>,
    /// Local replay result ids retained as local-only references.
    #[serde(default)]
    pub local_replay_result_refs: Vec<String>,
    /// Unsupported features.
    #[serde(default)]
    pub unsupported_features: Vec<ZkHarnessUnsupportedFeature>,
    /// Warnings.
    #[serde(default)]
    pub warnings: Vec<ZkHarnessMappingWarning>,
    /// Export manifest.
    pub export_manifest: ZkHarnessPackExportManifest,
}

/// Build a pack mapping from a validated local pack reader.
pub fn map_pack_reader_to_zk_harness(reader: &BenchmarkPackReader) -> Result<ZkHarnessPackMapping> {
    let validation = reader.validate();
    if !validation.valid {
        return Err(ZkBenchError::zk_harness(
            "zk_harness.pack_mapping.source_pack",
            format!("source pack validation failed: {:?}", validation.errors),
        ));
    }

    let manifest = reader.manifest();
    let source_pack_manifest_digest = compute_artifact_digest(
        manifest,
        Some(crate::evidence::ArtifactKind::BenchmarkPackManifest),
        Some(crate::evidence::ArtifactRole::Manifest),
    )?;
    let artifact_mappings = manifest
        .files
        .iter()
        .map(|file| ZkHarnessArtifactMapping {
            source_relative_path: file.relative_path.clone(),
            source_role: file.role,
            source_digest: file.digest.clone(),
            local_only: true,
            notes: vec![
                "Preserved from local benchmark pack; not a zk-Harness output.".to_string(),
            ],
        })
        .collect::<Vec<_>>();

    let mut family_mappings = Vec::new();
    let mut mutation_mappings = Vec::new();
    let mut trace_mappings = Vec::new();
    let mut expected_outcome_mappings = Vec::new();
    let mut unsupported_features = default_unsupported_features();
    let mut warnings = Vec::new();

    for file in manifest
        .files
        .iter()
        .filter(|file| file.role == BenchmarkPackFileRole::GeneratedInstance)
    {
        let instance = read_pack_json::<GeneratedBenchmarkInstance>(reader, &file.relative_path)?;
        match candidate_family_label(instance.family_kind) {
            Some(label) => family_mappings.push(ZkHarnessFamilyMapping {
                source_instance_id: instance.id.clone(),
                source_family_kind: instance.family_kind,
                candidate_workload_label: label.to_string(),
                notes: vec![
                    "Internal candidate label only; not verified zk-Harness schema.".to_string(),
                ],
            }),
            None => {
                unsupported_features.push(ZkHarnessUnsupportedFeature::new(
                    format!("family_kind_{}", instance.family_kind.id_segment()),
                    "local family kind has no Phase G candidate zk-Harness label",
                ));
                warnings.push(ZkHarnessMappingWarning {
                    path: file.relative_path.clone(),
                    message: "unsupported family kind for Phase G mapping".to_string(),
                });
            }
        }
        append_trace_mappings(
            &instance.id,
            instance
                .accepted_traces
                .iter()
                .chain(instance.rejected_traces.iter())
                .map(|trace| {
                    (
                        trace.id.clone(),
                        trace
                            .expected_verdict
                            .unwrap_or(ExpectedVerdict::Inconclusive),
                    )
                }),
            &mut trace_mappings,
            &mut expected_outcome_mappings,
        );
    }

    for file in manifest
        .files
        .iter()
        .filter(|file| file.role == BenchmarkPackFileRole::MutatedInstance)
    {
        let mutation = read_pack_json::<MutatedBenchmarkInstance>(reader, &file.relative_path)?;
        match candidate_mutation_label(mutation.mutation_class) {
            Some(label) => mutation_mappings.push(ZkHarnessMutationMapping {
                source_mutation_id: mutation.id.clone(),
                source_mutation_class: mutation.mutation_class,
                candidate_negative_test_label: label.to_string(),
                expected_verdict: mutation.expected_verdict,
                notes: vec!["Internal candidate negative-test label only.".to_string()],
            }),
            None => {
                unsupported_features.push(ZkHarnessUnsupportedFeature::new(
                    format!("mutation_class_{:?}", mutation.mutation_class),
                    "mutation class has no Phase G candidate zk-Harness label",
                ));
                warnings.push(ZkHarnessMappingWarning {
                    path: file.relative_path.clone(),
                    message: "unsupported mutation class for Phase G mapping".to_string(),
                });
            }
        }
        append_trace_mappings(
            &mutation.id,
            [(mutation.primary_trace.id.clone(), mutation.expected_verdict)].into_iter(),
            &mut trace_mappings,
            &mut expected_outcome_mappings,
        );
    }

    Ok(ZkHarnessPackMapping {
        source_pack_id: manifest.id.clone(),
        source_pack_manifest_digest,
        artifact_mappings,
        family_mappings,
        mutation_mappings,
        trace_mappings,
        expected_outcome_mappings,
        local_replay_result_refs: manifest.replay_result_ids.clone(),
        unsupported_features,
        warnings,
        export_manifest: ZkHarnessPackExportManifest {
            source_pack_id: manifest.id.clone(),
            dry_run_plan_id: None,
            exported_artifact_count: manifest.files.len(),
            notes: vec!["Export manifest is for dry-run planning only.".to_string()],
        },
    })
}

/// Candidate workload label for implemented local families.
pub fn candidate_family_label(kind: FamilyKind) -> Option<&'static str> {
    match kind {
        FamilyKind::BaselineFsm => Some("control_flow_baseline_fsm"),
        FamilyKind::BranchingFsm => Some("control_flow_branching_fsm"),
        FamilyKind::BoundedCounterLoop => Some("control_flow_bounded_counter_loop"),
        FamilyKind::NestedLoop => Some("control_flow_nested_loop"),
        FamilyKind::GuardHeavyMachine => Some("control_flow_guard_heavy_machine"),
        FamilyKind::RecursiveEnvelope => Some("control_flow_recursive_envelope"),
        FamilyKind::MemoryHeavyStateMachine => Some("control_flow_memory_heavy_state_machine"),
        FamilyKind::PublicPrivateBoundaryStress => {
            Some("control_flow_public_private_boundary_stress")
        }
        FamilyKind::ZkMlControlFlowMixed => Some("control_flow_zkml_control_flow_mixed"),
    }
}

/// Candidate negative-test label for v0 mutation classes.
pub fn candidate_mutation_label(class: MutationClass) -> Option<&'static str> {
    match class {
        MutationClass::MissingConstraints => Some("missing_constraints_negative_case"),
        MutationClass::CorruptedGuards => Some("corrupted_guards_negative_case"),
        MutationClass::BadCounters => Some("bad_counters_negative_case"),
        MutationClass::StaleStateReads
        | MutationClass::InvalidUnrollBounds
        | MutationClass::NondeterministicTransitionInjection
        | MutationClass::RecursionEnvelopeMismatch
        | MutationClass::PublicPrivateBoundaryMismatch
        | MutationClass::WitnessAliasing
        | MutationClass::InvariantWeakening
        | MutationClass::InvariantStrengthening
        | MutationClass::ObservationOmission
        | MutationClass::SemanticNoOpDrift
        | MutationClass::TraceOrderingCorruption => None,
    }
}

fn expected_outcome_label(expected: ExpectedVerdict) -> &'static str {
    match expected {
        ExpectedVerdict::Accept => "expected_accept",
        ExpectedVerdict::Reject => "expected_reject",
        ExpectedVerdict::BackendError => "expected_backend_error",
        ExpectedVerdict::Inconclusive => "expected_inconclusive",
        ExpectedVerdict::CapabilityGap => "expected_capability_gap",
        ExpectedVerdict::UnsoundIfAccepted => "expected_unsound_if_accepted",
    }
}

fn append_trace_mappings(
    source_subject_id: &str,
    traces: impl Iterator<Item = (String, ExpectedVerdict)>,
    trace_mappings: &mut Vec<ZkHarnessTraceMapping>,
    expected_outcome_mappings: &mut Vec<ZkHarnessExpectedOutcomeMapping>,
) {
    for (source_trace_id, expected_verdict) in traces {
        trace_mappings.push(ZkHarnessTraceMapping {
            source_subject_id: source_subject_id.to_string(),
            source_trace_id: source_trace_id.clone(),
            candidate_trace_label: format!("{source_subject_id}::{source_trace_id}"),
            expected_verdict,
            local_only: true,
        });
        expected_outcome_mappings.push(ZkHarnessExpectedOutcomeMapping {
            source_trace_id,
            expected_verdict,
            candidate_expected_outcome_label: expected_outcome_label(expected_verdict).to_string(),
        });
    }
}

fn read_pack_json<T: serde::de::DeserializeOwned>(
    reader: &BenchmarkPackReader,
    relative_path: &str,
) -> Result<T> {
    let path = reader.root().join(relative_path);
    let json = fs::read_to_string(&path)
        .map_err(|error| ZkBenchError::zk_harness(path.display().to_string(), error.to_string()))?;
    serde_json::from_str(&json)
        .map_err(|error| ZkBenchError::deserialization(relative_path, error.to_string()))
}

fn default_unsupported_features() -> Vec<ZkHarnessUnsupportedFeature> {
    vec![
        ZkHarnessUnsupportedFeature::new(
            "live_execution",
            "external execution is disabled by default",
        ),
        ZkHarnessUnsupportedFeature::new(
            "external_result_import",
            "external benchmark results are not imported in Phase G",
        ),
        ZkHarnessUnsupportedFeature::new(
            "metric_values",
            "metric mappings are schema-only and contain no values",
        ),
    ]
}

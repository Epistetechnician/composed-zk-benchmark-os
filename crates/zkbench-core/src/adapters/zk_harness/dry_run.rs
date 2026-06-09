//! zk-Harness dry-run plan data.

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{compute_artifact_digest, ArtifactDigest, ArtifactRole, ClaimBoundary};
use crate::pack::BenchmarkPackReader;

use super::evidence::{ZkHarnessEvidenceMapping, ZkHarnessEvidencePolicy};
use super::manifest::ZkHarnessAdapterManifest;
use super::mapping::{map_pack_reader_to_zk_harness, ZkHarnessPackMapping};
use super::metrics::{default_zk_harness_metric_mappings, ZkHarnessMetricMapping};

/// zk-Harness dry-run plan id.
pub type ZkHarnessDryRunPlanId = String;

/// zk-Harness dry-run plan version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessDryRunPlanVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for ZkHarnessDryRunPlanVersion {
    fn default() -> Self {
        Self {
            value: "phase-g-zk-harness-dry-run-plan-v0".to_string(),
        }
    }
}

/// Dry-run plan subject.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessPlanSubject {
    /// Source local pack id.
    pub source_pack_id: String,
    /// Source pack manifest digest.
    pub source_pack_manifest_digest: ArtifactDigest,
    /// Generated instance ids.
    pub generated_instance_ids: Vec<String>,
    /// Mutation ids.
    pub mutation_ids: Vec<String>,
    /// Replay manifest ids from local source pack.
    pub replay_manifest_ids: Vec<String>,
    /// Replay result ids from local source pack.
    pub replay_result_ids: Vec<String>,
    /// Local source pack claim boundary.
    pub local_pack_claim_boundary: ClaimBoundary,
}

/// Future planned step kinds. These are inert dry-run labels only.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ZkHarnessPlanStepKind {
    /// Prepare local input artifacts.
    PrepareInputs,
    /// Future circuit compilation.
    CompileCircuit,
    /// Future witness generation.
    GenerateWitness,
    /// Future proof generation.
    Prove,
    /// Future verification.
    Verify,
    /// Future metric collection.
    CollectMetrics,
    /// Future result normalization.
    NormalizeResults,
}

/// External tool reference as inert data.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessExternalToolRef {
    /// Display tool name.
    pub tool_name: String,
    /// Tool role.
    pub tool_role: String,
    /// Optional version requirement.
    #[serde(default)]
    pub version_requirement: Option<String>,
    /// Whether source has been verified. False for Phase G.
    pub verified_source: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Planned command argument as inert data.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessCommandArgument {
    /// Argument name.
    pub name: String,
    /// Argument value.
    pub value: String,
    /// True because this is inert data.
    pub inert: bool,
}

/// Planned command environment variable as inert data.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessCommandEnvironment {
    /// Variable name.
    pub name: String,
    /// Variable value.
    pub value: String,
    /// True because this is inert data.
    pub inert: bool,
}

/// Planned command artifact reference.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessCommandArtifact {
    /// Relative artifact reference.
    pub relative_uri: String,
    /// Artifact role.
    pub role: ArtifactRole,
    /// Required flag.
    pub required: bool,
}

/// Inert planned command description.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessPlannedCommand {
    /// Step kind this command would belong to in a future external replay.
    pub step_kind: ZkHarnessPlanStepKind,
    /// External tool reference.
    pub tool_ref: ZkHarnessExternalToolRef,
    /// Display program name. This is not executed.
    pub display_program_name: String,
    /// Arguments as data.
    #[serde(default)]
    pub arguments: Vec<ZkHarnessCommandArgument>,
    /// Environment values as data.
    #[serde(default)]
    pub environment: Vec<ZkHarnessCommandEnvironment>,
    /// Input artifact references.
    #[serde(default)]
    pub input_artifacts: Vec<ZkHarnessCommandArtifact>,
    /// Expected output artifact roles.
    #[serde(default)]
    pub expected_output_artifact_roles: Vec<ArtifactRole>,
    /// Working directory policy.
    pub working_directory_policy: String,
    /// True because Phase G commands are inert data.
    pub inert: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl ZkHarnessPlannedCommand {
    /// Return a human-readable inert description.
    pub fn describe(&self) -> String {
        format!(
            "{:?} planned for {} as dry-run data only",
            self.step_kind, self.display_program_name
        )
    }
}

/// Dry-run plan step.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessPlanStep {
    /// Step id.
    pub id: String,
    /// Step kind.
    pub kind: ZkHarnessPlanStepKind,
    /// True because this is dry-run only.
    pub dry_run_only: bool,
    /// Inert planned command description.
    pub planned_command: ZkHarnessPlannedCommand,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// External execution policy.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ZkHarnessExecutionPolicy {
    /// Disabled by default.
    DisabledByDefault,
    /// Dry-run only.
    DryRunOnly,
    /// Requires manual review.
    RequiresManualReview,
    /// Future external runner required.
    FutureExternalRunnerRequired,
    /// Future live execution placeholder. Validation rejects this in Phase G.
    FutureLiveExecution,
}

impl ZkHarnessExecutionPolicy {
    /// True if the policy is allowed in Phase G.
    pub fn is_phase_g_allowed(self) -> bool {
        matches!(
            self,
            Self::DisabledByDefault | Self::DryRunOnly | Self::RequiresManualReview
        )
    }
}

/// zk-Harness dry-run plan.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessDryRunPlan {
    /// Plan id.
    pub id: ZkHarnessDryRunPlanId,
    /// Plan version.
    pub plan_version: ZkHarnessDryRunPlanVersion,
    /// Adapter manifest id.
    pub adapter_manifest_id: String,
    /// Source local benchmark pack id.
    pub source_benchmark_pack_id: String,
    /// Source pack manifest digest.
    pub source_pack_digest: ArtifactDigest,
    /// Plan subject.
    pub subject: ZkHarnessPlanSubject,
    /// Pack mapping.
    pub pack_mapping: ZkHarnessPackMapping,
    /// Metric mappings. Values must be absent in Phase G.
    pub metric_mappings: Vec<ZkHarnessMetricMapping>,
    /// Evidence mapping schema.
    pub evidence_mapping: ZkHarnessEvidenceMapping,
    /// Planned dry-run steps.
    pub planned_steps: Vec<ZkHarnessPlanStep>,
    /// Planned artifacts.
    pub planned_artifacts: Vec<ZkHarnessCommandArtifact>,
    /// Unsupported features.
    #[serde(default)]
    pub unsupported_features: Vec<super::mapping::ZkHarnessUnsupportedFeature>,
    /// Warnings.
    #[serde(default)]
    pub warnings: Vec<super::mapping::ZkHarnessMappingWarning>,
    /// Execution policy.
    pub execution_policy: ZkHarnessExecutionPolicy,
    /// Claim boundary for this plan.
    pub claim_boundary: ClaimBoundary,
    /// Evidence policy.
    pub evidence_policy: ZkHarnessEvidencePolicy,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl ZkHarnessDryRunPlan {
    /// Return true when all planned commands are inert.
    pub fn contains_no_executable_process(&self) -> bool {
        self.planned_steps
            .iter()
            .all(|step| step.dry_run_only && step.planned_command.inert)
    }

    /// Return planned command references.
    pub fn planned_commands(&self) -> Vec<&ZkHarnessPlannedCommand> {
        self.planned_steps
            .iter()
            .map(|step| &step.planned_command)
            .collect()
    }
}

/// Builder for zk-Harness dry-run plans.
#[derive(Debug, Clone)]
pub struct ZkHarnessDryRunPlanner {
    manifest: ZkHarnessAdapterManifest,
    mapping: Option<ZkHarnessPackMapping>,
    subject: Option<ZkHarnessPlanSubject>,
}

impl ZkHarnessDryRunPlanner {
    /// Create a planner from an adapter manifest.
    pub fn new(manifest: ZkHarnessAdapterManifest) -> Self {
        Self {
            manifest,
            mapping: None,
            subject: None,
        }
    }

    /// Map a validated local benchmark pack into candidate zk-Harness labels.
    pub fn map_pack(mut self, reader: &BenchmarkPackReader) -> Result<Self> {
        let mapping = map_pack_reader_to_zk_harness(reader)?;
        let pack_manifest = reader.manifest();
        let subject = ZkHarnessPlanSubject {
            source_pack_id: pack_manifest.id.clone(),
            source_pack_manifest_digest: mapping.source_pack_manifest_digest.clone(),
            generated_instance_ids: pack_manifest.generated_instance_ids.clone(),
            mutation_ids: pack_manifest.mutation_ids.clone(),
            replay_manifest_ids: pack_manifest.replay_manifest_ids.clone(),
            replay_result_ids: pack_manifest.replay_result_ids.clone(),
            local_pack_claim_boundary: pack_manifest.claim_boundary,
        };
        self.mapping = Some(mapping);
        self.subject = Some(subject);
        Ok(self)
    }

    /// Build the dry-run plan.
    pub fn build(self) -> Result<ZkHarnessDryRunPlan> {
        let mapping = self.mapping.ok_or_else(|| {
            ZkBenchError::zk_harness(
                "zk_harness.dry_run_plan.mapping",
                "source pack mapping is missing",
            )
        })?;
        let subject = self.subject.ok_or_else(|| {
            ZkBenchError::zk_harness(
                "zk_harness.dry_run_plan.subject",
                "source pack subject is missing",
            )
        })?;
        let mut export_manifest = mapping.export_manifest.clone();
        let planned_steps = planned_steps(&mapping);
        let planned_artifacts = planned_artifacts(&mapping);
        let plan_digest_input = (
            &self.manifest.id,
            &subject.source_pack_id,
            &subject.source_pack_manifest_digest,
            &mapping,
            &planned_steps,
        );
        let plan_digest = compute_artifact_digest(
            &plan_digest_input,
            Some(crate::evidence::ArtifactKind::Other),
            Some(crate::evidence::ArtifactRole::Manifest),
        )?;
        let plan_id = format!("zk_harness_dry_run_plan_{}", plan_digest.hex_digest);
        export_manifest.dry_run_plan_id = Some(plan_id.clone());
        let mut mapping = mapping;
        mapping.export_manifest = export_manifest;
        Ok(ZkHarnessDryRunPlan {
            id: plan_id,
            plan_version: ZkHarnessDryRunPlanVersion::default(),
            adapter_manifest_id: self.manifest.id,
            source_benchmark_pack_id: subject.source_pack_id.clone(),
            source_pack_digest: subject.source_pack_manifest_digest.clone(),
            subject,
            metric_mappings: default_zk_harness_metric_mappings(),
            evidence_mapping: ZkHarnessEvidenceMapping::default(),
            planned_steps,
            planned_artifacts,
            unsupported_features: mapping.unsupported_features.clone(),
            warnings: mapping.warnings.clone(),
            execution_policy: ZkHarnessExecutionPolicy::DisabledByDefault,
            claim_boundary: ClaimBoundary::Level0DesignNote,
            evidence_policy: self.manifest.evidence_policy,
            notes: vec![
                "zk-Harness dry-run plans are not benchmark results.".to_string(),
                "External execution is disabled by default.".to_string(),
                "Local pack source references are not converted into zk-Harness results."
                    .to_string(),
            ],
            pack_mapping: mapping,
        })
    }
}

fn planned_steps(mapping: &ZkHarnessPackMapping) -> Vec<ZkHarnessPlanStep> {
    [
        ZkHarnessPlanStepKind::PrepareInputs,
        ZkHarnessPlanStepKind::CompileCircuit,
        ZkHarnessPlanStepKind::GenerateWitness,
        ZkHarnessPlanStepKind::Prove,
        ZkHarnessPlanStepKind::Verify,
        ZkHarnessPlanStepKind::CollectMetrics,
        ZkHarnessPlanStepKind::NormalizeResults,
    ]
    .into_iter()
    .map(|kind| {
        let id = format!("planned_{:?}", kind).to_ascii_lowercase();
        let command = planned_command(kind, mapping);
        ZkHarnessPlanStep {
            id,
            kind,
            dry_run_only: true,
            planned_command: command,
            notes: vec!["Future zk-Harness step represented as inert data only.".to_string()],
        }
    })
    .collect()
}

fn planned_command(
    kind: ZkHarnessPlanStepKind,
    mapping: &ZkHarnessPackMapping,
) -> ZkHarnessPlannedCommand {
    ZkHarnessPlannedCommand {
        step_kind: kind,
        tool_ref: ZkHarnessExternalToolRef {
            tool_name: "zk-Harness".to_string(),
            tool_role: "future benchmark runner".to_string(),
            version_requirement: None,
            verified_source: false,
            notes: vec!["Source verification required before live integration.".to_string()],
        },
        display_program_name: "zk-harness".to_string(),
        arguments: vec![
            ZkHarnessCommandArgument {
                name: "mode".to_string(),
                value: "dry_run_plan".to_string(),
                inert: true,
            },
            ZkHarnessCommandArgument {
                name: "source_pack_id".to_string(),
                value: mapping.source_pack_id.clone(),
                inert: true,
            },
            ZkHarnessCommandArgument {
                name: "planned_step".to_string(),
                value: format!("{:?}", kind),
                inert: true,
            },
        ],
        environment: vec![ZkHarnessCommandEnvironment {
            name: "ZK_HARNESS_PHASE".to_string(),
            value: "phase_g_dry_run_only".to_string(),
            inert: true,
        }],
        input_artifacts: mapping
            .artifact_mappings
            .iter()
            .map(|artifact| ZkHarnessCommandArtifact {
                relative_uri: artifact.source_relative_path.clone(),
                role: ArtifactRole::Input,
                required: true,
            })
            .collect(),
        expected_output_artifact_roles: vec![ArtifactRole::Report],
        working_directory_policy: "caller_supplied_relative_pack_root".to_string(),
        inert: true,
        notes: vec![
            "Inert planned command; no process handle or shell command is present.".to_string(),
        ],
    }
}

fn planned_artifacts(mapping: &ZkHarnessPackMapping) -> Vec<ZkHarnessCommandArtifact> {
    mapping
        .artifact_mappings
        .iter()
        .map(|artifact| ZkHarnessCommandArtifact {
            relative_uri: artifact.source_relative_path.clone(),
            role: ArtifactRole::Input,
            required: true,
        })
        .collect()
}

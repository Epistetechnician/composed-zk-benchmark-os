//! Narrow zkML workload plan data.

use serde::{Deserialize, Serialize};

use crate::evidence::{ArtifactRole, ClaimBoundary};

use super::evidence::{ZkmlNarrowEvidenceMapping, ZkmlNarrowEvidencePolicy};
use super::manifest::ZkmlNarrowAdapterManifest;
use super::mapping::{default_zkml_narrow_fixture_scope, ZkmlNarrowWorkloadScope};

/// Narrow zkML workload plan id.
pub type ZkmlNarrowWorkloadPlanId = String;

/// Narrow zkML workload plan version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowWorkloadPlanVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for ZkmlNarrowWorkloadPlanVersion {
    fn default() -> Self {
        Self {
            value: "phase-l-narrow-zkml-workload-plan-v0".to_string(),
        }
    }
}

/// Execution policy for Phase L workload planning.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ZkmlNarrowExecutionPolicy {
    /// Disabled for Phase L.
    Disabled,
    /// Manual handoff only in future phases.
    ManualHandoffOnly,
    /// Future live execution placeholder.
    FutureLiveExecution,
}

impl ZkmlNarrowExecutionPolicy {
    /// Return true when the policy is allowed for Phase L planning.
    pub fn is_phase_l_allowed(self) -> bool {
        matches!(self, Self::Disabled | Self::ManualHandoffOnly)
    }
}

/// Future planned step kinds. These are inert labels only.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ZkmlNarrowWorkloadStepKind {
    /// Prepare semantic fixture inputs.
    PrepareSemanticFixture,
    /// Future model artifact staging.
    StageModelArtifact,
    /// Future witness generation.
    GenerateWitness,
    /// Future proof generation.
    ProveWorkload,
    /// Future verification.
    VerifyWorkload,
    /// Future metric collection.
    CollectMetrics,
    /// Future result normalization.
    NormalizeResults,
}

/// External tool reference as inert data.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowToolRef {
    /// Display tool name.
    pub tool_name: String,
    /// Tool role.
    pub tool_role: String,
    /// Optional version requirement.
    #[serde(default)]
    pub version_requirement: Option<String>,
    /// Whether source has been verified. False for Phase L.
    pub verified_source: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Inert planned command description.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowPlannedCommand {
    /// Step kind this command would belong to in a future external replay.
    pub step_kind: ZkmlNarrowWorkloadStepKind,
    /// External tool reference.
    pub tool_ref: ZkmlNarrowToolRef,
    /// Display program name. This is not executed.
    pub display_program_name: String,
    /// Working directory policy.
    pub working_directory_policy: String,
    /// True because Phase L commands are inert data.
    pub inert: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl ZkmlNarrowPlannedCommand {
    /// Build a conservative inert zkML command placeholder.
    pub fn inert_zkml(step_kind: ZkmlNarrowWorkloadStepKind) -> Self {
        Self {
            step_kind,
            tool_ref: ZkmlNarrowToolRef {
                tool_name: "zkml-workload-runner".to_string(),
                tool_role: "future narrow zkML workload lane".to_string(),
                version_requirement: None,
                verified_source: false,
                notes: vec!["Future source verification required.".to_string()],
            },
            display_program_name: "zkml-workload-runner".to_string(),
            working_directory_policy: "relative_only".to_string(),
            inert: true,
            notes: vec!["Inert planned command; not executed in Phase L.".to_string()],
        }
    }
}

/// Planned workload step.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowWorkloadStep {
    /// Step id.
    pub id: String,
    /// Step kind.
    pub step_kind: ZkmlNarrowWorkloadStepKind,
    /// Planned command.
    pub planned_command: ZkmlNarrowPlannedCommand,
    /// Expected output artifact roles.
    #[serde(default)]
    pub expected_output_artifact_roles: Vec<ArtifactRole>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Narrow zkML workload plan.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowWorkloadPlan {
    /// Plan id.
    pub id: ZkmlNarrowWorkloadPlanId,
    /// Plan version.
    pub plan_version: ZkmlNarrowWorkloadPlanVersion,
    /// Adapter manifest id.
    pub adapter_manifest_id: String,
    /// Semantic fixture scope.
    pub scope: ZkmlNarrowWorkloadScope,
    /// Evidence mapping.
    pub evidence_mapping: ZkmlNarrowEvidenceMapping,
    /// Evidence policy.
    pub evidence_policy: ZkmlNarrowEvidencePolicy,
    /// Execution policy.
    pub execution_policy: ZkmlNarrowExecutionPolicy,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Planned steps.
    pub planned_steps: Vec<ZkmlNarrowWorkloadStep>,
    /// Metric schema labels only; no observed values.
    #[serde(default)]
    pub metric_schema: Vec<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl ZkmlNarrowWorkloadPlan {
    /// Return true when every planned command is inert.
    pub fn contains_no_executable_process(&self) -> bool {
        self.planned_steps
            .iter()
            .all(|step| step.planned_command.inert)
    }

    /// Return planned commands.
    pub fn planned_commands(&self) -> Vec<&ZkmlNarrowPlannedCommand> {
        self.planned_steps
            .iter()
            .map(|step| &step.planned_command)
            .collect()
    }
}

/// Build the default Phase L narrow zkML workload plan.
pub fn build_default_zkml_narrow_workload_plan(
    manifest: &ZkmlNarrowAdapterManifest,
) -> ZkmlNarrowWorkloadPlan {
    let scope = default_zkml_narrow_fixture_scope();
    let step_specs = [
        (
            "prepare_semantic_fixture",
            ZkmlNarrowWorkloadStepKind::PrepareSemanticFixture,
        ),
        (
            "stage_model_artifact",
            ZkmlNarrowWorkloadStepKind::StageModelArtifact,
        ),
        ("prove_workload", ZkmlNarrowWorkloadStepKind::ProveWorkload),
        (
            "verify_workload",
            ZkmlNarrowWorkloadStepKind::VerifyWorkload,
        ),
    ];
    let planned_steps = step_specs
        .into_iter()
        .map(|(id, step_kind)| ZkmlNarrowWorkloadStep {
            id: id.to_string(),
            step_kind,
            planned_command: ZkmlNarrowPlannedCommand::inert_zkml(step_kind),
            expected_output_artifact_roles: vec![ArtifactRole::Output],
            notes: vec!["Inert workload step only.".to_string()],
        })
        .collect();

    ZkmlNarrowWorkloadPlan {
        id: "zkml_narrow_workload_plan_control_flow_mixed_v0".to_string(),
        plan_version: ZkmlNarrowWorkloadPlanVersion::default(),
        adapter_manifest_id: manifest.id.clone(),
        scope,
        evidence_mapping: ZkmlNarrowEvidenceMapping::default(),
        evidence_policy: manifest.evidence_policy.clone(),
        execution_policy: ZkmlNarrowExecutionPolicy::Disabled,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        planned_steps,
        metric_schema: vec![
            "prover_time".to_string(),
            "verifier_latency".to_string(),
            "proof_size".to_string(),
            "zkml_accuracy_if_available".to_string(),
            "public_private_boundary_result".to_string(),
            "negative_test_result".to_string(),
        ],
        notes: vec![
            "Narrow zkML workload plans are not benchmark results.".to_string(),
            "zkML metrics do not prove semantic soundness.".to_string(),
        ],
    }
}

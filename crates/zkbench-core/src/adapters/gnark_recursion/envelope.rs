//! gnark recursion envelope plan data.

use serde::{Deserialize, Serialize};

use crate::evidence::{ArtifactRole, ClaimBoundary};

use super::evidence::{GnarkRecursionEvidenceMapping, GnarkRecursionEvidencePolicy};
use super::manifest::GnarkRecursionAdapterManifest;
use super::mapping::{default_gnark_recursion_fixture_scope, GnarkRecursionEnvelopeScope};

/// gnark recursion envelope plan id.
pub type GnarkRecursionEnvelopePlanId = String;

/// gnark recursion envelope plan version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionEnvelopePlanVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for GnarkRecursionEnvelopePlanVersion {
    fn default() -> Self {
        Self {
            value: "phase-k-gnark-recursion-envelope-plan-v0".to_string(),
        }
    }
}

/// Execution policy for Phase K envelope planning.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum GnarkRecursionExecutionPolicy {
    /// Disabled for Phase K.
    Disabled,
    /// Manual handoff only in future phases.
    ManualHandoffOnly,
    /// Future live execution placeholder.
    FutureLiveExecution,
}

impl GnarkRecursionExecutionPolicy {
    /// Return true when the policy is allowed for Phase K planning.
    pub fn is_phase_k_allowed(self) -> bool {
        matches!(self, Self::Disabled | Self::ManualHandoffOnly)
    }
}

/// Future planned step kinds. These are inert labels only.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum GnarkRecursionEnvelopeStepKind {
    /// Prepare semantic fixture inputs.
    PrepareSemanticFixture,
    /// Future circuit compilation.
    CompileRecursionCircuit,
    /// Future witness generation.
    GenerateWitness,
    /// Future proof generation.
    ProveRecursion,
    /// Future verification.
    VerifyRecursion,
    /// Future metric collection.
    CollectMetrics,
    /// Future result normalization.
    NormalizeResults,
}

/// External tool reference as inert data.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionToolRef {
    /// Display tool name.
    pub tool_name: String,
    /// Tool role.
    pub tool_role: String,
    /// Optional version requirement.
    #[serde(default)]
    pub version_requirement: Option<String>,
    /// Whether source has been verified. False for Phase K.
    pub verified_source: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Inert planned command description.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionPlannedCommand {
    /// Step kind this command would belong to in a future external replay.
    pub step_kind: GnarkRecursionEnvelopeStepKind,
    /// External tool reference.
    pub tool_ref: GnarkRecursionToolRef,
    /// Display program name. This is not executed.
    pub display_program_name: String,
    /// Working directory policy.
    pub working_directory_policy: String,
    /// True because Phase K commands are inert data.
    pub inert: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl GnarkRecursionPlannedCommand {
    /// Build a conservative inert gnark command placeholder.
    pub fn inert_gnark(step_kind: GnarkRecursionEnvelopeStepKind) -> Self {
        Self {
            step_kind,
            tool_ref: GnarkRecursionToolRef {
                tool_name: "gnark".to_string(),
                tool_role: "future recursion-envelope lane".to_string(),
                version_requirement: None,
                verified_source: false,
                notes: vec!["Future source verification required.".to_string()],
            },
            display_program_name: "gnark".to_string(),
            working_directory_policy: "relative_only".to_string(),
            inert: true,
            notes: vec!["Inert planned command; not executed in Phase K.".to_string()],
        }
    }
}

/// Planned envelope step.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionEnvelopeStep {
    /// Step id.
    pub id: String,
    /// Step kind.
    pub step_kind: GnarkRecursionEnvelopeStepKind,
    /// Planned command.
    pub planned_command: GnarkRecursionPlannedCommand,
    /// Expected output artifact roles.
    #[serde(default)]
    pub expected_output_artifact_roles: Vec<ArtifactRole>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// gnark recursion envelope plan.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionEnvelopePlan {
    /// Plan id.
    pub id: GnarkRecursionEnvelopePlanId,
    /// Plan version.
    pub plan_version: GnarkRecursionEnvelopePlanVersion,
    /// Adapter manifest id.
    pub adapter_manifest_id: String,
    /// Semantic fixture scope.
    pub scope: GnarkRecursionEnvelopeScope,
    /// Evidence mapping.
    pub evidence_mapping: GnarkRecursionEvidenceMapping,
    /// Evidence policy.
    pub evidence_policy: GnarkRecursionEvidencePolicy,
    /// Execution policy.
    pub execution_policy: GnarkRecursionExecutionPolicy,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Planned steps.
    pub planned_steps: Vec<GnarkRecursionEnvelopeStep>,
    /// Metric schema labels only; no observed values.
    #[serde(default)]
    pub metric_schema: Vec<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl GnarkRecursionEnvelopePlan {
    /// Return true when every planned command is inert.
    pub fn contains_no_executable_process(&self) -> bool {
        self.planned_steps
            .iter()
            .all(|step| step.planned_command.inert)
    }

    /// Return planned commands.
    pub fn planned_commands(&self) -> Vec<&GnarkRecursionPlannedCommand> {
        self.planned_steps
            .iter()
            .map(|step| &step.planned_command)
            .collect()
    }
}

/// Build the default Phase K gnark recursion envelope plan.
pub fn build_default_gnark_recursion_envelope_plan(
    manifest: &GnarkRecursionAdapterManifest,
) -> GnarkRecursionEnvelopePlan {
    let scope = default_gnark_recursion_fixture_scope();
    let step_specs = [
        (
            "prepare_semantic_fixture",
            GnarkRecursionEnvelopeStepKind::PrepareSemanticFixture,
        ),
        (
            "compile_recursion_circuit",
            GnarkRecursionEnvelopeStepKind::CompileRecursionCircuit,
        ),
        (
            "prove_recursion",
            GnarkRecursionEnvelopeStepKind::ProveRecursion,
        ),
        (
            "verify_recursion",
            GnarkRecursionEnvelopeStepKind::VerifyRecursion,
        ),
    ];
    let planned_steps = step_specs
        .into_iter()
        .map(|(id, step_kind)| GnarkRecursionEnvelopeStep {
            id: id.to_string(),
            step_kind,
            planned_command: GnarkRecursionPlannedCommand::inert_gnark(step_kind),
            expected_output_artifact_roles: vec![ArtifactRole::Output],
            notes: vec!["Inert envelope step only.".to_string()],
        })
        .collect();

    GnarkRecursionEnvelopePlan {
        id: "gnark_recursion_envelope_plan_recursive_loop_envelope_v0".to_string(),
        plan_version: GnarkRecursionEnvelopePlanVersion::default(),
        adapter_manifest_id: manifest.id.clone(),
        scope,
        evidence_mapping: GnarkRecursionEvidenceMapping::default(),
        evidence_policy: manifest.evidence_policy.clone(),
        execution_policy: GnarkRecursionExecutionPolicy::Disabled,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        planned_steps,
        metric_schema: vec![
            "recursion_depth".to_string(),
            "proof_size".to_string(),
            "verifier_latency".to_string(),
            "aggregation_width".to_string(),
            "envelope_verification_status".to_string(),
        ],
        notes: vec![
            "gnark recursion envelope plans are not benchmark results.".to_string(),
            "Recursion proof is not semantic proof.".to_string(),
        ],
    }
}

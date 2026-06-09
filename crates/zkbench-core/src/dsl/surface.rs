//! Surface DSL data structures.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use crate::evidence::{ClaimBoundary, ExpectedVerdict};
use crate::mutation::MutationSpec;
use crate::value::{FieldVisibility, Value, ValueType};

use super::expr::{ActionSpec, GuardSpec};

/// Complete top-level Surface DSL spec.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SurfaceSpec {
    /// Machine semantics.
    pub machine: MachineSpec,
    /// Oracle trace declarations.
    #[serde(default)]
    pub oracle: OracleSpec,
    /// Backend or local targets requested by the spec.
    #[serde(default)]
    pub targets: Vec<TargetSpec>,
    /// Mutation metadata declared by the spec.
    #[serde(default)]
    pub mutations: Vec<MutationSpec>,
    /// Evidence claim boundary requested by the spec.
    #[serde(default)]
    pub evidence: EvidenceSpec,
}

/// Machine declaration.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MachineSpec {
    /// Machine identifier.
    pub id: String,
    /// Human-readable description.
    #[serde(default)]
    pub description: Option<String>,
    /// Initial state id.
    pub initial_state: String,
    /// Semantic equivalence class.
    #[serde(default)]
    pub semantic_equivalence_class: Option<SemanticEquivalenceClass>,
    /// State declarations.
    #[serde(default)]
    pub states: Vec<StateSpec>,
    /// Field declarations.
    #[serde(default)]
    pub fields: Vec<FieldSpec>,
    /// Transition declarations.
    #[serde(default)]
    pub transitions: Vec<TransitionSpec>,
    /// Loop metadata declarations.
    #[serde(default)]
    pub loops: Vec<LoopSpec>,
    /// Invariant declarations.
    #[serde(default)]
    pub invariants: Vec<InvariantSpec>,
    /// Public observation declarations.
    #[serde(default)]
    pub observations: Vec<ObserveSpec>,
    /// Witness policy.
    #[serde(default)]
    pub witness_policy: WitnessPolicy,
    /// Public input declarations.
    #[serde(default)]
    pub public_inputs: Vec<PublicInputSpec>,
    /// Private witness declarations.
    #[serde(default)]
    pub private_witnesses: Vec<PrivateWitnessSpec>,
}

/// Named state.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct StateSpec {
    /// State id.
    pub id: String,
    /// Optional description.
    #[serde(default)]
    pub description: Option<String>,
}

/// Field declaration.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FieldSpec {
    /// Field id.
    pub id: String,
    /// Field type.
    #[serde(rename = "type")]
    pub field_type: ValueType,
    /// Initial value for local oracle evaluation.
    #[serde(default)]
    pub initial: Option<Value>,
    /// Visibility boundary.
    #[serde(default)]
    pub visibility: FieldVisibility,
}

/// Transition declaration.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TransitionSpec {
    /// Transition id.
    pub id: String,
    /// Source state id.
    pub from: String,
    /// Target state id.
    pub to: String,
    /// Guard expression.
    #[serde(default)]
    pub guard: GuardSpec,
    /// Ordered transition actions.
    #[serde(default)]
    pub actions: Vec<ActionSpec>,
}

/// Loop metadata declaration.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LoopSpec {
    /// Loop id.
    pub id: String,
    /// Bound expression or non-executable metadata.
    #[serde(default)]
    pub bound: Option<GuardSpec>,
    /// Transition ids in the loop body.
    #[serde(default)]
    pub body: Vec<String>,
    /// Metadata for future generator and adapter phases.
    #[serde(default)]
    pub metadata: BTreeMap<String, Value>,
}

/// Invariant declaration.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct InvariantSpec {
    /// Invariant id.
    pub id: String,
    /// Invariant guard.
    pub guard: GuardSpec,
    /// Optional invariant scope.
    #[serde(default)]
    pub scope: Option<String>,
}

/// Public observation declaration.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ObserveSpec {
    /// Observation id.
    pub id: String,
    /// Observed field id.
    pub field: String,
    /// Observation visibility.
    #[serde(default)]
    pub visibility: FieldVisibility,
}

/// Target metadata from the Surface DSL.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TargetSpec {
    /// Target id.
    pub id: String,
    /// Target kind such as `local`.
    pub kind: String,
    /// Required capability names.
    #[serde(default)]
    pub required_capabilities: Vec<String>,
}

/// Evidence metadata from the Surface DSL.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceSpec {
    /// Maximum current claim boundary for this spec.
    pub claim_boundary: ClaimBoundary,
    /// True only for planned future evidence metadata.
    #[serde(default)]
    pub planned: bool,
    /// Human-readable notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for EvidenceSpec {
    fn default() -> Self {
        Self {
            claim_boundary: ClaimBoundary::Level0DesignNote,
            planned: false,
            notes: Vec::new(),
        }
    }
}

/// Trace oracle declarations.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Default)]
pub struct OracleSpec {
    /// Traces expected to be locally accepted.
    #[serde(default)]
    pub accepted_traces: Vec<TraceSpec>,
    /// Traces expected to be locally rejected.
    #[serde(default)]
    pub rejected_traces: Vec<TraceSpec>,
}

/// Trace declaration for local oracle evaluation.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TraceSpec {
    /// Trace id.
    pub id: String,
    /// Optional explicit initial state.
    #[serde(default)]
    pub initial_state: Option<String>,
    /// Optional initial field overrides.
    #[serde(default)]
    pub initial_fields: BTreeMap<String, Value>,
    /// Ordered trace steps.
    #[serde(default)]
    pub steps: Vec<TraceStepSpec>,
    /// Optional expected final state.
    #[serde(default)]
    pub expected_final_state: Option<String>,
    /// Optional expected final field values.
    #[serde(default)]
    pub expected_final_fields: BTreeMap<String, Value>,
    /// Expected semantic verdict for this trace.
    #[serde(default)]
    pub expected_verdict: Option<ExpectedVerdict>,
    /// Capabilities required beyond the v0 local executable subset.
    #[serde(default)]
    pub requires_capabilities: Vec<String>,
}

/// A single trace step.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TraceStepSpec {
    /// Transition id to execute.
    pub transition: String,
}

/// Witness policy for public/private boundary checks.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct WitnessPolicy {
    /// Public input field ids.
    #[serde(default)]
    pub public_inputs: Vec<String>,
    /// Private witness field ids.
    #[serde(default)]
    pub private_witnesses: Vec<String>,
    /// Whether aliasing between witness values is allowed.
    #[serde(default)]
    pub aliasing_allowed: bool,
}

/// Public input declaration.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PublicInputSpec {
    /// Public input id.
    pub id: String,
    /// Referenced field id.
    pub field: String,
    /// Optional description.
    #[serde(default)]
    pub description: Option<String>,
}

/// Private witness declaration.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PrivateWitnessSpec {
    /// Private witness id.
    pub id: String,
    /// Referenced field id.
    pub field: String,
    /// Optional description.
    #[serde(default)]
    pub description: Option<String>,
}

/// Semantic equivalence class declaration.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SemanticEquivalenceClass {
    /// Class id.
    pub id: String,
    /// Optional description.
    #[serde(default)]
    pub description: Option<String>,
}

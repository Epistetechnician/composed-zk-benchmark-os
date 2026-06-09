//! Canonical Semantic IR types.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use crate::dsl::surface::{
    EvidenceSpec, LoopSpec, ObserveSpec, PrivateWitnessSpec, PublicInputSpec,
    SemanticEquivalenceClass, TargetSpec, TraceSpec, WitnessPolicy,
};
use crate::error::{Result, ZkBenchError};
use crate::mutation::MutationSpec;
use crate::value::{FieldVisibility, Value, ValueType};

use super::expr::{ActionSpec, GuardSpec};

/// Canonical Semantic IR. This is the local truth boundary for Level 1 tests.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SemanticIr {
    /// Canonical machine.
    pub machine: CanonicalMachine,
    /// Canonical oracle declarations.
    pub oracle: CanonicalOracle,
    /// Target metadata.
    pub targets: Vec<TargetSpec>,
    /// Mutation metadata.
    pub mutations: Vec<MutationSpec>,
    /// Evidence metadata.
    pub evidence: EvidenceSpec,
}

/// Canonical machine representation.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CanonicalMachine {
    /// Machine id.
    pub id: String,
    /// Optional description.
    pub description: Option<String>,
    /// Initial state id.
    pub initial_state: String,
    /// Semantic equivalence class.
    pub semantic_equivalence_class: Option<SemanticEquivalenceClass>,
    /// Canonical states sorted by id.
    pub states: Vec<CanonicalState>,
    /// Canonical fields sorted by id.
    pub fields: Vec<CanonicalField>,
    /// Canonical transitions sorted by id.
    pub transitions: Vec<CanonicalTransition>,
    /// Loop metadata sorted by id.
    pub loops: Vec<LoopSpec>,
    /// Canonical invariants sorted by id.
    pub invariants: Vec<CanonicalInvariant>,
    /// Observation declarations sorted by id.
    pub observations: Vec<ObserveSpec>,
    /// Witness policy.
    pub witness_policy: WitnessPolicy,
    /// Public input declarations sorted by id.
    pub public_inputs: Vec<PublicInputSpec>,
    /// Private witness declarations sorted by id.
    pub private_witnesses: Vec<PrivateWitnessSpec>,
}

/// Canonical state.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CanonicalState {
    /// State id.
    pub id: String,
    /// Optional description.
    pub description: Option<String>,
}

/// Canonical field.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CanonicalField {
    /// Field id.
    pub id: String,
    /// Field type.
    pub field_type: ValueType,
    /// Initial value.
    pub initial: Option<Value>,
    /// Visibility boundary.
    pub visibility: FieldVisibility,
}

/// Canonical transition.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CanonicalTransition {
    /// Transition id.
    pub id: String,
    /// Source state id.
    pub from: String,
    /// Target state id.
    pub to: String,
    /// Canonical guard.
    pub guard: CanonicalGuard,
    /// Canonical actions.
    pub actions: Vec<CanonicalAction>,
}

/// Canonical guard wrapper.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CanonicalGuard {
    /// Guard expression.
    pub guard: GuardSpec,
}

/// Canonical action wrapper.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CanonicalAction {
    /// Action expression.
    pub action: ActionSpec,
}

/// Canonical invariant.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CanonicalInvariant {
    /// Invariant id.
    pub id: String,
    /// Canonical invariant guard.
    pub guard: CanonicalGuard,
    /// Optional invariant scope.
    pub scope: Option<String>,
}

/// Canonical oracle declarations.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CanonicalOracle {
    /// Accepted traces.
    pub accepted_traces: Vec<TraceSpec>,
    /// Rejected traces.
    pub rejected_traces: Vec<TraceSpec>,
}

impl SemanticIr {
    /// Return a transition by id.
    pub fn transition(&self, id: &str) -> Option<&CanonicalTransition> {
        self.machine
            .transitions
            .iter()
            .find(|transition| transition.id == id)
    }

    /// Return a state by id.
    pub fn state(&self, id: &str) -> Option<&CanonicalState> {
        self.machine.states.iter().find(|state| state.id == id)
    }

    /// Return a field by id.
    pub fn field(&self, id: &str) -> Option<&CanonicalField> {
        self.machine.fields.iter().find(|field| field.id == id)
    }

    /// Build the machine's initial field map.
    pub fn initial_field_values(&self) -> Result<BTreeMap<String, Value>> {
        let mut values = BTreeMap::new();
        for field in &self.machine.fields {
            let value = field.initial.clone().ok_or_else(|| {
                ZkBenchError::oracle(
                    format!("machine.fields.{}", field.id),
                    "field has no initial value for local oracle evaluation",
                )
            })?;
            values.insert(field.id.clone(), value);
        }
        Ok(values)
    }
}

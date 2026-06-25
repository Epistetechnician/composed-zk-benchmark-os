//! Local generator family template registry.

use serde::{Deserialize, Serialize};

/// Family kinds known to the local generator.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum FamilyKind {
    /// Implemented v0 baseline FSM generator.
    BaselineFsm,
    /// Implemented v0 branching FSM generator.
    BranchingFsm,
    /// Implemented v0 bounded counter loop generator.
    BoundedCounterLoop,
    /// Implemented v0 nested loop generator.
    NestedLoop,
    /// Implemented v0 recursive envelope generator.
    RecursiveEnvelope,
    /// Implemented v0 memory-heavy state machine generator.
    MemoryHeavyStateMachine,
    /// Implemented v0 guard-heavy machine generator.
    GuardHeavyMachine,
    /// Implemented v0 public/private boundary stress generator.
    PublicPrivateBoundaryStress,
    /// Implemented v0 zkML/control-flow mixed generator.
    ZkMlControlFlowMixed,
}

impl FamilyKind {
    /// Whether the family kind has a local v0 implementation.
    pub fn is_implemented(self) -> bool {
        matches!(
            self,
            Self::BaselineFsm
                | Self::BranchingFsm
                | Self::BoundedCounterLoop
                | Self::NestedLoop
                | Self::GuardHeavyMachine
                | Self::RecursiveEnvelope
                | Self::MemoryHeavyStateMachine
                | Self::PublicPrivateBoundaryStress
                | Self::ZkMlControlFlowMixed
        )
    }

    /// Stable lowercase id segment.
    pub fn id_segment(self) -> &'static str {
        match self {
            Self::BaselineFsm => "baseline_fsm",
            Self::BranchingFsm => "branching_fsm",
            Self::BoundedCounterLoop => "bounded_counter_loop",
            Self::NestedLoop => "nested_loop",
            Self::RecursiveEnvelope => "recursive_envelope",
            Self::MemoryHeavyStateMachine => "memory_heavy_state_machine",
            Self::GuardHeavyMachine => "guard_heavy_machine",
            Self::PublicPrivateBoundaryStress => "public_private_boundary_stress",
            Self::ZkMlControlFlowMixed => "zkml_control_flow_mixed",
        }
    }
}

/// Family template metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FamilyTemplate {
    /// Family kind.
    pub kind: FamilyKind,
    /// Description.
    pub description: String,
    /// True when implemented in the local v0 generator.
    pub implemented: bool,
    /// Supported local oracle features.
    pub supported_oracle_features: Vec<String>,
    /// Unsupported or future features.
    pub unsupported_features: Vec<String>,
}

/// Return the template for a family kind.
pub fn family_template(kind: FamilyKind) -> FamilyTemplate {
    match kind {
        FamilyKind::BaselineFsm => FamilyTemplate {
            kind,
            description: "Generated linear FSM with positive and negative traces.".to_string(),
            implemented: true,
            supported_oracle_features: vec![
                "int_fields".to_string(),
                "guards".to_string(),
                "add_assign".to_string(),
            ],
            unsupported_features: vec![
                "backend_artifacts".to_string(),
                "formal_evidence".to_string(),
            ],
        },
        FamilyKind::BranchingFsm => FamilyTemplate {
            kind,
            description: "Generated guarded branching FSM with selected branch traces.".to_string(),
            implemented: true,
            supported_oracle_features: vec![
                "int_fields".to_string(),
                "bool_fields".to_string(),
                "branch_guards".to_string(),
            ],
            unsupported_features: vec![
                "nondeterministic_backend_choice".to_string(),
                "formal_evidence".to_string(),
            ],
        },
        FamilyKind::BoundedCounterLoop => FamilyTemplate {
            kind,
            description: "Generated bounded counter loop with invariant checks.".to_string(),
            implemented: true,
            supported_oracle_features: vec![
                "int_fields".to_string(),
                "lt_lte_eq_guards".to_string(),
                "add_assign".to_string(),
                "invariants".to_string(),
            ],
            unsupported_features: vec![
                "symbolic_unroll".to_string(),
                "backend_constraint_count".to_string(),
            ],
        },
        FamilyKind::NestedLoop => FamilyTemplate {
            kind,
            description:
                "Generated nested bounded loops with inner/outer counter dependency ordering."
                    .to_string(),
            implemented: true,
            supported_oracle_features: vec![
                "int_fields".to_string(),
                "nested_loop_bounds".to_string(),
                "add_assign".to_string(),
                "invariants".to_string(),
            ],
            unsupported_features: vec![
                "unbounded_nesting".to_string(),
                "backend_constraint_count".to_string(),
            ],
        },
        FamilyKind::GuardHeavyMachine => FamilyTemplate {
            kind,
            description:
                "Generated guarded machine exercising boolean and integer conjunction guards."
                    .to_string(),
            implemented: true,
            supported_oracle_features: vec![
                "int_fields".to_string(),
                "bool_fields".to_string(),
                "conjunction_guards".to_string(),
                "invariants".to_string(),
            ],
            unsupported_features: vec![
                "symbolic_unroll".to_string(),
                "formal_evidence".to_string(),
            ],
        },
        FamilyKind::RecursiveEnvelope => FamilyTemplate {
            kind,
            description: "Generated recursion-envelope bounded fold with digest metadata."
                .to_string(),
            implemented: true,
            supported_oracle_features: vec![
                "int_fields".to_string(),
                "loop_bounds".to_string(),
                "envelope_digest_metadata".to_string(),
                "invariants".to_string(),
            ],
            unsupported_features: vec![
                "live_gnark_recursion".to_string(),
                "backend_proof_size".to_string(),
            ],
        },
        FamilyKind::MemoryHeavyStateMachine => FamilyTemplate {
            kind,
            description: "Generated memory-heavy machine with multi-slot write/read ordering."
                .to_string(),
            implemented: true,
            supported_oracle_features: vec![
                "int_fields".to_string(),
                "bool_fields".to_string(),
                "memory_slots".to_string(),
                "invariants".to_string(),
            ],
            unsupported_features: vec![
                "backend_memory_usage".to_string(),
                "formal_evidence".to_string(),
            ],
        },
        FamilyKind::PublicPrivateBoundaryStress => FamilyTemplate {
            kind,
            description: "Generated public/private nonce binding with witness-policy metadata."
                .to_string(),
            implemented: true,
            supported_oracle_features: vec![
                "int_fields".to_string(),
                "bool_fields".to_string(),
                "witness_policy".to_string(),
                "public_inputs".to_string(),
            ],
            unsupported_features: vec![
                "zkml_execution".to_string(),
                "backend_boundary_checks".to_string(),
            ],
        },
        FamilyKind::ZkMlControlFlowMixed => FamilyTemplate {
            kind,
            description: "Generated confidence/threshold control-flow machine with observations."
                .to_string(),
            implemented: true,
            supported_oracle_features: vec![
                "int_fields".to_string(),
                "text_fields".to_string(),
                "observations".to_string(),
                "gte_guards".to_string(),
            ],
            unsupported_features: vec!["zkml_execution".to_string(), "model_accuracy".to_string()],
        },
    }
}

/// List all local family templates.
pub fn all_family_templates() -> Vec<FamilyTemplate> {
    [
        FamilyKind::BaselineFsm,
        FamilyKind::BranchingFsm,
        FamilyKind::BoundedCounterLoop,
        FamilyKind::NestedLoop,
        FamilyKind::RecursiveEnvelope,
        FamilyKind::MemoryHeavyStateMachine,
        FamilyKind::GuardHeavyMachine,
        FamilyKind::PublicPrivateBoundaryStress,
        FamilyKind::ZkMlControlFlowMixed,
    ]
    .into_iter()
    .map(family_template)
    .collect()
}

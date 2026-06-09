//! Mutation metadata, mutation verdict primitives, and local mutation engine.

pub mod apply;
pub mod bad_counters;
pub mod corrupted_guards;
pub mod missing_constraints;
pub mod pass;
pub mod provenance;

use serde::{Deserialize, Serialize};

use crate::evidence::{ArtifactDigest, ClaimBoundary, ExpectedVerdict};

pub use apply::{
    apply_default_mutations, apply_mutation_pass, evaluate_mutated_instance, MutationEngine,
};
pub use bad_counters::BadCountersPass;
pub use corrupted_guards::CorruptedGuardsPass;
pub use missing_constraints::MissingConstraintsPass;
pub use pass::{
    MutatedBenchmarkInstance, MutationApplication, MutationExpectedVerdict, MutationInput,
    MutationOutput, MutationPass, MutationPlan, MutationSafetyClass,
};
pub use provenance::MutationProvenance;

/// Required mutation class taxonomy.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum MutationClass {
    /// Remove a required invariant or transition constraint.
    #[serde(alias = "missing_constraints")]
    MissingConstraints,
    /// Change a guard predicate.
    #[serde(alias = "corrupted_guards")]
    CorruptedGuards,
    /// Skip, double, or corrupt a counter update.
    #[serde(alias = "bad_counters")]
    BadCounters,
    /// Read stale state after update.
    #[serde(alias = "stale_state_reads")]
    StaleStateReads,
    /// Exceed or corrupt loop unroll bounds.
    #[serde(alias = "invalid_unroll_bounds")]
    InvalidUnrollBounds,
    /// Add a transition outside the semantic relation.
    #[serde(alias = "nondeterministic_transition_injection")]
    NondeterministicTransitionInjection,
    /// Break recursion envelope binding.
    #[serde(alias = "recursion_envelope_mismatch")]
    RecursionEnvelopeMismatch,
    /// Violate public/private witness boundaries.
    #[serde(alias = "public_private_boundary_mismatch")]
    PublicPrivateBoundaryMismatch,
    /// Alias distinct witness slots incorrectly.
    #[serde(alias = "witness_aliasing")]
    WitnessAliasing,
    /// Weaken an invariant.
    #[serde(alias = "invariant_weakening")]
    InvariantWeakening,
    /// Strengthen an invariant beyond valid semantics.
    #[serde(alias = "invariant_strengthening")]
    InvariantStrengthening,
    /// Omit required observation data.
    #[serde(alias = "observation_omission")]
    ObservationOmission,
    /// Change semantic effect while appearing no-op-like.
    #[serde(alias = "semantic_no_op_drift")]
    SemanticNoOpDrift,
    /// Corrupt trace ordering.
    #[serde(alias = "trace_ordering_corruption")]
    TraceOrderingCorruption,
}

/// Mutation variant kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MutationKind {
    /// Semantics preserved.
    #[serde(alias = "valid")]
    Valid,
    /// Close to valid but violates a scoped boundary.
    #[serde(alias = "near_valid")]
    NearValid,
    /// Designed to expose unsound acceptance candidates.
    #[serde(alias = "malicious")]
    Malicious,
    /// Malformed or semantically impossible.
    #[serde(alias = "invalid")]
    Invalid,
}

/// Mutation severity.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MutationSeverity {
    /// Low severity.
    #[serde(alias = "low")]
    Low,
    /// Medium severity.
    #[serde(alias = "medium")]
    Medium,
    /// High severity.
    #[serde(alias = "high")]
    High,
    /// Critical severity.
    #[serde(alias = "critical")]
    Critical,
}

/// Surface mutation metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MutationSpec {
    /// Mutation id.
    pub id: String,
    /// Mutation class.
    pub class: MutationClass,
    /// Mutation kind.
    pub kind: MutationKind,
    /// Target field, transition, loop, invariant, or witness policy id.
    pub target: String,
    /// Expected semantic verdict.
    pub expected_verdict: ExpectedVerdict,
    /// Severity.
    pub severity: MutationSeverity,
    /// Oracle rationale.
    #[serde(default)]
    pub oracle_rationale: Option<String>,
}

/// Concrete mutation variant metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MutationVariant {
    /// Variant id.
    pub id: String,
    /// Source machine id.
    pub source_machine: String,
    /// Source benchmark instance id.
    pub benchmark_instance: String,
    /// Mutation class.
    pub mutation_class: MutationClass,
    /// Mutation kind.
    pub kind: MutationKind,
    /// Mutation target.
    pub target: String,
    /// Expected semantic verdict.
    pub expected_verdict: ExpectedVerdict,
    /// Oracle rationale.
    pub oracle_rationale: String,
    /// Deterministic seed if generation was used.
    #[serde(default)]
    pub seed: Option<u64>,
    /// Parent artifact digest when one exists.
    #[serde(default)]
    pub parent_artifact_digest: Option<ArtifactDigest>,
    /// Maximum claim boundary for the variant.
    pub claim_boundary_max: ClaimBoundary,
}

//! Mutation pass trait and output structures.

use serde::{Deserialize, Serialize};

use crate::dsl::{OracleOutcome, SemanticIr, SurfaceSpec, TraceSpec};
use crate::evidence::{ClaimBoundary, ExpectedVerdict};
use crate::generator::GeneratedBenchmarkInstance;

use super::provenance::MutationProvenance;
use super::MutationClass;

/// Mutation expected verdict alias for public API clarity.
pub type MutationExpectedVerdict = ExpectedVerdict;

/// Mutation safety class.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MutationSafetyClass {
    /// Semantics-preserving mutation.
    Valid,
    /// Near-valid mutation that violates a scoped boundary.
    NearValid,
    /// Malicious local semantic mutation.
    Malicious,
    /// Diagnostic mutation used to expose local behavior changes.
    Diagnostic,
}

/// Borrowed mutation input.
#[derive(Debug)]
pub struct MutationInput<'a> {
    /// Source generated Benchmark Instance.
    pub instance: &'a GeneratedBenchmarkInstance,
}

/// Mutation plan.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MutationPlan {
    /// Stable mutation id.
    pub mutation_id: String,
    /// Mutation class.
    pub mutation_class: MutationClass,
    /// Source instance id.
    pub source_instance_id: String,
    /// Target description.
    pub target_description: String,
}

/// Mutated generated Benchmark Instance.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MutatedBenchmarkInstance {
    /// Stable mutated instance id.
    pub id: String,
    /// Source instance id.
    pub source_instance_id: String,
    /// Mutation class.
    pub mutation_class: MutationClass,
    /// Expected verdict.
    pub expected_verdict: MutationExpectedVerdict,
    /// Safety class.
    pub safety_class: MutationSafetyClass,
    /// Mutation provenance.
    pub provenance: MutationProvenance,
    /// Mutated Surface DSL.
    pub surface_spec: SurfaceSpec,
    /// Mutated Semantic IR.
    pub semantic_ir: SemanticIr,
    /// Primary trace for mutation evaluation.
    pub primary_trace: TraceSpec,
    /// Local oracle outcomes when evaluated by helper functions.
    #[serde(default)]
    pub local_oracle_outcomes: Vec<OracleOutcome>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Mutation output alias.
pub type MutationOutput = MutatedBenchmarkInstance;

/// Mutation application result.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MutationApplication {
    /// Mutation plan.
    pub plan: MutationPlan,
    /// Mutated output.
    pub output: MutationOutput,
}

/// Local mutation pass.
pub trait MutationPass {
    /// Mutation class implemented by this pass.
    fn mutation_class(&self) -> MutationClass;

    /// Apply the mutation pass.
    fn apply(&self, input: &MutationInput<'_>) -> crate::error::Result<MutationApplication>;
}

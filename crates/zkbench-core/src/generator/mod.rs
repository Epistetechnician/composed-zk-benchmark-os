//! Benchmark Family, Benchmark Instance, and deterministic local generator
//! primitives.

pub mod config;
pub mod deterministic;
pub mod family;
pub mod instance;
pub mod templates;

use serde::{Deserialize, Serialize};

use crate::evidence::{ClaimBoundary, ExpectedVerdict};

pub use config::{
    GeneratorConfig, GeneratorLimits, GeneratorProfile, GeneratorSeed, GeneratorTunables,
};
pub use deterministic::{
    evaluate_generated_instance, generate_family, generate_instance, DeterministicGenerator,
};
pub use family::{GeneratedBenchmarkFamily, GenerationProvenance};
pub use instance::{GeneratedBenchmarkInstance, InstanceParams};
pub use templates::{FamilyKind, FamilyTemplate};

/// Benchmark Family metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BenchmarkFamily {
    /// Family id.
    pub id: String,
    /// Source machine id.
    pub source_machine: String,
    /// Optional semantic equivalence class id.
    #[serde(default)]
    pub semantic_equivalence_class: Option<String>,
    /// Instances in this family.
    #[serde(default)]
    pub instances: Vec<BenchmarkInstance>,
    /// Maximum claim boundary for this family.
    pub claim_boundary_max: ClaimBoundary,
}

/// Concrete Benchmark Instance metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BenchmarkInstance {
    /// Instance id.
    pub id: String,
    /// Family id.
    pub family_id: String,
    /// Machine id.
    pub machine_id: String,
    /// Trace ids included in the instance.
    #[serde(default)]
    pub trace_ids: Vec<String>,
    /// Optional mutation variant id.
    #[serde(default)]
    pub mutation_variant_id: Option<String>,
    /// Expected verdict for this instance.
    pub expected_verdict: ExpectedVerdict,
    /// Maximum claim boundary for this instance.
    pub claim_boundary_max: ClaimBoundary,
}

//! Generated Benchmark Family structures.

use serde::{Deserialize, Serialize};

use crate::dsl::{SemanticIr, SurfaceSpec};
use crate::evidence::ClaimBoundary;

use super::config::{GeneratorConfig, GeneratorSeed, GeneratorTunables};
use super::instance::{GeneratedBenchmarkInstance, InstanceParams};
use super::templates::FamilyKind;

/// Deterministic generation provenance.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GenerationProvenance {
    /// Generator version.
    pub generator_version: String,
    /// Seed.
    pub seed: GeneratorSeed,
    /// Logical deterministic generation marker, not wall-clock time.
    pub generated_at: String,
    /// Human-readable description.
    pub description: String,
}

/// Generated Benchmark Family with local Surface DSL and Semantic IR.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct GeneratedBenchmarkFamily {
    /// Stable family id.
    pub id: String,
    /// Family kind.
    pub family_kind: FamilyKind,
    /// Description.
    pub description: String,
    /// Generator config.
    pub config: GeneratorConfig,
    /// Generation provenance.
    pub provenance: GenerationProvenance,
    /// Generated Surface DSL.
    pub surface_spec: SurfaceSpec,
    /// Lowered Semantic IR.
    pub semantic_ir: SemanticIr,
    /// Default generated instances.
    pub instances: Vec<GeneratedBenchmarkInstance>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Supported local oracle features.
    pub supported_oracle_features: Vec<String>,
    /// Unsupported or future features.
    pub unsupported_features: Vec<String>,
    /// Conservative evidence notes.
    pub evidence_notes: Vec<String>,
}

impl GeneratedBenchmarkFamily {
    /// Instantiate a concrete Benchmark Instance from this generated family.
    pub fn instantiate(
        &self,
        params: InstanceParams,
    ) -> crate::error::Result<GeneratedBenchmarkInstance> {
        Ok(GeneratedBenchmarkInstance::from_family(self, params))
    }
}

pub(crate) fn family_id(
    kind: FamilyKind,
    seed: GeneratorSeed,
    tunables: &GeneratorTunables,
) -> String {
    format!(
        "{}_s{}_st{}_b{}_l{}",
        kind.id_segment(),
        seed.value,
        tunables.state_count,
        tunables.branching_factor,
        tunables.loop_bound
    )
}

//! Generated Benchmark Instance structures.

use serde::{Deserialize, Serialize};

use crate::dsl::{SemanticIr, SurfaceSpec, TraceSpec};
use crate::evidence::{ClaimBoundary, EvidenceRecord, ExpectedVerdict};

use super::config::GeneratorConfig;
use super::family::{GeneratedBenchmarkFamily, GenerationProvenance};
use super::templates::FamilyKind;

/// Instance parameters. V0 keeps these intentionally small.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct InstanceParams {
    /// Stable suffix for the instance id.
    pub id_suffix: String,
}

impl Default for InstanceParams {
    fn default() -> Self {
        Self {
            id_suffix: "default".to_string(),
        }
    }
}

/// Generated concrete Benchmark Instance.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct GeneratedBenchmarkInstance {
    /// Stable instance id.
    pub id: String,
    /// Source family id.
    pub family_id: String,
    /// Family kind.
    pub family_kind: FamilyKind,
    /// Generator config.
    pub config: GeneratorConfig,
    /// Generation provenance.
    pub generation_provenance: GenerationProvenance,
    /// Generated Surface DSL.
    pub surface_spec: SurfaceSpec,
    /// Lowered Semantic IR.
    pub semantic_ir: SemanticIr,
    /// Accepted traces copied from the oracle.
    pub accepted_traces: Vec<TraceSpec>,
    /// Rejected traces copied from the oracle.
    pub rejected_traces: Vec<TraceSpec>,
    /// Expected verdicts declared by traces.
    pub expected_verdicts: Vec<ExpectedVerdict>,
    /// Primary trace for focused local evaluation.
    pub primary_trace: TraceSpec,
    /// Optional local evidence records.
    #[serde(default)]
    pub local_evidence: Vec<EvidenceRecord>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

impl GeneratedBenchmarkInstance {
    pub(crate) fn from_family(family: &GeneratedBenchmarkFamily, params: InstanceParams) -> Self {
        let accepted_traces = family.semantic_ir.oracle.accepted_traces.clone();
        let rejected_traces = family.semantic_ir.oracle.rejected_traces.clone();
        let primary_trace = accepted_traces
            .first()
            .cloned()
            .or_else(|| rejected_traces.first().cloned())
            .unwrap_or_else(|| TraceSpec {
                id: "empty_trace".to_string(),
                initial_state: None,
                initial_fields: Default::default(),
                steps: Vec::new(),
                expected_final_state: None,
                expected_final_fields: Default::default(),
                expected_verdict: Some(ExpectedVerdict::Inconclusive),
                requires_capabilities: Vec::new(),
            });
        let expected_verdicts = accepted_traces
            .iter()
            .chain(rejected_traces.iter())
            .filter_map(|trace| trace.expected_verdict)
            .collect();
        Self {
            id: format!("{}_{}", family.id, params.id_suffix),
            family_id: family.id.clone(),
            family_kind: family.family_kind,
            config: family.config.clone(),
            generation_provenance: family.provenance.clone(),
            surface_spec: family.surface_spec.clone(),
            semantic_ir: family.semantic_ir.clone(),
            accepted_traces,
            rejected_traces,
            expected_verdicts,
            primary_trace,
            local_evidence: Vec::new(),
            claim_boundary: family.claim_boundary,
        }
    }
}

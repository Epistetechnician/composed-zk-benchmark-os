//! Planned zk-Harness metric mapping schema.
//!
//! Phase G records metric names only. It does not ingest or create metric
//! values.

use serde::{Deserialize, Serialize};

/// Planned metric kinds for future zk-Harness result import.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ZkHarnessMetricKind {
    /// Future prover time.
    ProverTime,
    /// Future verifier time.
    VerifierTime,
    /// Future proof size.
    ProofSize,
    /// Future memory usage.
    MemoryUsage,
    /// Future constraint count.
    ConstraintCount,
    /// Future setup time.
    SetupTime,
    /// Future witness generation time.
    WitnessGenerationTime,
}

/// Planned metric mapping. `observed_value` must remain absent in Phase G.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkHarnessMetricMapping {
    /// Metric kind.
    pub metric_kind: ZkHarnessMetricKind,
    /// Candidate future zk-Harness metric label.
    pub candidate_metric_label: String,
    /// True because Phase G is schema-only.
    pub planned_only: bool,
    /// Observed metric value. Must be `None` in Phase G.
    #[serde(default)]
    pub observed_value: Option<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Default planned metric mappings with no values.
pub fn default_zk_harness_metric_mappings() -> Vec<ZkHarnessMetricMapping> {
    [
        (ZkHarnessMetricKind::ProverTime, "prover_time"),
        (ZkHarnessMetricKind::VerifierTime, "verifier_time"),
        (ZkHarnessMetricKind::ProofSize, "proof_size"),
        (ZkHarnessMetricKind::MemoryUsage, "memory_usage"),
        (ZkHarnessMetricKind::ConstraintCount, "constraint_count"),
        (ZkHarnessMetricKind::SetupTime, "setup_time"),
        (
            ZkHarnessMetricKind::WitnessGenerationTime,
            "witness_generation_time",
        ),
    ]
    .into_iter()
    .map(
        |(metric_kind, candidate_metric_label)| ZkHarnessMetricMapping {
            metric_kind,
            candidate_metric_label: candidate_metric_label.to_string(),
            planned_only: true,
            observed_value: None,
            notes: vec!["Phase G metric mapping only; no metric value is present.".to_string()],
        },
    )
    .collect()
}

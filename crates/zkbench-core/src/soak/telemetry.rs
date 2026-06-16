//! Internal benchmark OS telemetry for local soak runs.

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::ClaimBoundary;

use super::shard::SoakShardId;

/// Telemetry report id.
pub type SoakTelemetryReportId = String;

/// Telemetry classification.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum SoakTelemetryClassification {
    /// Internal-only telemetry.
    InternalOnly,
    /// Local engineering metric.
    LocalEngineeringMetric,
    /// Not ZK backend performance.
    NotZkBackendPerformance,
    /// Not official benchmark evidence.
    NotOfficialBenchmarkEvidence,
}

/// Internal timing metric kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum InternalTimingMetricKind {
    /// Generation duration.
    Generation,
    /// Mutation duration.
    Mutation,
    /// Local oracle duration.
    LocalOracle,
    /// Local replay duration.
    LocalReplay,
    /// Pack write/read duration.
    PackWriteRead,
    /// Proposal preview duration.
    ProposalReviewPreview,
    /// Total local runner duration.
    SoakRunnerTotal,
}

/// Internal timing metric.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct InternalTimingMetric {
    /// Machine-stable metric name.
    pub metric_name: String,
    /// Metric kind.
    pub kind: InternalTimingMetricKind,
    /// Duration in milliseconds.
    pub duration_ms: u64,
    /// Classification.
    pub classification: Vec<SoakTelemetryClassification>,
}

/// Internal count metric.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct InternalCountMetric {
    /// Machine-stable metric name.
    pub metric_name: String,
    /// Count.
    pub count: usize,
    /// Classification.
    pub classification: Vec<SoakTelemetryClassification>,
}

/// Internal size metric.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct InternalSizeMetric {
    /// Machine-stable metric name.
    pub metric_name: String,
    /// Byte count.
    pub byte_count: usize,
    /// Classification.
    pub classification: Vec<SoakTelemetryClassification>,
}

/// Soak telemetry counters.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct SoakTelemetryCounters {
    /// Generated family count.
    pub generated_family_count: usize,
    /// Generated instance count.
    pub generated_instance_count: usize,
    /// Mutation variant count.
    pub mutation_variant_count: usize,
    /// Mutation pass no-target count.
    pub mutation_no_target_count: usize,
    /// Trace evaluations.
    pub traces_evaluated: usize,
    /// Local oracle accepted count.
    pub local_oracle_accepted_count: usize,
    /// Local oracle rejected count.
    pub local_oracle_rejected_count: usize,
    /// Local oracle capability gap count.
    pub local_oracle_capability_gap_count: usize,
    /// Local replay completed count.
    pub local_replay_completed_count: usize,
    /// Local replay failed count.
    pub local_replay_failed_count: usize,
    /// Pack write count.
    pub pack_write_count: usize,
    /// Pack read/validation count.
    pub pack_read_validation_count: usize,
    /// Evidence proposal count.
    pub evidence_proposal_count: usize,
    /// Append preview count.
    pub append_preview_count: usize,
    /// Quarantine count.
    pub quarantine_count: usize,
    /// Failure count.
    pub failure_count: usize,
    /// Failure count by phase.
    #[serde(default)]
    pub failure_count_by_phase: Vec<InternalCountMetric>,
    /// Bytes written by local artifact role.
    #[serde(default)]
    pub bytes_written_by_artifact_role: Vec<InternalSizeMetric>,
}

impl SoakTelemetryCounters {
    /// Merge counters.
    pub fn merge(&mut self, other: &Self) {
        self.generated_family_count = self
            .generated_family_count
            .saturating_add(other.generated_family_count);
        self.generated_instance_count = self
            .generated_instance_count
            .saturating_add(other.generated_instance_count);
        self.mutation_variant_count = self
            .mutation_variant_count
            .saturating_add(other.mutation_variant_count);
        self.mutation_no_target_count = self
            .mutation_no_target_count
            .saturating_add(other.mutation_no_target_count);
        self.traces_evaluated = self.traces_evaluated.saturating_add(other.traces_evaluated);
        self.local_oracle_accepted_count = self
            .local_oracle_accepted_count
            .saturating_add(other.local_oracle_accepted_count);
        self.local_oracle_rejected_count = self
            .local_oracle_rejected_count
            .saturating_add(other.local_oracle_rejected_count);
        self.local_oracle_capability_gap_count = self
            .local_oracle_capability_gap_count
            .saturating_add(other.local_oracle_capability_gap_count);
        self.local_replay_completed_count = self
            .local_replay_completed_count
            .saturating_add(other.local_replay_completed_count);
        self.local_replay_failed_count = self
            .local_replay_failed_count
            .saturating_add(other.local_replay_failed_count);
        self.pack_write_count = self.pack_write_count.saturating_add(other.pack_write_count);
        self.pack_read_validation_count = self
            .pack_read_validation_count
            .saturating_add(other.pack_read_validation_count);
        self.evidence_proposal_count = self
            .evidence_proposal_count
            .saturating_add(other.evidence_proposal_count);
        self.append_preview_count = self
            .append_preview_count
            .saturating_add(other.append_preview_count);
        self.quarantine_count = self.quarantine_count.saturating_add(other.quarantine_count);
        self.failure_count = self.failure_count.saturating_add(other.failure_count);
        self.failure_count_by_phase
            .extend(other.failure_count_by_phase.clone());
        self.bytes_written_by_artifact_role
            .extend(other.bytes_written_by_artifact_role.clone());
    }
}

/// Soak telemetry durations.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct SoakTelemetryDurations {
    /// Generation duration.
    pub generation_duration_ms: u64,
    /// Mutation duration.
    pub mutation_duration_ms: u64,
    /// Local oracle duration.
    pub local_oracle_duration_ms: u64,
    /// Local replay duration.
    pub local_replay_duration_ms: u64,
    /// Pack write/read duration.
    pub pack_write_duration_ms: u64,
    /// Proposal preview duration.
    pub proposal_preview_duration_ms: u64,
    /// Total local runner duration.
    pub soak_runner_total_duration_ms: u64,
    /// Detailed timing metrics.
    #[serde(default)]
    pub internal_timing_metrics: Vec<InternalTimingMetric>,
}

impl SoakTelemetryDurations {
    /// Record a timing metric and update aggregate fields.
    pub fn add_metric(&mut self, kind: InternalTimingMetricKind, duration_ms: u64) {
        let metric_name = match kind {
            InternalTimingMetricKind::Generation => {
                self.generation_duration_ms =
                    self.generation_duration_ms.saturating_add(duration_ms);
                "generation_duration_ms"
            }
            InternalTimingMetricKind::Mutation => {
                self.mutation_duration_ms = self.mutation_duration_ms.saturating_add(duration_ms);
                "mutation_duration_ms"
            }
            InternalTimingMetricKind::LocalOracle => {
                self.local_oracle_duration_ms =
                    self.local_oracle_duration_ms.saturating_add(duration_ms);
                "local_oracle_duration_ms"
            }
            InternalTimingMetricKind::LocalReplay => {
                self.local_replay_duration_ms =
                    self.local_replay_duration_ms.saturating_add(duration_ms);
                "local_replay_duration_ms"
            }
            InternalTimingMetricKind::PackWriteRead => {
                self.pack_write_duration_ms =
                    self.pack_write_duration_ms.saturating_add(duration_ms);
                "pack_write_duration_ms"
            }
            InternalTimingMetricKind::ProposalReviewPreview => {
                self.proposal_preview_duration_ms = self
                    .proposal_preview_duration_ms
                    .saturating_add(duration_ms);
                "proposal_preview_duration_ms"
            }
            InternalTimingMetricKind::SoakRunnerTotal => {
                self.soak_runner_total_duration_ms = self
                    .soak_runner_total_duration_ms
                    .saturating_add(duration_ms);
                "soak_runner_total_duration_ms"
            }
        };
        self.internal_timing_metrics.push(InternalTimingMetric {
            metric_name: metric_name.to_string(),
            kind,
            duration_ms,
            classification: default_classification(),
        });
    }
}

/// Telemetry snapshot.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakTelemetrySnapshot {
    /// Counters.
    pub counters: SoakTelemetryCounters,
    /// Durations.
    pub durations: SoakTelemetryDurations,
    /// Classification.
    pub classification: Vec<SoakTelemetryClassification>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

impl Default for SoakTelemetrySnapshot {
    fn default() -> Self {
        Self {
            counters: SoakTelemetryCounters::default(),
            durations: SoakTelemetryDurations::default(),
            classification: default_classification(),
            claim_boundary: ClaimBoundary::Level0DesignNote,
        }
    }
}

/// Telemetry report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakTelemetryReport {
    /// Report id.
    pub report_id: SoakTelemetryReportId,
    /// Report version.
    pub report_version: String,
    /// Source config id.
    pub source_config_id: String,
    /// Shard id.
    #[serde(default)]
    pub shard_id: Option<SoakShardId>,
    /// Snapshot.
    pub snapshot: SoakTelemetrySnapshot,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl SoakTelemetryReport {
    /// True when all telemetry classifications are internal-only.
    pub fn is_internal_only(&self) -> bool {
        self.snapshot
            .classification
            .contains(&SoakTelemetryClassification::InternalOnly)
            && self
                .snapshot
                .classification
                .contains(&SoakTelemetryClassification::NotZkBackendPerformance)
            && self
                .snapshot
                .classification
                .contains(&SoakTelemetryClassification::NotOfficialBenchmarkEvidence)
    }
}

/// Telemetry clock abstraction.
pub trait SoakTelemetryClock {
    /// Return monotonically increasing milliseconds for internal duration deltas.
    fn now_ms(&self) -> u64;
}

/// System clock for local telemetry.
#[derive(Debug, Clone)]
pub struct SystemTelemetryClock {
    start: std::time::Instant,
}

impl Default for SystemTelemetryClock {
    fn default() -> Self {
        Self {
            start: std::time::Instant::now(),
        }
    }
}

impl SoakTelemetryClock for SystemTelemetryClock {
    fn now_ms(&self) -> u64 {
        let millis = self.start.elapsed().as_millis();
        if millis > u128::from(u64::MAX) {
            u64::MAX
        } else {
            millis as u64
        }
    }
}

/// Deterministic test clock.
#[derive(Debug, Clone)]
pub struct MockTelemetryClock {
    current_ms: std::cell::Cell<u64>,
    step_ms: u64,
}

impl MockTelemetryClock {
    /// Build a mock clock with a fixed increment per observation.
    pub fn new(start_ms: u64, step_ms: u64) -> Self {
        Self {
            current_ms: std::cell::Cell::new(start_ms),
            step_ms,
        }
    }
}

impl Default for MockTelemetryClock {
    fn default() -> Self {
        Self::new(0, 5)
    }
}

impl SoakTelemetryClock for MockTelemetryClock {
    fn now_ms(&self) -> u64 {
        let current = self.current_ms.get();
        self.current_ms.set(current.saturating_add(self.step_ms));
        current
    }
}

/// Validate telemetry labels and claim boundary.
pub fn validate_soak_telemetry_report(report: &SoakTelemetryReport) -> Result<()> {
    if report.claim_boundary != ClaimBoundary::Level0DesignNote
        || report.snapshot.claim_boundary != ClaimBoundary::Level0DesignNote
    {
        return Err(ZkBenchError::soak(
            "soak.telemetry.claim_boundary",
            "telemetry reports must remain Level0DesignNote",
        ));
    }
    if !report.is_internal_only() {
        return Err(ZkBenchError::soak(
            "soak.telemetry.classification",
            "telemetry must be InternalOnly and NotZkBackendPerformance",
        ));
    }
    for metric in &report.snapshot.durations.internal_timing_metrics {
        reject_forbidden_metric_label(&metric.metric_name)?;
    }
    for metric in &report.snapshot.counters.failure_count_by_phase {
        reject_forbidden_metric_label(&metric.metric_name)?;
    }
    for metric in &report.snapshot.counters.bytes_written_by_artifact_role {
        reject_forbidden_metric_label(&metric.metric_name)?;
    }
    Ok(())
}

/// Reject forbidden ZK backend performance labels.
pub fn reject_forbidden_metric_label(label: &str) -> Result<()> {
    const FORBIDDEN: [&str; 5] = [
        "prover_time",
        "verifier_time",
        "proof_size",
        "zk_harness_time",
        "constraint_count",
    ];
    if FORBIDDEN.iter().any(|needle| label.contains(needle)) {
        return Err(ZkBenchError::soak(
            "soak.telemetry.metric_name",
            format!("forbidden metric label {label:?}"),
        ));
    }
    Ok(())
}

pub(crate) fn default_classification() -> Vec<SoakTelemetryClassification> {
    vec![
        SoakTelemetryClassification::InternalOnly,
        SoakTelemetryClassification::LocalEngineeringMetric,
        SoakTelemetryClassification::NotZkBackendPerformance,
        SoakTelemetryClassification::NotOfficialBenchmarkEvidence,
    ]
}

//! Internal benchmark OS telemetry for local soak runs.

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::ClaimBoundary;
use crate::formal::{FormalLanePipelineOutcome, FormalLaneProofStatus, FormalPropertyScopeKind};

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
    /// Observed distinguishability axis: true positive.
    #[serde(default)]
    pub distinguishability_true_positive_count: usize,
    /// Observed distinguishability axis: detected rejection.
    #[serde(default)]
    pub distinguishability_detected_rejection_count: usize,
    /// Observed distinguishability axis: unsound acceptance candidate.
    #[serde(default)]
    pub distinguishability_unsound_acceptance_candidate_count: usize,
    /// Observed distinguishability axis: false rejection candidate.
    #[serde(default)]
    pub distinguishability_false_rejection_candidate_count: usize,
    /// Observed distinguishability axis: inconclusive.
    #[serde(default)]
    pub distinguishability_inconclusive_count: usize,
    /// Formal property templates derived from mutation × surface cross-product.
    #[serde(default)]
    pub formal_lane_template_derived_count: usize,
    /// Formal lane evaluations attempted.
    #[serde(default)]
    pub formal_lane_evaluation_count: usize,
    /// Formal lane outcomes at `DeclaredOnly`.
    #[serde(default)]
    pub formal_lane_declared_only_count: usize,
    /// Formal lane passes where no assertion template could be derived.
    #[serde(default)]
    pub formal_lane_no_template_count: usize,
    /// Formal lane pipeline count by primary formal scope kind.
    #[serde(default)]
    pub formal_lane_count_by_scope: Vec<InternalCountMetric>,
    /// Formal lane pipeline count by proof status.
    #[serde(default)]
    pub formal_lane_count_by_status: Vec<InternalCountMetric>,
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
        self.distinguishability_true_positive_count = self
            .distinguishability_true_positive_count
            .saturating_add(other.distinguishability_true_positive_count);
        self.distinguishability_detected_rejection_count = self
            .distinguishability_detected_rejection_count
            .saturating_add(other.distinguishability_detected_rejection_count);
        self.distinguishability_unsound_acceptance_candidate_count = self
            .distinguishability_unsound_acceptance_candidate_count
            .saturating_add(other.distinguishability_unsound_acceptance_candidate_count);
        self.distinguishability_false_rejection_candidate_count = self
            .distinguishability_false_rejection_candidate_count
            .saturating_add(other.distinguishability_false_rejection_candidate_count);
        self.distinguishability_inconclusive_count = self
            .distinguishability_inconclusive_count
            .saturating_add(other.distinguishability_inconclusive_count);
        self.formal_lane_template_derived_count = self
            .formal_lane_template_derived_count
            .saturating_add(other.formal_lane_template_derived_count);
        self.formal_lane_evaluation_count = self
            .formal_lane_evaluation_count
            .saturating_add(other.formal_lane_evaluation_count);
        self.formal_lane_declared_only_count = self
            .formal_lane_declared_only_count
            .saturating_add(other.formal_lane_declared_only_count);
        self.formal_lane_no_template_count = self
            .formal_lane_no_template_count
            .saturating_add(other.formal_lane_no_template_count);
        self.formal_lane_count_by_scope
            .extend(other.formal_lane_count_by_scope.clone());
        self.formal_lane_count_by_status
            .extend(other.formal_lane_count_by_status.clone());
    }

    /// Record one observed mutation distinguishability axis from local replay.
    pub fn record_distinguishability_axis(
        &mut self,
        axis: crate::scoring::MutationDistinguishabilityAxis,
    ) {
        use crate::scoring::MutationDistinguishabilityAxis;
        match axis {
            MutationDistinguishabilityAxis::TruePositive => {
                self.distinguishability_true_positive_count = self
                    .distinguishability_true_positive_count
                    .saturating_add(1);
            }
            MutationDistinguishabilityAxis::DetectedRejection => {
                self.distinguishability_detected_rejection_count = self
                    .distinguishability_detected_rejection_count
                    .saturating_add(1);
            }
            MutationDistinguishabilityAxis::UnsoundAcceptanceCandidate => {
                self.distinguishability_unsound_acceptance_candidate_count = self
                    .distinguishability_unsound_acceptance_candidate_count
                    .saturating_add(1);
            }
            MutationDistinguishabilityAxis::FalseRejectionCandidate => {
                self.distinguishability_false_rejection_candidate_count = self
                    .distinguishability_false_rejection_candidate_count
                    .saturating_add(1);
            }
            MutationDistinguishabilityAxis::Inconclusive => {
                self.distinguishability_inconclusive_count =
                    self.distinguishability_inconclusive_count.saturating_add(1);
            }
        }
    }

    /// Record one formal-lane pipeline outcome.
    pub fn record_formal_lane_pipeline(&mut self, template_derived: bool, declared_only: bool) {
        if template_derived {
            self.formal_lane_template_derived_count =
                self.formal_lane_template_derived_count.saturating_add(1);
            self.formal_lane_evaluation_count = self.formal_lane_evaluation_count.saturating_add(1);
        } else {
            self.formal_lane_no_template_count =
                self.formal_lane_no_template_count.saturating_add(1);
        }
        if declared_only {
            self.formal_lane_declared_only_count =
                self.formal_lane_declared_only_count.saturating_add(1);
        }
    }

    /// Record one formal-lane pipeline outcome with scope and status detail.
    pub fn record_formal_lane_pipeline_outcome(&mut self, outcome: &FormalLanePipelineOutcome) {
        self.record_formal_lane_pipeline(
            outcome.template_derived,
            outcome.proof_status == Some(FormalLaneProofStatus::DeclaredOnly),
        );
        increment_count_metric(
            &mut self.formal_lane_count_by_scope,
            formal_scope_metric_name(outcome.primary_formal_scope),
        );
        if let Some(status) = outcome.proof_status {
            increment_count_metric(
                &mut self.formal_lane_count_by_status,
                formal_status_metric_name(status),
            );
        }
    }
}

fn increment_count_metric(metrics: &mut Vec<InternalCountMetric>, metric_name: &'static str) {
    if let Some(metric) = metrics
        .iter_mut()
        .find(|metric| metric.metric_name == metric_name)
    {
        metric.count = metric.count.saturating_add(1);
        return;
    }
    metrics.push(InternalCountMetric {
        metric_name: metric_name.to_string(),
        count: 1,
        classification: default_classification(),
    });
}

fn formal_scope_metric_name(scope: FormalPropertyScopeKind) -> &'static str {
    match scope {
        FormalPropertyScopeKind::TransitionGuard => "formal_lane_scope_transition_guard_count",
        FormalPropertyScopeKind::Invariant => "formal_lane_scope_invariant_count",
        FormalPropertyScopeKind::LoopBound => "formal_lane_scope_loop_bound_count",
        FormalPropertyScopeKind::Machine => "formal_lane_scope_machine_count",
        FormalPropertyScopeKind::NotApplicable => "formal_lane_scope_not_applicable_count",
    }
}

fn formal_status_metric_name(status: FormalLaneProofStatus) -> &'static str {
    match status {
        FormalLaneProofStatus::DeclaredOnly => "formal_lane_status_declared_only_count",
        FormalLaneProofStatus::ProofAttempted => "formal_lane_status_proof_attempted_count",
        FormalLaneProofStatus::MachineCheckedScoped => {
            "formal_lane_status_machine_checked_scoped_count"
        }
        FormalLaneProofStatus::IndependentlyReproduced => {
            "formal_lane_status_independently_reproduced_count"
        }
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
    validate_telemetry_identity(report)?;
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
    validate_telemetry_counter_relationships(&report.snapshot.counters)?;
    for metric in &report.snapshot.durations.internal_timing_metrics {
        reject_forbidden_metric_label(&metric.metric_name)?;
        validate_telemetry_classification(
            "soak.telemetry.durations.internal_timing_metrics.classification",
            &metric.classification,
        )?;
    }
    for metric in &report.snapshot.counters.failure_count_by_phase {
        reject_forbidden_metric_label(&metric.metric_name)?;
        validate_telemetry_classification(
            "soak.telemetry.counters.failure_count_by_phase.classification",
            &metric.classification,
        )?;
    }
    for metric in &report.snapshot.counters.bytes_written_by_artifact_role {
        reject_forbidden_metric_label(&metric.metric_name)?;
        validate_telemetry_classification(
            "soak.telemetry.counters.bytes_written_by_artifact_role.classification",
            &metric.classification,
        )?;
    }
    for metric in &report.snapshot.counters.formal_lane_count_by_scope {
        reject_forbidden_metric_label(&metric.metric_name)?;
        validate_telemetry_classification(
            "soak.telemetry.counters.formal_lane_count_by_scope.classification",
            &metric.classification,
        )?;
    }
    for metric in &report.snapshot.counters.formal_lane_count_by_status {
        reject_forbidden_metric_label(&metric.metric_name)?;
        validate_telemetry_classification(
            "soak.telemetry.counters.formal_lane_count_by_status.classification",
            &metric.classification,
        )?;
    }
    Ok(())
}

fn validate_telemetry_identity(report: &SoakTelemetryReport) -> Result<()> {
    if report.report_id.trim().is_empty() {
        return Err(ZkBenchError::soak(
            "soak.telemetry.report_id",
            "telemetry report id is empty",
        ));
    }
    if report.report_version.trim().is_empty() {
        return Err(ZkBenchError::soak(
            "soak.telemetry.report_version",
            "telemetry report version is empty",
        ));
    }
    if report.source_config_id.trim().is_empty() {
        return Err(ZkBenchError::soak(
            "soak.telemetry.source_config_id",
            "telemetry report source config id is empty",
        ));
    }
    match &report.shard_id {
        Some(shard_id) if !shard_id.value.trim().is_empty() => Ok(()),
        Some(_) => Err(ZkBenchError::soak(
            "soak.telemetry.shard_id",
            "telemetry report shard id is empty",
        )),
        None => Err(ZkBenchError::soak(
            "soak.telemetry.shard_id",
            "telemetry report must be shard-scoped",
        )),
    }
}

fn validate_telemetry_counter_relationships(counters: &SoakTelemetryCounters) -> Result<()> {
    let oracle_total = counters
        .local_oracle_accepted_count
        .saturating_add(counters.local_oracle_rejected_count)
        .saturating_add(counters.local_oracle_capability_gap_count);
    if oracle_total > counters.traces_evaluated {
        return Err(ZkBenchError::soak(
            "soak.telemetry.counters.local_oracle",
            "local oracle outcome counts exceed traces_evaluated",
        ));
    }
    let replay_total = counters
        .local_replay_completed_count
        .saturating_add(counters.local_replay_failed_count);
    let replay_inputs = counters
        .generated_instance_count
        .saturating_add(counters.mutation_variant_count);
    if replay_total > replay_inputs {
        return Err(ZkBenchError::soak(
            "soak.telemetry.counters.local_replay",
            "local replay attempts exceed generated instances plus mutation variants",
        ));
    }
    if counters.formal_lane_evaluation_count > counters.formal_lane_template_derived_count {
        return Err(ZkBenchError::soak(
            "soak.telemetry.counters.formal_lane_evaluation",
            "formal lane evaluations exceed derived templates",
        ));
    }
    if counters.formal_lane_declared_only_count > counters.formal_lane_evaluation_count {
        return Err(ZkBenchError::soak(
            "soak.telemetry.counters.formal_lane_declared_only",
            "declared-only formal lane outcomes exceed evaluations",
        ));
    }
    Ok(())
}

fn validate_telemetry_classification(
    field: impl Into<String>,
    classification: &[SoakTelemetryClassification],
) -> Result<()> {
    if classification.contains(&SoakTelemetryClassification::InternalOnly)
        && classification.contains(&SoakTelemetryClassification::NotZkBackendPerformance)
        && classification.contains(&SoakTelemetryClassification::NotOfficialBenchmarkEvidence)
    {
        return Ok(());
    }
    Err(ZkBenchError::soak(
        field,
        "telemetry metric classification must be InternalOnly, NotZkBackendPerformance, and NotOfficialBenchmarkEvidence",
    ))
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

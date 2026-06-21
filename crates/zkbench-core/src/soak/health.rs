//! Local health reports for soak runs.

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::ClaimBoundary;

use super::failure_corpus::FailureCorpusIndex;
use super::shard::{SoakShardId, SoakShardStatus, SoakShardSummary};
use super::telemetry::{
    reject_forbidden_metric_label, validate_soak_telemetry_report, SoakTelemetryCounters,
    SoakTelemetryReport,
};

/// Health report id.
pub type SoakHealthReportId = String;

/// Soak health status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum SoakHealthStatus {
    /// Healthy.
    Healthy,
    /// Healthy with warnings.
    HealthyWithWarnings,
    /// Degraded.
    Degraded,
    /// Failed.
    Failed,
    /// Inconclusive.
    Inconclusive,
}

/// Finding severity.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum SoakHealthFindingSeverity {
    /// Informational.
    Info,
    /// Warning.
    Warning,
    /// Error.
    Error,
    /// Blocking.
    Blocking,
}

/// Health finding.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakHealthFinding {
    /// Finding id.
    pub id: String,
    /// Severity.
    pub severity: SoakHealthFindingSeverity,
    /// Message.
    pub message: String,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Health recommendation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakHealthRecommendation {
    /// Recommendation id.
    pub id: String,
    /// Message.
    pub message: String,
}

/// Regression signal.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakRegressionSignal {
    /// Signal id.
    pub id: String,
    /// True when the signal is active.
    pub active: bool,
    /// Message.
    pub message: String,
}

/// Health summary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct SoakHealthSummary {
    /// Generated instances.
    pub generated_instances: usize,
    /// Mutation variants.
    pub mutation_variants: usize,
    /// Local replays.
    pub local_replays: usize,
    /// Failures.
    pub failures: usize,
    /// Failure corpus entries.
    pub failure_corpus_entries: usize,
}

/// Local health report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakHealthReport {
    /// Report id.
    pub report_id: SoakHealthReportId,
    /// Report version.
    pub report_version: String,
    /// Source config id.
    pub source_config_id: String,
    /// Shard id or aggregate id.
    #[serde(default)]
    pub shard_id: Option<SoakShardId>,
    /// Aggregate id.
    #[serde(default)]
    pub aggregate_id: Option<String>,
    /// Health status.
    pub health_status: SoakHealthStatus,
    /// Summary.
    pub summary: SoakHealthSummary,
    /// Telemetry summary.
    pub telemetry_summary: SoakTelemetryCounters,
    /// Failure summary.
    pub failure_summary: String,
    /// Claim-boundary summary.
    pub claim_boundary_summary: String,
    /// Reproducibility summary.
    pub reproducibility_summary: String,
    /// Determinism summary.
    pub determinism_summary: String,
    /// Output artifact summary.
    pub output_artifact_summary: String,
    /// Findings.
    #[serde(default)]
    pub findings: Vec<SoakHealthFinding>,
    /// Regression signals.
    #[serde(default)]
    pub regression_signals: Vec<SoakRegressionSignal>,
    /// Recommendations.
    #[serde(default)]
    pub recommendations: Vec<SoakHealthRecommendation>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl SoakHealthReport {
    /// Build from a shard summary, telemetry report, and failure corpus.
    pub fn from_shard(
        source_config_id: String,
        shard_summary: &SoakShardSummary,
        telemetry: &SoakTelemetryReport,
        failure_corpus: &FailureCorpusIndex,
    ) -> Self {
        let mut findings = default_claim_boundary_findings();
        let mut status = match shard_summary.status {
            SoakShardStatus::Completed => SoakHealthStatus::Healthy,
            SoakShardStatus::CompletedWithFailures => SoakHealthStatus::HealthyWithWarnings,
            SoakShardStatus::Failed => SoakHealthStatus::Failed,
            SoakShardStatus::Planned | SoakShardStatus::Running | SoakShardStatus::Resumable => {
                SoakHealthStatus::Inconclusive
            }
        };
        if failure_corpus.summary.entry_count > 0 && status == SoakHealthStatus::Healthy {
            status = SoakHealthStatus::HealthyWithWarnings;
        }
        if telemetry.snapshot.counters.failure_count > 0 {
            findings.push(SoakHealthFinding {
                id: "local_failure_count_nonzero".to_string(),
                severity: SoakHealthFindingSeverity::Warning,
                message: "local failure corpus contains entries".to_string(),
                claim_boundary: ClaimBoundary::Level0DesignNote,
            });
        }
        Self {
            report_id: format!("health_report_{}", shard_summary.shard_id.value),
            report_version: "phase-k-local-health-report-v0".to_string(),
            source_config_id,
            shard_id: Some(shard_summary.shard_id.clone()),
            aggregate_id: None,
            health_status: status,
            summary: SoakHealthSummary {
                generated_instances: telemetry.snapshot.counters.generated_instance_count,
                mutation_variants: telemetry.snapshot.counters.mutation_variant_count,
                local_replays: telemetry.snapshot.counters.local_replay_completed_count,
                failures: telemetry.snapshot.counters.failure_count,
                failure_corpus_entries: failure_corpus.summary.entry_count,
            },
            telemetry_summary: telemetry.snapshot.counters.clone(),
            failure_summary: format!("failure_corpus_entries={}", failure_corpus.summary.entry_count),
            claim_boundary_summary:
                "soak report is Level0DesignNote; local replay artifacts are Level1LocalReplay at most"
                    .to_string(),
            reproducibility_summary:
                "deterministic config digest, shard manifest, and checkpoint are recorded"
                    .to_string(),
            determinism_summary:
                "shard assignment uses stable case ordering and contains no wall-clock ids"
                    .to_string(),
            output_artifact_summary:
                "soak artifact refs are relative and local-only".to_string(),
            findings,
            regression_signals: vec![SoakRegressionSignal {
                id: "failure_corpus_growth".to_string(),
                active: failure_corpus.summary.entry_count > 0,
                message: "failure corpus growth is a local regression signal only".to_string(),
            }],
            recommendations: vec![SoakHealthRecommendation {
                id: "phase_l_local_soak".to_string(),
                message:
                    "Phase L should run longer local soak jobs only with explicit user approval"
                        .to_string(),
            }],
            claim_boundary: ClaimBoundary::Level0DesignNote,
            notes: default_health_notes(),
        }
    }
}

/// Validate a health report.
pub fn validate_soak_health_report(report: &SoakHealthReport) -> Result<()> {
    if report.claim_boundary != ClaimBoundary::Level0DesignNote {
        return Err(ZkBenchError::soak(
            "soak.health.claim_boundary",
            "soak health reports must remain Level0DesignNote",
        ));
    }
    validate_health_identity(report)?;
    validate_health_summary(report)?;
    for (index, finding) in report.findings.iter().enumerate() {
        if finding.id.trim().is_empty() {
            return Err(ZkBenchError::soak(
                format!("soak.health.findings[{index}].id"),
                "health finding id is empty",
            ));
        }
        if finding.claim_boundary != ClaimBoundary::Level0DesignNote {
            return Err(ZkBenchError::soak(
                "soak.health.findings.claim_boundary",
                "health findings must remain Level0DesignNote",
            ));
        }
        reject_forbidden_metric_label(&finding.id)?;
    }
    for note in &report.notes {
        if note.contains("ZK backend performance") && !note.contains("not ZK backend performance") {
            return Err(ZkBenchError::soak(
                "soak.health.notes",
                "health report must not imply ZK backend performance",
            ));
        }
    }
    for (index, signal) in report.regression_signals.iter().enumerate() {
        if signal.id.trim().is_empty() {
            return Err(ZkBenchError::soak(
                format!("soak.health.regression_signals[{index}].id"),
                "health regression signal id is empty",
            ));
        }
    }
    for (index, recommendation) in report.recommendations.iter().enumerate() {
        if recommendation.id.trim().is_empty() {
            return Err(ZkBenchError::soak(
                format!("soak.health.recommendations[{index}].id"),
                "health recommendation id is empty",
            ));
        }
    }
    Ok(())
}

fn validate_health_identity(report: &SoakHealthReport) -> Result<()> {
    if report.report_id.trim().is_empty() {
        return Err(ZkBenchError::soak(
            "soak.health.report_id",
            "health report id is empty",
        ));
    }
    if report.report_version.trim().is_empty() {
        return Err(ZkBenchError::soak(
            "soak.health.report_version",
            "health report version is empty",
        ));
    }
    if report.source_config_id.trim().is_empty() {
        return Err(ZkBenchError::soak(
            "soak.health.source_config_id",
            "health report source config id is empty",
        ));
    }
    match (&report.shard_id, &report.aggregate_id) {
        (Some(_), Some(_)) => {
            return Err(ZkBenchError::soak(
                "soak.health.identity",
                "health report cannot be both shard-scoped and aggregate-scoped",
            ));
        }
        (None, None) => {
            return Err(ZkBenchError::soak(
                "soak.health.identity",
                "health report must be either shard-scoped or aggregate-scoped",
            ));
        }
        (Some(shard_id), None) => {
            if shard_id.value.trim().is_empty() {
                return Err(ZkBenchError::soak(
                    "soak.health.shard_id",
                    "health report shard id is empty",
                ));
            }
        }
        (None, Some(aggregate_id)) => {
            if aggregate_id.trim().is_empty() {
                return Err(ZkBenchError::soak(
                    "soak.health.aggregate_id",
                    "health report aggregate id is empty",
                ));
            }
        }
    }
    Ok(())
}

fn validate_health_summary(report: &SoakHealthReport) -> Result<()> {
    if report.summary.generated_instances != report.telemetry_summary.generated_instance_count {
        return Err(ZkBenchError::soak(
            "soak.health.summary.generated_instances",
            "health summary generated_instances does not match telemetry",
        ));
    }
    if report.summary.mutation_variants != report.telemetry_summary.mutation_variant_count {
        return Err(ZkBenchError::soak(
            "soak.health.summary.mutation_variants",
            "health summary mutation_variants does not match telemetry",
        ));
    }
    if report.summary.local_replays != report.telemetry_summary.local_replay_completed_count {
        return Err(ZkBenchError::soak(
            "soak.health.summary.local_replays",
            "health summary local_replays does not match telemetry",
        ));
    }
    if report.summary.failures != report.telemetry_summary.failure_count {
        return Err(ZkBenchError::soak(
            "soak.health.summary.failures",
            "health summary failures does not match telemetry",
        ));
    }
    if report.summary.failure_corpus_entries > 0
        && report.health_status == SoakHealthStatus::Healthy
    {
        return Err(ZkBenchError::soak(
            "soak.health.status",
            "healthy status cannot report failure corpus entries",
        ));
    }
    Ok(())
}

/// Build an aggregate report from shard health reports.
pub fn aggregate_soak_health_reports(
    source_config_id: impl Into<String>,
    reports: &[SoakHealthReport],
) -> Result<SoakHealthReport> {
    let source_config_id = source_config_id.into();
    let mut counters = SoakTelemetryCounters::default();
    let mut failure_entries = 0usize;
    let mut findings = default_claim_boundary_findings();
    let mut status = SoakHealthStatus::Healthy;
    for report in reports {
        validate_soak_health_report(report)?;
        counters.merge(&report.telemetry_summary);
        failure_entries = failure_entries.saturating_add(report.summary.failure_corpus_entries);
        findings.extend(report.findings.clone());
        status = merge_status(status, report.health_status);
    }
    if failure_entries > 0 && status == SoakHealthStatus::Healthy {
        status = SoakHealthStatus::HealthyWithWarnings;
    }
    Ok(SoakHealthReport {
        report_id: format!("aggregate_health_report_{source_config_id}"),
        report_version: "phase-k-local-health-report-v0".to_string(),
        source_config_id,
        shard_id: None,
        aggregate_id: Some("aggregate".to_string()),
        health_status: status,
        summary: SoakHealthSummary {
            generated_instances: counters.generated_instance_count,
            mutation_variants: counters.mutation_variant_count,
            local_replays: counters.local_replay_completed_count,
            failures: counters.failure_count,
            failure_corpus_entries: failure_entries,
        },
        telemetry_summary: counters,
        failure_summary: format!("aggregate_failure_corpus_entries={failure_entries}"),
        claim_boundary_summary:
            "aggregate health report is Level0DesignNote and creates no Level2 evidence".to_string(),
        reproducibility_summary: "aggregate over deterministic shard reports".to_string(),
        determinism_summary: "aggregate preserves deterministic shard ids".to_string(),
        output_artifact_summary: "aggregate report is local-only".to_string(),
        findings,
        regression_signals: vec![SoakRegressionSignal {
            id: "aggregate_failure_corpus_growth".to_string(),
            active: failure_entries > 0,
            message: "aggregate failure corpus growth is local pipeline telemetry only".to_string(),
        }],
        recommendations: vec![SoakHealthRecommendation {
            id: "phase_l_sampled_local_reports".to_string(),
            message: "curate sampled local reports before any future external execution phase"
                .to_string(),
        }],
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: default_health_notes(),
    })
}

/// Validate telemetry and produce report-level findings for selected hazards.
pub fn health_findings_from_telemetry(telemetry: &SoakTelemetryReport) -> Vec<SoakHealthFinding> {
    let mut findings = Vec::new();
    if let Err(error) = validate_soak_telemetry_report(telemetry) {
        findings.push(SoakHealthFinding {
            id: "telemetry_validation_failure".to_string(),
            severity: SoakHealthFindingSeverity::Error,
            message: error.to_string(),
            claim_boundary: ClaimBoundary::Level0DesignNote,
        });
    }
    if telemetry.snapshot.counters.local_replay_failed_count > 0 {
        findings.push(SoakHealthFinding {
            id: "local_replay_failure".to_string(),
            severity: SoakHealthFindingSeverity::Warning,
            message: "one or more local replay attempts failed".to_string(),
            claim_boundary: ClaimBoundary::Level0DesignNote,
        });
    }
    findings
}

fn merge_status(left: SoakHealthStatus, right: SoakHealthStatus) -> SoakHealthStatus {
    use SoakHealthStatus::{Degraded, Failed, Healthy, HealthyWithWarnings, Inconclusive};
    match (left, right) {
        (Failed, _) | (_, Failed) => Failed,
        (Degraded, _) | (_, Degraded) => Degraded,
        (Inconclusive, _) | (_, Inconclusive) => Inconclusive,
        (HealthyWithWarnings, _) | (_, HealthyWithWarnings) => HealthyWithWarnings,
        (Healthy, Healthy) => Healthy,
    }
}

fn default_claim_boundary_findings() -> Vec<SoakHealthFinding> {
    vec![
        SoakHealthFinding {
            id: "local_soak_telemetry_not_official".to_string(),
            severity: SoakHealthFindingSeverity::Info,
            message: "Local soak telemetry is not official benchmark evidence.".to_string(),
            claim_boundary: ClaimBoundary::Level0DesignNote,
        },
        SoakHealthFinding {
            id: "internal_timing_not_zk_backend_performance".to_string(),
            severity: SoakHealthFindingSeverity::Info,
            message: "Internal timing telemetry is not ZK backend performance.".to_string(),
            claim_boundary: ClaimBoundary::Level0DesignNote,
        },
        SoakHealthFinding {
            id: "no_external_backend_invoked".to_string(),
            severity: SoakHealthFindingSeverity::Info,
            message: "No external backend was invoked.".to_string(),
            claim_boundary: ClaimBoundary::Level0DesignNote,
        },
    ]
}

fn default_health_notes() -> Vec<String> {
    vec![
        "Local soak telemetry is not official benchmark evidence.".to_string(),
        "Internal timing telemetry is not ZK backend performance.".to_string(),
        "Failure corpus entries are reproduction aids, not accepted evidence.".to_string(),
        "No external backend was invoked.".to_string(),
    ]
}

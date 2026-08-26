//! Phase K local soak runner and internal benchmark OS telemetry.
//!
//! Phase K artifacts are local health and reproducibility artifacts only.
//! Local soak telemetry is not official benchmark evidence. Internal timing
//! telemetry is not ZK backend performance.

pub mod artifact_layout;
pub mod campaign;
pub mod clock;
pub mod config;
pub mod failure_corpus;
pub mod health;
pub mod report;
pub mod reproduction;
pub mod resume;
pub mod runner;
pub mod serialization;
pub mod shard;
pub mod telemetry;
pub mod validation;

pub use artifact_layout::{
    read_soak_report_bundle, soak_artifact_manifest, validate_soak_report_bundle,
    write_soak_report_bundle, SoakArtifactDigestSet, SoakArtifactLayout, SoakArtifactManifest,
    SoakArtifactRole, SoakReportBundle, SoakReportBundleValidation,
};
pub use campaign::{
    run_soak_campaign, run_soak_campaign_with_local_json_adapter, validate_soak_campaign_config,
    SoakCampaignApproval, SoakCampaignArtifactRootPolicy, SoakCampaignConfig, SoakCampaignResult,
    SoakCampaignShardOutcome,
};
pub use clock::{MockTelemetryClock, SoakTelemetryClock, SystemTelemetryClock};
pub use config::{
    build_regression_soak_config, build_smoke_soak_config, validate_soak_run_config,
    SoakClaimBoundaryPolicy, SoakFamilySelection, SoakLimits, SoakMutationSelection,
    SoakOutputPolicy, SoakRunConfig, SoakRunConfigId, SoakRunConfigVersion, SoakRunProfile,
    SoakRunScope, SoakSeedRange, SoakShardConfig, SoakTelemetryPolicy,
};
pub use failure_corpus::{
    build_failure_corpus_entry, validate_failure_corpus_index, FailureArtifactRef, FailureCorpus,
    FailureCorpusEntry, FailureCorpusEntryId, FailureCorpusEntryInput, FailureCorpusIndex,
    FailureCorpusKind, FailureCorpusSummary, FailureMinimizationHint, FailureReproductionManifest,
    FailureTriageStatus,
};
pub use health::{
    aggregate_soak_health_reports, health_findings_from_telemetry, validate_soak_health_report,
    SoakHealthFinding, SoakHealthFindingSeverity, SoakHealthRecommendation, SoakHealthReport,
    SoakHealthReportId, SoakHealthStatus, SoakHealthSummary, SoakRegressionSignal,
};
pub use report::{build_soak_report_bundle, build_soak_report_bundle_with_exploration};
pub use reproduction::{
    attach_reproduction_bundle_to_pack, read_reproduction_bundle_from_pack,
    validate_reproduction_bundle, ReproductionBundle, ReproductionBundleAttachment,
    REPRODUCTION_BUNDLE_RELATIVE_PATH,
};
pub use resume::{
    read_soak_shard_checkpoint, validate_soak_shard_checkpoint, write_soak_shard_checkpoint,
    SoakShardCheckpoint,
};
pub use runner::{
    extract_failure_corpus, resume_local_soak_shard, run_local_soak_shard, LocalSoakRunner,
    LocalSoakRunnerConfig, SoakCaseFailure, SoakCaseResult, SoakCaseStatus, SoakReplayObservation,
    SoakRunRequest, SoakRunResult, SoakRunnerErrorPolicy,
};
pub use serialization::{
    deserialize_failure_corpus_index_json, deserialize_failure_reproduction_manifest_json,
    deserialize_soak_artifact_manifest_json, deserialize_soak_health_report_json,
    deserialize_soak_report_bundle_json, deserialize_soak_run_config_json,
    deserialize_soak_shard_checkpoint_json, deserialize_soak_shard_manifest_json,
    deserialize_soak_shard_plan_json, deserialize_soak_telemetry_report_json,
    serialize_failure_corpus_index_json, serialize_failure_reproduction_manifest_json,
    serialize_soak_artifact_manifest_json, serialize_soak_health_report_json,
    serialize_soak_report_bundle_json, serialize_soak_run_config_json,
    serialize_soak_shard_checkpoint_json, serialize_soak_shard_manifest_json,
    serialize_soak_shard_plan_json, serialize_soak_telemetry_report_json,
};
pub use shard::{
    plan_soak_shards, validate_soak_shard_manifest, validate_soak_shard_plan,
    validate_soak_shard_summary, SoakCaseId, SoakCasePlan, SoakShardId, SoakShardManifest,
    SoakShardPlan, SoakShardPlanner, SoakShardProgress, SoakShardResumeToken, SoakShardStatus,
    SoakShardSummary, SoakShardValidation, SoakShardValidationIssue,
};
pub use telemetry::{
    reject_forbidden_metric_label, validate_soak_telemetry_report, InternalCountMetric,
    InternalSizeMetric, InternalTimingMetric, InternalTimingMetricKind,
    SoakTelemetryClassification, SoakTelemetryCounters, SoakTelemetryDurations,
    SoakTelemetryReport, SoakTelemetryReportId, SoakTelemetrySnapshot,
};

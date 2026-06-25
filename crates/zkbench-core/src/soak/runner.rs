//! Local soak runner.

use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::adapters::{LocalJsonAdapter, LocalJsonReplayInput, LocalJsonReplaySummary};
use crate::error::{Result, ZkBenchError};
use crate::evidence::ClaimBoundary;
use crate::formal::{evaluate_formal_lane_pipeline, pipeline_outcome_is_declared_only};
use crate::generator::{generate_instance, FamilyKind, GeneratorConfig, InstanceParams};
use crate::mutation::{apply_mutation_for_class, MutatedBenchmarkInstance, MutationClass};
use crate::pack::{BenchmarkPackReader, BenchmarkPackWriter};
use crate::replay::{
    build_local_replay_manifest_for_instance, build_local_replay_manifest_for_mutation,
    ReplayManifest, ReplayResult, ReplayStatus,
};
use crate::scoring::observed_distinguishability_axis;

use super::artifact_layout::{write_json, SoakArtifactLayout};
use super::config::{SoakOutputPolicy, SoakRunConfig};
use super::failure_corpus::{
    build_failure_corpus_entry, FailureCorpus, FailureCorpusEntryInput, FailureCorpusIndex,
    FailureCorpusKind,
};
use super::health::SoakHealthReport;
use super::resume::{
    read_soak_shard_checkpoint, validate_soak_shard_checkpoint, write_soak_shard_checkpoint,
    SoakShardCheckpoint,
};
use super::shard::{
    validate_soak_shard_summary, SoakCaseId, SoakCasePlan, SoakShardId, SoakShardManifest,
    SoakShardPlan, SoakShardProgress, SoakShardStatus, SoakShardSummary,
};
use super::telemetry::{
    default_classification, validate_soak_telemetry_report, InternalCountMetric,
    InternalTimingMetricKind, SoakTelemetryClock, SoakTelemetryCounters, SoakTelemetryDurations,
    SoakTelemetryReport, SoakTelemetrySnapshot, SystemTelemetryClock,
};

/// Runner error policy.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum SoakRunnerErrorPolicy {
    /// Continue after case failures and record them.
    ContinueAndRecord,
    /// Stop at first case failure.
    StopOnFirstFailure,
    /// Skip failed cases when resuming.
    SkipFailedOnResume,
    /// Retry failed cases when resuming.
    RetryFailedOnResume,
}

/// Local soak runner config.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalSoakRunnerConfig {
    /// Error policy.
    pub error_policy: SoakRunnerErrorPolicy,
    /// Enable synthetic proposal/review preview accounting hook.
    pub enable_proposal_review_preview: bool,
    /// Allow pack directory overwrite.
    pub overwrite_existing_packs: bool,
}

impl Default for LocalSoakRunnerConfig {
    fn default() -> Self {
        Self {
            error_policy: SoakRunnerErrorPolicy::ContinueAndRecord,
            enable_proposal_review_preview: false,
            overwrite_existing_packs: false,
        }
    }
}

/// Run request.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakRunRequest {
    /// Shard id.
    pub shard_id: SoakShardId,
    /// Resume when a checkpoint exists.
    pub resume: bool,
}

/// Case status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum SoakCaseStatus {
    /// Completed.
    Completed,
    /// Completed with local rejections.
    CompletedWithLocalRejections,
    /// Generation failed.
    FailedGeneration,
    /// Mutation failed.
    FailedMutation,
    /// Replay failed.
    FailedReplay,
    /// Pack write failed.
    FailedPackWrite,
    /// Proposal preview failed.
    FailedProposalPreview,
    /// Skipped by resume.
    SkippedByResume,
    /// Skipped by limit.
    SkippedByLimit,
    /// Inconclusive.
    Inconclusive,
}

/// Case failure.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakCaseFailure {
    /// Failure kind.
    pub failure_kind: FailureCorpusKind,
    /// Phase.
    pub phase: String,
    /// Message.
    pub message: String,
    /// Mutation class, when applicable.
    #[serde(default)]
    pub mutation_class: Option<MutationClass>,
    /// Trace id, when applicable.
    #[serde(default)]
    pub trace_id: Option<String>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Case result.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SoakCaseResult {
    /// Case id.
    pub case_id: SoakCaseId,
    /// Family kind.
    pub family_kind: FamilyKind,
    /// Generator seed.
    pub generator_seed: u64,
    /// Status.
    pub status: SoakCaseStatus,
    /// Mutation ids.
    #[serde(default)]
    pub mutation_ids: Vec<String>,
    /// Replay result ids.
    #[serde(default)]
    pub replay_result_ids: Vec<String>,
    /// Failures.
    #[serde(default)]
    pub failures: Vec<SoakCaseFailure>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Run result.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SoakRunResult {
    /// Shard summary.
    pub shard_summary: SoakShardSummary,
    /// Case results.
    pub case_results: Vec<SoakCaseResult>,
    /// Telemetry report.
    pub telemetry_report: SoakTelemetryReport,
    /// Health report.
    pub health_report: SoakHealthReport,
    /// Failure corpus index.
    pub failure_corpus_index: FailureCorpusIndex,
    /// Final checkpoint.
    pub checkpoint: SoakShardCheckpoint,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl SoakRunResult {
    /// Claim boundary.
    pub fn claim_boundary(&self) -> ClaimBoundary {
        self.claim_boundary
    }

    /// Telemetry.
    pub fn telemetry(&self) -> &SoakTelemetryReport {
        &self.telemetry_report
    }

    /// Reports never contain ZK backend performance claims.
    pub fn contains_zk_backend_performance_claims(&self) -> bool {
        false
    }
}

/// Local soak runner.
pub struct LocalSoakRunner {
    plan: SoakShardPlan,
    adapter: LocalJsonAdapter,
    output_dir: Option<PathBuf>,
    clock: Box<dyn SoakTelemetryClock>,
    config: LocalSoakRunnerConfig,
}

struct CasePackPayload {
    instance: crate::generator::GeneratedBenchmarkInstance,
    mutations: Vec<MutatedBenchmarkInstance>,
    manifests: Vec<ReplayManifest>,
    results: Vec<ReplayResult>,
    failed: bool,
}

impl LocalSoakRunner {
    /// Create a new local soak runner.
    pub fn new(plan: SoakShardPlan) -> Self {
        Self {
            plan,
            adapter: LocalJsonAdapter::default(),
            output_dir: None,
            clock: Box::<SystemTelemetryClock>::default(),
            config: LocalSoakRunnerConfig::default(),
        }
    }

    /// Use a specific local JSON adapter.
    pub fn with_local_json_adapter(mut self, adapter: LocalJsonAdapter) -> Self {
        self.adapter = adapter;
        self
    }

    /// Write local artifacts under a caller-provided directory.
    pub fn with_temp_or_user_output_dir(mut self, output_dir: impl Into<PathBuf>) -> Self {
        self.output_dir = Some(output_dir.into());
        self
    }

    /// Use a specific clock.
    pub fn with_clock(mut self, clock: impl SoakTelemetryClock + 'static) -> Self {
        self.clock = Box::new(clock);
        self
    }

    /// Override runner config.
    pub fn with_runner_config(mut self, config: LocalSoakRunnerConfig) -> Self {
        self.config = config;
        self
    }

    /// Run a shard.
    pub fn run_shard(&mut self, shard_id: SoakShardId) -> Result<SoakRunResult> {
        self.run_request(SoakRunRequest {
            shard_id,
            resume: true,
        })
    }

    /// Run a request.
    pub fn run_request(&mut self, request: SoakRunRequest) -> Result<SoakRunResult> {
        let manifest = self
            .plan
            .shard_manifests
            .iter()
            .find(|manifest| manifest.shard_id == request.shard_id)
            .cloned()
            .ok_or_else(|| {
                ZkBenchError::soak(
                    "soak.runner.shard_id",
                    format!("unknown shard id {}", request.shard_id.value),
                )
            })?;
        let total_start = self.clock.now_ms();
        let layout = SoakArtifactLayout::for_shard(&manifest.shard_id);
        let mut checkpoint = self.initial_checkpoint(&manifest, &layout, request.resume)?;
        let mut counters = checkpoint.telemetry_counters.clone();
        let mut durations = SoakTelemetryDurations::default();
        let mut case_results = Vec::new();
        let mut corpus =
            FailureCorpus::empty(format!("failure_corpus_{}", manifest.shard_id.value));

        self.write_static_artifacts(&layout, &manifest)?;
        for (case_index, case_id) in manifest.assigned_case_ids.iter().enumerate() {
            let case_plan = self.case_plan(case_id)?;
            if checkpoint.completed_case(case_id) {
                checkpoint.mark_skipped(case_id.clone());
                case_results.push(SoakCaseResult {
                    case_id: case_id.clone(),
                    family_kind: case_plan.family_kind,
                    generator_seed: case_plan.generator_seed,
                    status: SoakCaseStatus::SkippedByResume,
                    mutation_ids: Vec::new(),
                    replay_result_ids: Vec::new(),
                    failures: Vec::new(),
                    claim_boundary: ClaimBoundary::Level0DesignNote,
                    notes: vec!["case skipped because checkpoint marked it completed".to_string()],
                });
                continue;
            }

            let case_result = self.run_case(
                case_plan,
                &layout,
                &mut counters,
                &mut durations,
                &mut corpus,
            )?;
            if case_result.failures.is_empty() {
                checkpoint.mark_completed(case_result.case_id.clone(), case_index);
            } else {
                checkpoint.mark_failed(case_result.case_id.clone());
                // Each failure pushed one corpus entry in run_case, in order;
                // reference the matching tail entries rather than repeating the last one.
                let failure_count = case_result.failures.len();
                let first_entry_index = corpus.index.entries.len().saturating_sub(failure_count);
                for entry in &corpus.index.entries[first_entry_index..] {
                    checkpoint.failure_corpus_refs.push(entry.entry_id.clone());
                }
                for failure in &case_result.failures {
                    increment_failure_phase(&mut counters, &failure.phase);
                }
                if self.config.error_policy == SoakRunnerErrorPolicy::StopOnFirstFailure {
                    checkpoint.telemetry_counters = counters.clone();
                    self.write_checkpoint(&layout, &checkpoint)?;
                    case_results.push(case_result);
                    break;
                }
            }
            checkpoint.telemetry_counters = counters.clone();
            self.write_checkpoint(&layout, &checkpoint)?;
            case_results.push(case_result);
        }

        let total_duration = self.clock.now_ms().saturating_sub(total_start);
        durations.add_metric(InternalTimingMetricKind::SoakRunnerTotal, total_duration);
        let progress = SoakShardProgress {
            total_cases: manifest.expected_case_count,
            completed_cases: checkpoint.completed_case_ids.len(),
            failed_cases: checkpoint.failed_case_ids.len(),
            skipped_cases: checkpoint.skipped_case_ids.len(),
        };
        let status = if progress.failed_cases > 0 {
            SoakShardStatus::CompletedWithFailures
        } else {
            SoakShardStatus::Completed
        };
        let shard_summary = SoakShardSummary {
            shard_id: manifest.shard_id.clone(),
            status,
            progress,
            claim_boundary: ClaimBoundary::Level0DesignNote,
            notes: vec!["Shard summary is local health metadata only.".to_string()],
        };
        let summary_validation = validate_soak_shard_summary(&shard_summary);
        if !summary_validation.valid {
            return Err(ZkBenchError::soak(
                "soak.runner.shard_summary",
                format!("invalid shard summary: {:?}", summary_validation.issues),
            ));
        }
        let telemetry_report = SoakTelemetryReport {
            report_id: format!("telemetry_{}", manifest.shard_id.value),
            report_version: "phase-k-soak-telemetry-v0".to_string(),
            source_config_id: self.plan.config.id.clone(),
            shard_id: Some(manifest.shard_id.clone()),
            snapshot: SoakTelemetrySnapshot {
                counters: counters.clone(),
                durations,
                classification: default_classification(),
                claim_boundary: ClaimBoundary::Level0DesignNote,
            },
            claim_boundary: ClaimBoundary::Level0DesignNote,
            notes: vec![
                "Local soak telemetry is not official benchmark evidence.".to_string(),
                "Internal timing telemetry is not ZK backend performance.".to_string(),
            ],
        };
        validate_soak_telemetry_report(&telemetry_report)?;
        corpus.recompute_summary();
        let health_report = SoakHealthReport::from_shard(
            self.plan.config.id.clone(),
            &shard_summary,
            &telemetry_report,
            &corpus.index,
        );
        self.write_final_artifacts(&layout, &telemetry_report, &health_report, &corpus.index)?;
        Ok(SoakRunResult {
            shard_summary,
            case_results,
            telemetry_report,
            health_report,
            failure_corpus_index: corpus.index,
            checkpoint,
            claim_boundary: ClaimBoundary::Level0DesignNote,
            notes: vec!["Local soak run result is a Level0DesignNote health artifact.".to_string()],
        })
    }

    fn run_case(
        &self,
        case_plan: &SoakCasePlan,
        layout: &SoakArtifactLayout,
        counters: &mut SoakTelemetryCounters,
        durations: &mut SoakTelemetryDurations,
        corpus: &mut FailureCorpus,
    ) -> Result<SoakCaseResult> {
        let mut failures = Vec::new();
        let generation_start = self.clock.now_ms();
        let generator_config = generator_config_for_case(case_plan, &self.plan.config)?;
        let instance = match generate_instance(
            generator_config,
            InstanceParams {
                id_suffix: case_plan.id.clone(),
            },
        ) {
            Ok(instance) => instance,
            Err(error) => {
                let failure = failure(
                    FailureCorpusKind::GenerationFailure,
                    "generation",
                    error.to_string(),
                    None,
                    None,
                );
                failures.push(failure.clone());
                corpus.push(corpus_entry(&self.plan, case_plan, &failure, None));
                counters.failure_count = counters.failure_count.saturating_add(1);
                return Ok(case_result(
                    case_plan,
                    SoakCaseStatus::FailedGeneration,
                    failures,
                ));
            }
        };
        counters.generated_family_count = counters.generated_family_count.saturating_add(1);
        counters.generated_instance_count = counters.generated_instance_count.saturating_add(1);
        durations.add_metric(
            InternalTimingMetricKind::Generation,
            self.clock.now_ms().saturating_sub(generation_start),
        );

        let mut replay_manifests = Vec::new();
        let mut replay_results = Vec::new();
        let mut mutation_outputs = Vec::new();
        let replay_start = self.clock.now_ms();
        match build_local_replay_manifest_for_instance(&instance)
            .and_then(|manifest| self.replay_manifest(manifest))
        {
            Ok((manifest, result, summary)) => {
                update_replay_counters(counters, &result, &summary);
                replay_manifests.push(manifest);
                replay_results.push(result);
            }
            Err(error) => {
                let failure = failure(
                    FailureCorpusKind::ReplayFailure,
                    "local_replay",
                    error.to_string(),
                    None,
                    None,
                );
                failures.push(failure.clone());
                corpus.push(corpus_entry(&self.plan, case_plan, &failure, None));
                counters.failure_count = counters.failure_count.saturating_add(1);
                counters.local_replay_failed_count =
                    counters.local_replay_failed_count.saturating_add(1);
            }
        }
        durations.add_metric(
            InternalTimingMetricKind::LocalReplay,
            self.clock.now_ms().saturating_sub(replay_start),
        );

        let mutation_start = self.clock.now_ms();
        for mutation_class in &case_plan.mutation_classes {
            match apply_selected_mutation(&instance, *mutation_class) {
                Ok(mutated) => {
                    counters.mutation_variant_count =
                        counters.mutation_variant_count.saturating_add(1);
                    if let Ok(pipeline_outcome) =
                        evaluate_formal_lane_pipeline(*mutation_class, &mutated.surface_spec)
                    {
                        counters.record_formal_lane_pipeline(
                            pipeline_outcome.template_derived,
                            pipeline_outcome_is_declared_only(&pipeline_outcome),
                        );
                    }
                    let replay_start = self.clock.now_ms();
                    match build_local_replay_manifest_for_mutation(&mutated)
                        .and_then(|manifest| self.replay_manifest(manifest))
                    {
                        Ok((manifest, result, summary)) => {
                            update_replay_counters(counters, &result, &summary);
                            if let Some(trace) = result.trace_results.first() {
                                let axis = observed_distinguishability_axis(
                                    mutated.expected_verdict,
                                    trace.backend_outcome,
                                );
                                counters.record_distinguishability_axis(axis);
                            }
                            replay_manifests.push(manifest);
                            replay_results.push(result);
                            mutation_outputs.push(mutated);
                        }
                        Err(error) => {
                            let failure = failure(
                                FailureCorpusKind::ReplayFailure,
                                "local_replay",
                                error.to_string(),
                                Some(*mutation_class),
                                Some(mutated.primary_trace.id.clone()),
                            );
                            failures.push(failure.clone());
                            corpus.push(corpus_entry(&self.plan, case_plan, &failure, None));
                            counters.failure_count = counters.failure_count.saturating_add(1);
                            counters.local_replay_failed_count =
                                counters.local_replay_failed_count.saturating_add(1);
                        }
                    }
                    durations.add_metric(
                        InternalTimingMetricKind::LocalReplay,
                        self.clock.now_ms().saturating_sub(replay_start),
                    );
                }
                Err(error) => {
                    counters.mutation_no_target_count =
                        counters.mutation_no_target_count.saturating_add(1);
                    if is_targetless_mutation_error(&error) {
                        continue;
                    }
                    let failure = failure(
                        FailureCorpusKind::MutationFailure,
                        "mutation",
                        error.to_string(),
                        Some(*mutation_class),
                        None,
                    );
                    failures.push(failure.clone());
                    corpus.push(corpus_entry(&self.plan, case_plan, &failure, None));
                    counters.failure_count = counters.failure_count.saturating_add(1);
                }
            }
        }
        durations.add_metric(
            InternalTimingMetricKind::Mutation,
            self.clock.now_ms().saturating_sub(mutation_start),
        );

        if self.should_write_pack(counters, !failures.is_empty()) {
            let pack_start = self.clock.now_ms();
            let payload = CasePackPayload {
                instance,
                mutations: mutation_outputs.clone(),
                manifests: replay_manifests.clone(),
                results: replay_results.clone(),
                failed: !failures.is_empty(),
            };
            if let Err(error) = self.write_case_pack(layout, case_plan, payload) {
                let failure = failure(
                    FailureCorpusKind::PackValidationFailure,
                    "pack_write",
                    error.to_string(),
                    None,
                    None,
                );
                failures.push(failure.clone());
                corpus.push(corpus_entry(&self.plan, case_plan, &failure, None));
                counters.failure_count = counters.failure_count.saturating_add(1);
            } else {
                counters.pack_write_count = counters.pack_write_count.saturating_add(1);
                counters.pack_read_validation_count =
                    counters.pack_read_validation_count.saturating_add(1);
            }
            durations.add_metric(
                InternalTimingMetricKind::PackWriteRead,
                self.clock.now_ms().saturating_sub(pack_start),
            );
        }

        let status = case_status_from_failures_and_replays(&failures, &replay_results);
        Ok(SoakCaseResult {
            case_id: case_plan.id.clone(),
            family_kind: case_plan.family_kind,
            generator_seed: case_plan.generator_seed,
            status,
            mutation_ids: mutation_outputs
                .iter()
                .map(|mutation| mutation.id.clone())
                .collect(),
            replay_result_ids: replay_results
                .iter()
                .map(|result| result.id.clone())
                .collect(),
            failures,
            claim_boundary: ClaimBoundary::Level0DesignNote,
            notes: vec![
                "Case result is local soak health metadata only.".to_string(),
                "Local oracle acceptance is semantic-local only.".to_string(),
            ],
        })
    }

    fn replay_manifest(
        &self,
        manifest: ReplayManifest,
    ) -> Result<(ReplayManifest, ReplayResult, LocalJsonReplaySummary)> {
        if manifest.claim_boundary > ClaimBoundary::Level1LocalReplay {
            return Err(ZkBenchError::soak(
                "soak.runner.replay_manifest.claim_boundary",
                "local replay manifest exceeded Level1LocalReplay",
            ));
        }
        let output = self.adapter.replay_with_summary(LocalJsonReplayInput {
            manifest: manifest.clone(),
        })?;
        if output.replay_result.claim_boundary > ClaimBoundary::Level1LocalReplay {
            return Err(ZkBenchError::soak(
                "soak.runner.replay_result.claim_boundary",
                "local replay result exceeded Level1LocalReplay",
            ));
        }
        Ok((manifest, output.replay_result, output.summary))
    }

    fn initial_checkpoint(
        &self,
        manifest: &SoakShardManifest,
        layout: &SoakArtifactLayout,
        resume: bool,
    ) -> Result<SoakShardCheckpoint> {
        let resume_token = manifest.resume_token.clone().ok_or_else(|| {
            ZkBenchError::soak(
                "soak.runner.manifest.resume_token",
                "shard manifest is missing resume token",
            )
        })?;
        let empty = SoakShardCheckpoint::empty(
            manifest.shard_id.clone(),
            manifest.config_digest.clone(),
            resume_token.clone(),
        );
        let Some(output_dir) = &self.output_dir else {
            return Ok(empty);
        };
        let checkpoint_path = output_dir.join(&layout.checkpoint_path);
        if resume && checkpoint_path.exists() {
            let checkpoint = read_soak_shard_checkpoint(&checkpoint_path)?;
            validate_soak_shard_checkpoint(&checkpoint, &manifest.config_digest, &resume_token)?;
            Ok(checkpoint)
        } else {
            Ok(empty)
        }
    }

    fn write_static_artifacts(
        &self,
        layout: &SoakArtifactLayout,
        manifest: &SoakShardManifest,
    ) -> Result<()> {
        let Some(output_dir) = &self.output_dir else {
            return Ok(());
        };
        write_json(output_dir.join(&layout.run_config_path), &self.plan.config)?;
        write_json(output_dir.join(&layout.shard_plan_path), &self.plan)?;
        write_json(output_dir.join(&layout.shard_manifest_path), manifest)
    }

    fn write_checkpoint(
        &self,
        layout: &SoakArtifactLayout,
        checkpoint: &SoakShardCheckpoint,
    ) -> Result<()> {
        let Some(output_dir) = &self.output_dir else {
            return Ok(());
        };
        write_soak_shard_checkpoint(output_dir.join(&layout.checkpoint_path), checkpoint)
    }

    fn write_final_artifacts(
        &self,
        layout: &SoakArtifactLayout,
        telemetry: &SoakTelemetryReport,
        health: &SoakHealthReport,
        corpus: &FailureCorpusIndex,
    ) -> Result<()> {
        let Some(output_dir) = &self.output_dir else {
            return Ok(());
        };
        write_json(output_dir.join(&layout.telemetry_path), telemetry)?;
        write_json(output_dir.join(&layout.health_report_path), health)?;
        write_json(output_dir.join(&layout.failure_corpus_index_path), corpus)?;
        write_json(output_dir.join(&layout.local_summary_path), health)
    }

    fn case_plan(&self, case_id: &str) -> Result<&SoakCasePlan> {
        self.plan
            .case_plans
            .iter()
            .find(|case| case.id == case_id)
            .ok_or_else(|| {
                ZkBenchError::soak(
                    "soak.runner.case_id",
                    format!("case id {case_id} was not found in plan"),
                )
            })
    }

    fn should_write_pack(&self, counters: &SoakTelemetryCounters, failed: bool) -> bool {
        match self.plan.config.output_policy {
            SoakOutputPolicy::NoPacks => false,
            SoakOutputPolicy::SampledPacks { max_packs }
            | SoakOutputPolicy::AllPacksWithinLimit { max_packs } => {
                counters.pack_write_count < max_packs
            }
            SoakOutputPolicy::FailurePacksOnly { max_failure_packs } => {
                failed && counters.pack_write_count < max_failure_packs
            }
        }
    }

    fn write_case_pack(
        &self,
        layout: &SoakArtifactLayout,
        case_plan: &SoakCasePlan,
        payload: CasePackPayload,
    ) -> Result<()> {
        let Some(output_dir) = &self.output_dir else {
            return Ok(());
        };
        let pack_dir = if payload.failed {
            Path::new(&layout.failure_packs_dir).join(&case_plan.id)
        } else {
            Path::new(&layout.sampled_packs_dir).join(&case_plan.id)
        };
        let mut writer = BenchmarkPackWriter::new(format!("phase_k_{}", case_plan.id))
            .with_generated_instance(payload.instance)
            .include_score_report(false)
            .overwrite(self.config.overwrite_existing_packs);
        for mutation in payload.mutations {
            writer = writer.with_mutated_instance(mutation);
        }
        for manifest in payload.manifests {
            writer = writer.with_replay_manifest(manifest);
        }
        for result in payload.results {
            writer = writer.with_replay_result(result);
        }
        let root = output_dir.join(pack_dir);
        writer.write_to(&root)?;
        let reader = BenchmarkPackReader::read(&root)?;
        let validation = reader.validate();
        if !validation.valid {
            return Err(ZkBenchError::soak(
                "soak.runner.pack_validation",
                format!("pack validation failed: {:?}", validation.errors),
            ));
        }
        Ok(())
    }
}

/// Run a local soak shard.
pub fn run_local_soak_shard(plan: SoakShardPlan, shard_id: SoakShardId) -> Result<SoakRunResult> {
    LocalSoakRunner::new(plan).run_shard(shard_id)
}

/// Resume a local soak shard.
pub fn resume_local_soak_shard(
    plan: SoakShardPlan,
    shard_id: SoakShardId,
    output_dir: impl Into<PathBuf>,
) -> Result<SoakRunResult> {
    LocalSoakRunner::new(plan)
        .with_temp_or_user_output_dir(output_dir)
        .run_shard(shard_id)
}

/// Extract a failure corpus from case results.
pub fn extract_failure_corpus(
    plan: &SoakShardPlan,
    shard_id: SoakShardId,
    case_results: &[SoakCaseResult],
) -> FailureCorpusIndex {
    let mut corpus = FailureCorpus::empty(format!("failure_corpus_{}", shard_id.value));
    for result in case_results {
        if let Some(case_plan) = plan
            .case_plans
            .iter()
            .find(|case| case.id == result.case_id)
        {
            for failure in &result.failures {
                corpus.push(corpus_entry(
                    plan,
                    case_plan,
                    failure,
                    Some(shard_id.clone()),
                ));
            }
        }
    }
    corpus.index
}

fn generator_config_for_case(
    case_plan: &SoakCasePlan,
    config: &SoakRunConfig,
) -> Result<GeneratorConfig> {
    let mut generator_config = match case_plan.family_kind {
        FamilyKind::BaselineFsm => GeneratorConfig::baseline_fsm(),
        FamilyKind::BranchingFsm => GeneratorConfig::branching_fsm(),
        FamilyKind::BoundedCounterLoop => GeneratorConfig::bounded_counter_loop(),
        FamilyKind::NestedLoop => GeneratorConfig::nested_loop(),
        FamilyKind::GuardHeavyMachine => GeneratorConfig::guard_heavy_machine(),
        FamilyKind::RecursiveEnvelope => GeneratorConfig::recursive_envelope(),
        FamilyKind::MemoryHeavyStateMachine => GeneratorConfig::memory_heavy_state_machine(),
        FamilyKind::PublicPrivateBoundaryStress => {
            GeneratorConfig::public_private_boundary_stress()
        }
        FamilyKind::ZkMlControlFlowMixed => GeneratorConfig::zkml_control_flow_mixed(),
    }
    .seed(case_plan.generator_seed);
    generator_config.tunables = case_plan.generator_tunables.clone();
    if matches!(
        case_plan.family_kind,
        FamilyKind::BoundedCounterLoop
            | FamilyKind::NestedLoop
            | FamilyKind::GuardHeavyMachine
            | FamilyKind::RecursiveEnvelope
            | FamilyKind::ZkMlControlFlowMixed
    ) {
        generator_config.tunables.trace_length =
            generator_config.tunables.loop_bound.saturating_add(1);
    }
    generator_config.limits.max_mutations_per_instance = config.normalized_mutations().len();
    Ok(generator_config)
}

fn apply_selected_mutation(
    instance: &crate::generator::GeneratedBenchmarkInstance,
    mutation_class: MutationClass,
) -> Result<MutatedBenchmarkInstance> {
    apply_mutation_for_class(instance, mutation_class)
}

fn is_targetless_mutation_error(error: &ZkBenchError) -> bool {
    matches!(
        error,
        ZkBenchError::Mutation { path, .. } if path.ends_with(".target")
    )
}

fn update_replay_counters(
    counters: &mut SoakTelemetryCounters,
    result: &ReplayResult,
    summary: &LocalJsonReplaySummary,
) {
    counters.traces_evaluated = counters
        .traces_evaluated
        .saturating_add(summary.trace_count);
    counters.local_oracle_accepted_count = counters
        .local_oracle_accepted_count
        .saturating_add(summary.local_accepted_count);
    counters.local_oracle_rejected_count = counters
        .local_oracle_rejected_count
        .saturating_add(summary.local_rejected_count);
    counters.local_oracle_capability_gap_count = counters
        .local_oracle_capability_gap_count
        .saturating_add(summary.capability_gap_count);
    if matches!(
        result.status,
        ReplayStatus::Completed
            | ReplayStatus::CompletedWithRejectedTraces
            | ReplayStatus::CapabilityGap
            | ReplayStatus::Inconclusive
    ) {
        counters.local_replay_completed_count =
            counters.local_replay_completed_count.saturating_add(1);
    } else {
        counters.local_replay_failed_count = counters.local_replay_failed_count.saturating_add(1);
    }
}

fn case_status_from_failures_and_replays(
    failures: &[SoakCaseFailure],
    replay_results: &[ReplayResult],
) -> SoakCaseStatus {
    if let Some(failure) = failures.first() {
        return match failure.failure_kind {
            FailureCorpusKind::GenerationFailure => SoakCaseStatus::FailedGeneration,
            FailureCorpusKind::MutationFailure => SoakCaseStatus::FailedMutation,
            FailureCorpusKind::ReplayFailure => SoakCaseStatus::FailedReplay,
            FailureCorpusKind::PackValidationFailure => SoakCaseStatus::FailedPackWrite,
            FailureCorpusKind::ProposalPreviewFailure => SoakCaseStatus::FailedProposalPreview,
            _ => SoakCaseStatus::Inconclusive,
        };
    }
    if replay_results.iter().any(|result| {
        matches!(
            result.status,
            ReplayStatus::CompletedWithRejectedTraces
                | ReplayStatus::CapabilityGap
                | ReplayStatus::Inconclusive
        )
    }) {
        SoakCaseStatus::CompletedWithLocalRejections
    } else {
        SoakCaseStatus::Completed
    }
}

fn case_result(
    case_plan: &SoakCasePlan,
    status: SoakCaseStatus,
    failures: Vec<SoakCaseFailure>,
) -> SoakCaseResult {
    SoakCaseResult {
        case_id: case_plan.id.clone(),
        family_kind: case_plan.family_kind,
        generator_seed: case_plan.generator_seed,
        status,
        mutation_ids: Vec::new(),
        replay_result_ids: Vec::new(),
        failures,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: Vec::new(),
    }
}

fn failure(
    failure_kind: FailureCorpusKind,
    phase: impl Into<String>,
    message: impl Into<String>,
    mutation_class: Option<MutationClass>,
    trace_id: Option<String>,
) -> SoakCaseFailure {
    SoakCaseFailure {
        failure_kind,
        phase: phase.into(),
        message: message.into(),
        mutation_class,
        trace_id,
        claim_boundary: ClaimBoundary::Level0DesignNote,
    }
}

fn corpus_entry(
    plan: &SoakShardPlan,
    case_plan: &SoakCasePlan,
    failure: &SoakCaseFailure,
    shard_id: Option<SoakShardId>,
) -> super::failure_corpus::FailureCorpusEntry {
    let shard_id = shard_id.unwrap_or_else(|| {
        plan.shard_manifests
            .iter()
            .find(|manifest| {
                manifest
                    .assigned_case_ids
                    .iter()
                    .any(|case_id| case_id == &case_plan.id)
            })
            .map(|manifest| manifest.shard_id.clone())
            .unwrap_or_else(|| SoakShardId::from_index(0))
    });
    build_failure_corpus_entry(FailureCorpusEntryInput {
        shard_id,
        case_id: case_plan.id.clone(),
        family_kind: case_plan.family_kind,
        generator_seed: case_plan.generator_seed,
        tunables: case_plan.generator_tunables.clone(),
        mutation_class: failure.mutation_class,
        trace_id: failure.trace_id.clone(),
        failure_kind: failure.failure_kind,
        local_error_summary: failure.message.clone(),
    })
}

fn increment_failure_phase(counters: &mut SoakTelemetryCounters, phase: &str) {
    if let Some(metric) = counters
        .failure_count_by_phase
        .iter_mut()
        .find(|metric| metric.metric_name == phase)
    {
        metric.count = metric.count.saturating_add(1);
        return;
    }
    counters.failure_count_by_phase.push(InternalCountMetric {
        metric_name: phase.to_string(),
        count: 1,
        classification: default_classification(),
    });
}

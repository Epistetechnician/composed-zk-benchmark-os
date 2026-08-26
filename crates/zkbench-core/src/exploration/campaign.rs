//! Provider-free local strategy campaigns for
//! `antithesis-inspired-deterministic-exploration-v1`.
//!
//! This module turns the deterministic explorer into a usable local strategy
//! harness. It freezes one primary metric, executes every policy through a
//! fresh local replay, retains Semantic IR, mutation provenance, oracle
//! outcomes, replay manifests/results, and failure-corpus entries, then
//! compares fixed baselines under equal deterministic allocation budgets.
//!
//! Assessment observations remain sealed until `finalize_assessment`. The
//! campaign never mutates oracle semantics or evidence state and never uses
//! wall-clock telemetry, backend-performance data, models, or network inputs.

use std::collections::BTreeSet;

use serde::{Deserialize, Serialize};

use crate::dsl::{OracleOutcome, SemanticIr};
use crate::error::{Result, ZkBenchError};
use crate::evidence::{
    compute_artifact_digest, ArtifactKind, ArtifactRole, ClaimBoundary, ResultClassification,
};
use crate::mutation::MutationProvenance;
use crate::replay::{ReplayManifest, ReplayResult};
use crate::soak::{
    build_failure_corpus_entry, validate_soak_shard_plan, FailureCorpusEntry,
    FailureCorpusEntryInput, FailureCorpusKind, FailureTriageStatus, LocalSoakRunner,
    LocalSoakRunnerConfig, MockTelemetryClock, SoakCasePlan, SoakCaseStatus, SoakRunRequest,
    SoakRunResult, SoakShardId, SoakShardPlan,
};

use super::{
    DeterministicExplorer, ExplorationPhase, ExplorationResult, ExplorationRunConfig,
    ExplorerPolicy, QueuePolicy, EXPLORATION_CLAIM_BOUNDARY,
};

/// Named state slice for the operational strategy layer.
pub const REAL_STRATEGY_STATE_SLICE: &str =
    "antithesis-inspired-deterministic-exploration-v1-real-target-campaign-matrix";

/// Version of the local strategy campaign schema.
pub const BASELINE_CAMPAIGN_SCHEMA_VERSION: &str = "antithesis-inspired-baseline-campaign-v1";

/// Frozen primary metric identifier.
pub const PRIMARY_METRIC_ID: &str = "distinct-reproducible-failure-classifications-per-case-budget";

/// Fixed strategy baseline names.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum BaselinePolicyKind {
    /// Canonical case and mutation ordering.
    StableDigest,
    /// Family-order round robin.
    RoundRobinFamilies,
    /// Mutation-order round robin.
    RoundRobinMutations,
    /// The bounded deterministic beam search.
    BeamSearch,
    /// A fixed-seed control policy with rotated ordering and tie behavior.
    SeededControl,
}

/// Deterministic work units used to compare strategies.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct ExplorationWorkUnits {
    /// Number of planned cases.
    pub case_count: usize,
    /// Number of deterministic shards.
    pub shard_count: usize,
    /// Number of configured mutation attempts.
    pub mutation_attempt_count: usize,
    /// Number of local replay outputs produced.
    pub replay_attempt_count: usize,
}

impl ExplorationWorkUnits {
    fn allocation_key(self) -> (usize, usize, usize) {
        (
            self.case_count,
            self.shard_count,
            self.mutation_attempt_count,
        )
    }
}

/// Frozen primary metric for one local strategy run.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExplorationPrimaryMetric {
    /// Metric identifier.
    pub metric_id: String,
    /// Distinct failure classifications reproduced by local replay.
    pub failure_classifications: Vec<ResultClassification>,
    /// Deterministic work-unit accounting.
    pub work_units: ExplorationWorkUnits,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

impl ExplorationPrimaryMetric {
    /// Number of distinct reproducible failure classifications.
    pub fn value(&self) -> usize {
        self.failure_classifications.len()
    }

    /// Validate the frozen metric contract.
    pub fn validate(&self) -> Result<()> {
        if self.metric_id != PRIMARY_METRIC_ID {
            return Err(ZkBenchError::validation(
                "exploration.metric.metric_id",
                "unsupported primary metric",
            ));
        }
        if self.work_units.case_count == 0 || self.work_units.shard_count == 0 {
            return Err(ZkBenchError::validation(
                "exploration.metric.work_units",
                "metric work units must include cases and shards",
            ));
        }
        if self.claim_boundary != EXPLORATION_CLAIM_BOUNDARY {
            return Err(ZkBenchError::validation(
                "exploration.metric.claim_boundary",
                "strategy metric must remain Level0DesignNote",
            ));
        }
        let mut seen = BTreeSet::new();
        for classification in &self.failure_classifications {
            if !is_reproducible_failure_classification(*classification) {
                return Err(ZkBenchError::validation(
                    "exploration.metric.failure_classifications",
                    "primary metric contains a non-failure classification",
                ));
            }
            if !seen.insert(format!("{classification:?}")) {
                return Err(ZkBenchError::validation(
                    "exploration.metric.failure_classifications",
                    "primary metric contains duplicate classifications",
                ));
            }
        }
        Ok(())
    }
}

/// Result classifications counted by the frozen primary metric.
pub fn is_reproducible_failure_classification(classification: ResultClassification) -> bool {
    matches!(
        classification,
        ResultClassification::ExpectedAcceptRejected
            | ResultClassification::ExpectedRejectAcceptedUnsoundCandidate
            | ResultClassification::ExpectedRejectBackendError
            | ResultClassification::UnexpectedOutcome
            | ResultClassification::MalformedArtifact
    )
}

/// Repository-owned local target corpus descriptor.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LocalTargetCorpus {
    /// Corpus identifier.
    pub corpus_id: String,
    /// Corpus schema version.
    pub schema_version: String,
    /// Canonical source plan.
    pub plan: SoakShardPlan,
    /// Digest binding the target corpus to its source plan.
    pub target_corpus_digest: String,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Nonclaim notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl LocalTargetCorpus {
    /// Build the validation corpus from a validated exploration configuration.
    ///
    /// The withheld assessment plan is intentionally not materialized here.
    /// It is created only by the internal assessment path after the caller
    /// explicitly requests the finalized assessment phase.
    pub fn from_exploration_config(config: &ExplorationRunConfig) -> Result<Self> {
        config.validate()?;
        let explorer = DeterministicExplorer::new(config.clone())?;
        let reference_policy = ExplorerPolicy::from_config(&config.base_soak_config);
        let plan = explorer.plan_shards(&reference_policy, ExplorationPhase::Validation)?;
        Self::from_plan(plan)
    }

    /// Build a corpus from a canonical local soak plan.
    pub fn from_plan(plan: SoakShardPlan) -> Result<Self> {
        validate_soak_shard_plan(&plan)?;
        let target_corpus_digest = compute_artifact_digest(
            &plan,
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Manifest),
        )?
        .hex_digest;
        let corpus = Self {
            corpus_id: format!("target_corpus_{}", plan.config.id),
            schema_version: "local-target-corpus-v1".to_string(),
            plan,
            target_corpus_digest,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
            notes: vec![
                "Repository-owned local target corpus only.".to_string(),
                "Corpus outputs are not accepted benchmark evidence.".to_string(),
            ],
        };
        corpus.validate()?;
        Ok(corpus)
    }

    /// Validate corpus identity and local claim boundaries.
    pub fn validate(&self) -> Result<()> {
        if self.corpus_id.trim().is_empty() {
            return Err(ZkBenchError::validation(
                "exploration.target_corpus.corpus_id",
                "target corpus id is empty",
            ));
        }
        if self.schema_version != "local-target-corpus-v1" {
            return Err(ZkBenchError::validation(
                "exploration.target_corpus.schema_version",
                "unsupported target corpus schema version",
            ));
        }
        if self.claim_boundary != EXPLORATION_CLAIM_BOUNDARY {
            return Err(ZkBenchError::validation(
                "exploration.target_corpus.claim_boundary",
                "target corpus must remain Level0DesignNote",
            ));
        }
        validate_soak_shard_plan(&self.plan)?;
        let expected_digest = compute_artifact_digest(
            &self.plan,
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Manifest),
        )?
        .hex_digest;
        if self.target_corpus_digest != expected_digest {
            return Err(ZkBenchError::validation(
                "exploration.target_corpus.digest",
                "target corpus digest does not match its source plan",
            ));
        }
        Ok(())
    }
}

/// Per-case provenance assembled by the real local target adapter.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LocalTargetCaseObservation {
    /// Stable case id.
    pub case_id: String,
    /// Stable shard id.
    pub shard_id: SoakShardId,
    /// Family and generator seed from the target corpus.
    pub family_kind: crate::generator::FamilyKind,
    /// Generator seed from the target corpus.
    pub generator_seed: u64,
    /// Number of configured mutation attempts for this case.
    pub mutation_attempt_count: usize,
    /// Local case status.
    pub status: TargetCaseStatus,
    /// Generated and mutated Semantic IR payloads observed for this case.
    pub semantic_irs: Vec<SemanticIr>,
    /// Exact mutation provenance observed for this case.
    pub mutation_provenance: Vec<MutationProvenance>,
    /// Exact replay manifests observed for this case.
    pub replay_manifests: Vec<ReplayManifest>,
    /// Exact replay results observed for this case.
    pub replay_results: Vec<ReplayResult>,
    /// Local semantic oracle outcomes from replay traces.
    pub oracle_outcomes: Vec<OracleOutcome>,
    /// Failure-corpus entries for this case; empty means no corpus failure.
    pub failure_corpus_entries: Vec<FailureCorpusEntry>,
    /// Explicit missing-input markers for failed or incomplete cases.
    #[serde(default)]
    pub missing_artifacts: Vec<String>,
    /// Claim boundary of the case observation.
    pub claim_boundary: ClaimBoundary,
}

/// Availability state for one target case observation.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum TargetCaseStatus {
    /// Semantic IR and replay provenance are complete.
    Complete,
    /// Generation failed before Semantic IR was available.
    GenerationFailure,
    /// Generation existed but no replay result was produced.
    ReplayFailure,
    /// The local run completed with an explicit incomplete input marker.
    Incomplete,
}

/// Aggregate local target run for one policy and one phase.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LocalTargetRun {
    /// Policy digest.
    pub policy_digest: String,
    /// Validation or finalized assessment phase.
    pub phase: ExplorationPhase,
    /// Target corpus digest shared by all policy runs.
    pub target_corpus_digest: String,
    /// Per-case provenance.
    pub case_observations: Vec<LocalTargetCaseObservation>,
    /// Frozen primary metric.
    pub primary_metric: ExplorationPrimaryMetric,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Nonclaim notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl LocalTargetRun {
    /// Validate provenance, work units, replay identity, and metric integrity.
    pub fn validate(&self) -> Result<()> {
        if self.policy_digest.trim().is_empty() {
            return Err(ZkBenchError::validation(
                "exploration.target_run.policy_digest",
                "target run policy digest is empty",
            ));
        }
        if self.target_corpus_digest.trim().is_empty() {
            return Err(ZkBenchError::validation(
                "exploration.target_run.target_corpus_digest",
                "target run corpus digest is empty",
            ));
        }
        if self.claim_boundary != EXPLORATION_CLAIM_BOUNDARY {
            return Err(ZkBenchError::validation(
                "exploration.target_run.claim_boundary",
                "target run must remain Level0DesignNote",
            ));
        }
        let mut case_ids = BTreeSet::new();
        let mut mutation_attempt_count = 0usize;
        let mut replay_attempt_count = 0usize;
        let mut classifications = BTreeSet::new();
        for case in &self.case_observations {
            if !case_ids.insert(case.case_id.clone()) {
                return Err(ZkBenchError::validation(
                    "exploration.target_run.case_observations",
                    "target run contains duplicate case ids",
                ));
            }
            validate_case_observation(case)?;
            mutation_attempt_count =
                mutation_attempt_count.saturating_add(case.mutation_attempt_count);
            replay_attempt_count = replay_attempt_count.saturating_add(case.replay_results.len());
            for classification in case
                .replay_results
                .iter()
                .flat_map(|result| result.trace_results.iter())
                .map(|trace| trace.result_classification)
            {
                if is_reproducible_failure_classification(classification) {
                    classifications.insert(format!("{classification:?}"));
                }
            }
        }
        let expected_classes = self
            .primary_metric
            .failure_classifications
            .iter()
            .map(|classification| format!("{classification:?}"))
            .collect::<BTreeSet<_>>();
        if classifications != expected_classes {
            return Err(ZkBenchError::validation(
                "exploration.target_run.primary_metric",
                "primary metric classifications do not match replay results",
            ));
        }
        if self.primary_metric.work_units.case_count != self.case_observations.len()
            || self.primary_metric.work_units.mutation_attempt_count != mutation_attempt_count
            || self.primary_metric.work_units.replay_attempt_count != replay_attempt_count
        {
            return Err(ZkBenchError::validation(
                "exploration.target_run.work_units",
                "primary metric work units do not match target observations",
            ));
        }
        self.primary_metric.validate()
    }
}

/// Provider-free adapter from local soak plans to strategy observations.
#[derive(Debug, Clone)]
pub struct LocalTargetAdapter {
    corpus: LocalTargetCorpus,
    runner_config: LocalSoakRunnerConfig,
}

impl LocalTargetAdapter {
    /// Create an adapter for a repository-owned corpus.
    pub fn new(corpus: LocalTargetCorpus) -> Result<Self> {
        corpus.validate()?;
        Ok(Self {
            corpus,
            runner_config: LocalSoakRunnerConfig::default(),
        })
    }

    /// Override local runner behavior while retaining deterministic clocks.
    pub fn with_runner_config(mut self, runner_config: LocalSoakRunnerConfig) -> Self {
        self.runner_config = runner_config;
        self
    }

    /// Return the target corpus descriptor.
    pub fn corpus(&self) -> &LocalTargetCorpus {
        &self.corpus
    }

    /// Run one policy through fresh validation replays.
    pub fn run_validation_policy(
        &self,
        explorer: &DeterministicExplorer,
        policy: &ExplorerPolicy,
    ) -> Result<LocalTargetRun> {
        self.run_policy(explorer, policy, ExplorationPhase::Validation)
    }

    /// Run one policy through fresh local replays for an internal phase.
    ///
    /// Assessment execution is crate-visible only and is called by the
    /// explicit finalization path. This prevents public callers from reading
    /// withheld case observations before finalization.
    pub(crate) fn run_policy(
        &self,
        explorer: &DeterministicExplorer,
        policy: &ExplorerPolicy,
        phase: ExplorationPhase,
    ) -> Result<LocalTargetRun> {
        let plan = explorer.plan_shards(policy, phase)?;
        let reference_policy = ExplorerPolicy::from_config(&explorer.config().base_soak_config);
        let reference_plan = explorer.plan_shards(&reference_policy, phase)?;
        validate_equal_allocation(&reference_plan, &plan)?;
        let phase_corpus = LocalTargetCorpus::from_plan(reference_plan.clone())?;
        let policy_digest = policy.digest()?;
        let mut case_observations = Vec::new();
        for shard_manifest in &plan.shard_manifests {
            let mut runner = LocalSoakRunner::new(plan.clone())
                .with_clock(MockTelemetryClock::default())
                .with_runner_config(self.runner_config.clone());
            let result = runner.run_request(SoakRunRequest {
                shard_id: shard_manifest.shard_id.clone(),
                resume: false,
            })?;
            for case_id in &shard_manifest.assigned_case_ids {
                let case_plan = plan
                    .case_plans
                    .iter()
                    .find(|case| &case.id == case_id)
                    .ok_or_else(|| {
                        ZkBenchError::validation(
                            "exploration.target_run.case_plan",
                            "shard references an unknown target case",
                        )
                    })?;
                case_observations.push(build_case_observation(
                    case_plan,
                    &shard_manifest.shard_id,
                    &result,
                )?);
            }
        }
        case_observations.sort_by(|left, right| {
            left.case_id
                .cmp(&right.case_id)
                .then_with(|| left.shard_id.cmp(&right.shard_id))
        });
        let work_units = ExplorationWorkUnits {
            case_count: case_observations.len(),
            shard_count: plan.shard_manifests.len(),
            mutation_attempt_count: plan
                .case_plans
                .iter()
                .map(|case| case.mutation_classes.len())
                .sum(),
            replay_attempt_count: case_observations
                .iter()
                .map(|case| case.replay_results.len())
                .sum(),
        };
        let primary_metric = build_primary_metric(&case_observations, work_units);
        let run = LocalTargetRun {
            policy_digest,
            phase,
            target_corpus_digest: phase_corpus.target_corpus_digest,
            case_observations,
            primary_metric,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
            notes: vec![
                "Local target run uses fresh provider-free replay per policy.".to_string(),
                "Primary metric counts distinct reproducible local failure classifications only."
                    .to_string(),
            ],
        };
        run.validate()?;
        Ok(run)
    }
}

/// One baseline policy record with assessment sealed until finalization.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BaselinePolicyRecord {
    /// Baseline label.
    pub kind: BaselinePolicyKind,
    /// Policy evaluated by the local target adapter.
    pub policy: ExplorerPolicy,
    /// Policy digest.
    pub policy_digest: String,
    /// Fresh validation run.
    pub validation_run: LocalTargetRun,
    /// Fresh assessment run, present only after finalization.
    #[serde(default)]
    pub assessment_run: Option<LocalTargetRun>,
    /// Beam lineage and validation checkpoint for the beam baseline.
    #[serde(default)]
    pub beam_search_result: Option<ExplorationResult>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// One row in a baseline comparison report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BaselineComparisonRow {
    /// Baseline label.
    pub kind: BaselinePolicyKind,
    /// Policy digest.
    pub policy_digest: String,
    /// Primary metric value.
    pub distinct_failure_classification_count: usize,
    /// Deterministic work units.
    pub work_units: ExplorationWorkUnits,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Deterministic comparison report for one phase.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BaselineComparisonReport {
    /// Phase represented by this report.
    pub phase: ExplorationPhase,
    /// Frozen primary metric identifier.
    pub metric_id: String,
    /// Rows in stable policy order.
    pub rows: Vec<BaselineComparisonRow>,
    /// Policy selected by validation only. Assessment never changes it.
    pub validation_winner: BaselinePolicyKind,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Resumable validation checkpoint for a baseline matrix.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BaselineCampaignCheckpoint {
    /// Campaign id.
    pub campaign_id: String,
    /// Configuration digest.
    pub config_digest: String,
    /// Target corpus digest.
    pub target_corpus_digest: String,
    /// Validation records only.
    pub validation_records: Vec<BaselinePolicyRecord>,
    /// Validation-selected policy.
    pub validation_winner: BaselinePolicyKind,
    /// Validation comparison.
    pub validation_comparison: BaselineComparisonReport,
    /// Finalization marker.
    pub finalized: bool,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Complete local baseline campaign result.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct BaselineCampaignResult {
    /// Campaign id.
    pub campaign_id: String,
    /// Configuration digest.
    pub config_digest: String,
    /// Target corpus descriptor.
    pub target_corpus: LocalTargetCorpus,
    /// Baseline records.
    pub records: Vec<BaselinePolicyRecord>,
    /// Policy selected using validation only.
    pub validation_winner: BaselinePolicyKind,
    /// Validation comparison.
    pub validation_comparison: BaselineComparisonReport,
    /// Resumable checkpoint.
    pub checkpoint: BaselineCampaignCheckpoint,
    /// Assessment comparison, present only after finalization.
    #[serde(default)]
    pub assessment_comparison: Option<BaselineComparisonReport>,
    /// One-way finalization marker.
    pub finalized: bool,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Nonclaim notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Configuration for the equal-budget baseline matrix.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BaselineCampaignConfig {
    /// Stable campaign id.
    pub campaign_id: String,
    /// Exploration configuration. Equal-work mode is required.
    pub exploration: ExplorationRunConfig,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Nonclaim notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl BaselineCampaignConfig {
    /// Build an equal-budget campaign configuration.
    pub fn new(exploration: ExplorationRunConfig) -> Self {
        Self {
            campaign_id: format!("{}_baseline_matrix", exploration.run_id),
            exploration: exploration.with_equal_work_budget(true),
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
            notes: vec![
                "Baseline matrix is local strategy diagnostics only.".to_string(),
                "Assessment remains sealed until explicit finalization.".to_string(),
            ],
        }
    }

    /// Set a stable campaign id.
    pub fn with_campaign_id(mut self, campaign_id: impl Into<String>) -> Self {
        self.campaign_id = campaign_id.into();
        self
    }

    /// Validate campaign identity, equal-work mode, and baseline uniqueness.
    pub fn validate(&self) -> Result<()> {
        if self.campaign_id.trim().is_empty() {
            return Err(ZkBenchError::validation(
                "exploration.campaign.campaign_id",
                "baseline campaign id is empty",
            ));
        }
        if self.claim_boundary != EXPLORATION_CLAIM_BOUNDARY {
            return Err(ZkBenchError::validation(
                "exploration.campaign.claim_boundary",
                "baseline campaign must remain Level0DesignNote",
            ));
        }
        self.exploration.validate()?;
        if !self.exploration.equal_work_budget {
            return Err(ZkBenchError::validation(
                "exploration.campaign.equal_work_budget",
                "baseline campaign requires equal-work mode",
            ));
        }
        let policies = baseline_policy_definitions(&self.exploration)?;
        let mut digests = BTreeSet::new();
        for (kind, policy) in policies {
            if kind != BaselinePolicyKind::BeamSearch && !digests.insert(policy.digest()?) {
                return Err(ZkBenchError::validation(
                    "exploration.campaign.baselines",
                    "fixed baseline policies must have unique digests",
                ));
            }
        }
        Ok(())
    }

    /// Compute the campaign configuration digest.
    pub fn digest(&self) -> Result<String> {
        Ok(compute_artifact_digest(
            self,
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Manifest),
        )?
        .hex_digest)
    }
}

/// Equal-budget baseline campaign runner.
#[derive(Debug, Clone)]
pub struct BaselineCampaignRunner {
    config: BaselineCampaignConfig,
}

impl BaselineCampaignRunner {
    /// Validate and create a campaign runner.
    pub fn new(config: BaselineCampaignConfig) -> Result<Self> {
        config.validate()?;
        Ok(Self { config })
    }

    /// Return the campaign configuration.
    pub fn config(&self) -> &BaselineCampaignConfig {
        &self.config
    }

    /// Run all validation baselines with fresh local replays.
    pub fn run_validation(&self) -> Result<BaselineCampaignResult> {
        let corpus = LocalTargetCorpus::from_exploration_config(&self.config.exploration)?;
        let adapter = LocalTargetAdapter::new(corpus.clone())?;
        let explorer = DeterministicExplorer::new(self.config.exploration.clone())?;
        let mut records = Vec::new();
        for (kind, policy) in baseline_policy_definitions(&self.config.exploration)? {
            let (policy, beam_search_result) = if kind == BaselinePolicyKind::BeamSearch {
                let search = explorer.run_validation()?;
                let record = search.validation_frontier.records.first().ok_or_else(|| {
                    ZkBenchError::validation(
                        "exploration.campaign.beam_frontier",
                        "beam search produced an empty validation frontier",
                    )
                })?;
                (record.candidate.policy.clone(), Some(search))
            } else {
                (policy, None)
            };
            let policy_digest = policy.digest()?;
            let validation_run =
                adapter.run_policy(&explorer, &policy, ExplorationPhase::Validation)?;
            records.push(BaselinePolicyRecord {
                kind,
                policy,
                policy_digest,
                validation_run,
                assessment_run: None,
                beam_search_result,
                claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
            });
        }
        records.sort_by_key(|record| record.kind);
        validate_equal_campaign_allocations(&records, ExplorationPhase::Validation)?;
        let validation_winner = select_validation_winner(&records)?;
        let validation_comparison =
            build_comparison_report(&records, ExplorationPhase::Validation, validation_winner)?;
        let config_digest = self.config.digest()?;
        let checkpoint = BaselineCampaignCheckpoint {
            campaign_id: self.config.campaign_id.clone(),
            config_digest: config_digest.clone(),
            target_corpus_digest: corpus.target_corpus_digest.clone(),
            validation_records: records.clone(),
            validation_winner,
            validation_comparison: validation_comparison.clone(),
            finalized: false,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
        };
        let result = BaselineCampaignResult {
            campaign_id: self.config.campaign_id.clone(),
            config_digest,
            target_corpus: corpus,
            records,
            validation_winner,
            validation_comparison,
            checkpoint,
            assessment_comparison: None,
            finalized: false,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
            notes: vec![
                "Validation baselines used fresh local replays under equal work units.".to_string(),
                "Assessment case ids and outcomes are unavailable before finalization.".to_string(),
            ],
        };
        validate_baseline_campaign_result(&result, &self.config)?;
        Ok(result)
    }

    /// Resume a completed validation matrix from its checkpoint without
    /// exposing or recomputing assessment data.
    pub fn resume_validation(
        &self,
        checkpoint: BaselineCampaignCheckpoint,
    ) -> Result<BaselineCampaignResult> {
        self.validate_checkpoint(&checkpoint)?;
        if checkpoint.finalized {
            return Err(ZkBenchError::validation(
                "exploration.campaign.resume",
                "finalized baseline campaigns cannot resume validation",
            ));
        }
        let corpus = LocalTargetCorpus::from_exploration_config(&self.config.exploration)?;
        let result = BaselineCampaignResult {
            campaign_id: checkpoint.campaign_id.clone(),
            config_digest: checkpoint.config_digest.clone(),
            target_corpus: corpus,
            records: checkpoint.validation_records.clone(),
            validation_winner: checkpoint.validation_winner,
            validation_comparison: checkpoint.validation_comparison.clone(),
            checkpoint,
            assessment_comparison: None,
            finalized: false,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
            notes: vec![
                "Validation baselines used fresh local replays under equal work units.".to_string(),
                "Assessment case ids and outcomes are unavailable before finalization.".to_string(),
            ],
        };
        validate_baseline_campaign_result(&result, &self.config)?;
        Ok(result)
    }

    /// Finalize every policy once on the withheld assessment range.
    pub fn finalize_assessment(&self, result: &mut BaselineCampaignResult) -> Result<()> {
        validate_baseline_campaign_result(result, &self.config)?;
        if result.finalized || result.checkpoint.finalized {
            return Err(ZkBenchError::validation(
                "exploration.campaign.finalize_assessment",
                "baseline campaign assessment has already been finalized",
            ));
        }
        let corpus = LocalTargetCorpus::from_exploration_config(&self.config.exploration)?;
        let adapter = LocalTargetAdapter::new(corpus)?;
        let explorer = DeterministicExplorer::new(self.config.exploration.clone())?;
        let mut assessment_runs = Vec::new();
        let mut beam_search_results = Vec::new();
        for record in &result.records {
            let assessment_run = adapter.run_policy(
                &explorer,
                &record.policy,
                ExplorationPhase::FinalizedAssessment,
            )?;
            assessment_runs.push((record.kind, assessment_run));
            if let Some(search) = &record.beam_search_result {
                let mut finalized_search = search.clone();
                explorer.finalize_assessment(&mut finalized_search)?;
                beam_search_results.push((record.kind, finalized_search));
            }
        }
        for record in &mut result.records {
            record.assessment_run = Some(
                assessment_runs
                    .iter()
                    .find(|(kind, _)| *kind == record.kind)
                    .map(|(_, run)| run.clone())
                    .ok_or_else(|| {
                        ZkBenchError::validation(
                            "exploration.campaign.assessment_runs",
                            "assessment run missing for baseline policy",
                        )
                    })?,
            );
            if let Some((_, search)) = beam_search_results
                .iter()
                .find(|(kind, _)| *kind == record.kind)
            {
                record.beam_search_result = Some(search.clone());
            }
        }
        result.checkpoint.validation_records = result.records.clone();
        validate_equal_campaign_allocations(
            result.records.as_slice(),
            ExplorationPhase::FinalizedAssessment,
        )?;
        result.assessment_comparison = Some(build_comparison_report(
            &result.records,
            ExplorationPhase::FinalizedAssessment,
            result.validation_winner,
        )?);
        result.finalized = true;
        result.checkpoint.finalized = true;
        validate_baseline_campaign_result(result, &self.config)?;
        Ok(())
    }

    fn validate_checkpoint(&self, checkpoint: &BaselineCampaignCheckpoint) -> Result<()> {
        let config_digest = self.config.digest()?;
        if checkpoint.campaign_id != self.config.campaign_id
            || checkpoint.config_digest != config_digest
        {
            return Err(ZkBenchError::validation(
                "exploration.campaign.checkpoint.identity",
                "baseline checkpoint identity does not match config",
            ));
        }
        if checkpoint.claim_boundary != EXPLORATION_CLAIM_BOUNDARY {
            return Err(ZkBenchError::validation(
                "exploration.campaign.checkpoint.claim_boundary",
                "baseline checkpoint must remain Level0DesignNote",
            ));
        }
        Ok(())
    }
}

/// Serialize a baseline campaign result as deterministic local JSON.
pub fn serialize_baseline_campaign_result_json(result: &BaselineCampaignResult) -> Result<String> {
    result.target_corpus.validate()?;
    if result.claim_boundary != EXPLORATION_CLAIM_BOUNDARY {
        return Err(ZkBenchError::validation(
            "exploration.campaign.serialize.claim_boundary",
            "baseline result must remain Level0DesignNote",
        ));
    }
    serde_json::to_string_pretty(result).map_err(|error| {
        ZkBenchError::serialization("serialize_baseline_campaign_result_json", error.to_string())
    })
}

/// Deserialize and validate a baseline campaign result.
pub fn deserialize_baseline_campaign_result_json(
    json: &str,
    config: &BaselineCampaignConfig,
) -> Result<BaselineCampaignResult> {
    let result: BaselineCampaignResult = serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_baseline_campaign_result_json",
            error.to_string(),
        )
    })?;
    validate_baseline_campaign_result(&result, config)?;
    Ok(result)
}

fn baseline_policy_definitions(
    config: &ExplorationRunConfig,
) -> Result<Vec<(BaselinePolicyKind, ExplorerPolicy)>> {
    let base = ExplorerPolicy::from_config(&config.base_soak_config);
    let mut family_round_robin = base.clone();
    family_round_robin.queue_policy = QueuePolicy::RoundRobinFamilies;
    let mut mutation_round_robin = base.clone();
    mutation_round_robin.queue_policy = QueuePolicy::RoundRobinMutations;
    let mut seeded = base.clone();
    let family_shift = (config.fixed_seed as usize) % seeded.family_order.len();
    let mutation_shift =
        (config.fixed_seed as usize) % seeded.mutation_schedule.mutation_classes.len();
    seeded.family_order.rotate_left(family_shift);
    seeded
        .mutation_schedule
        .mutation_classes
        .rotate_left(mutation_shift);
    seeded.minimization_order.rotate_left(family_shift % 4);
    seeded.queue_policy = QueuePolicy::PreferFailuresOnTie;
    for policy in [&base, &family_round_robin, &mutation_round_robin, &seeded] {
        policy.validate(&config.base_soak_config)?;
    }
    Ok(vec![
        (BaselinePolicyKind::StableDigest, base),
        (BaselinePolicyKind::RoundRobinFamilies, family_round_robin),
        (
            BaselinePolicyKind::RoundRobinMutations,
            mutation_round_robin,
        ),
        (
            BaselinePolicyKind::BeamSearch,
            ExplorerPolicy::from_config(&config.base_soak_config),
        ),
        (BaselinePolicyKind::SeededControl, seeded),
    ])
}

fn build_case_observation(
    case_plan: &SoakCasePlan,
    shard_id: &SoakShardId,
    result: &SoakRunResult,
) -> Result<LocalTargetCaseObservation> {
    let replays = result
        .replay_observations
        .iter()
        .filter(|replay| replay.case_id == case_plan.id)
        .collect::<Vec<_>>();
    let case_result = result
        .case_results
        .iter()
        .find(|case| case.case_id == case_plan.id);
    let mut failures = result
        .failure_corpus_index
        .entries
        .iter()
        .filter(|entry| entry.source_soak_case_id == case_plan.id)
        .cloned()
        .collect::<Vec<_>>();
    let mut semantic_irs = Vec::new();
    let mut mutation_provenance = Vec::new();
    let mut replay_manifests = Vec::new();
    let mut replay_results = Vec::new();
    let mut oracle_outcomes = Vec::new();
    for replay in &replays {
        replay_manifests.push(replay.manifest.clone());
        replay_results.push(replay.result.clone());
        if let Some(provenance) = &replay.manifest.mutation_provenance {
            if !mutation_provenance.contains(provenance) {
                mutation_provenance.push(provenance.clone());
            }
        }
        if let Some(instance) = &replay.manifest.subject.generated_instance {
            push_unique_semantic_ir(&mut semantic_irs, &instance.semantic_ir)?;
        }
        if let Some(instance) = &replay.manifest.subject.mutated_instance {
            push_unique_semantic_ir(&mut semantic_irs, &instance.semantic_ir)?;
        }
        oracle_outcomes.extend(
            replay
                .result
                .trace_results
                .iter()
                .map(|trace| trace.local_oracle_outcome.clone()),
        );
        if let Some(classification) = replay
            .result
            .trace_results
            .iter()
            .map(|trace| trace.result_classification)
            .find(|classification| is_reproducible_failure_classification(*classification))
        {
            let mutation_class = replay
                .manifest
                .mutation_provenance
                .as_ref()
                .map(|provenance| provenance.mutation_class);
            let entry = build_failure_corpus_entry(FailureCorpusEntryInput {
                shard_id: shard_id.clone(),
                case_id: case_plan.id.clone(),
                family_kind: case_plan.family_kind,
                generator_seed: case_plan.generator_seed,
                tunables: case_plan.generator_tunables.clone(),
                mutation_class,
                trace_id: replay
                    .result
                    .trace_results
                    .iter()
                    .find(|trace| trace.result_classification == classification)
                    .map(|trace| trace.trace_id.clone()),
                failure_kind: FailureCorpusKind::OracleMismatch,
                local_error_summary: format!("local replay classification: {classification:?}"),
            });
            if !failures
                .iter()
                .any(|existing| existing.entry_id == entry.entry_id)
            {
                failures.push(entry);
            }
        }
    }
    let status = match case_result.map(|case| case.status) {
        Some(SoakCaseStatus::FailedGeneration) => TargetCaseStatus::GenerationFailure,
        Some(SoakCaseStatus::FailedReplay) if replays.is_empty() => TargetCaseStatus::ReplayFailure,
        _ if semantic_irs.is_empty() => TargetCaseStatus::Incomplete,
        _ if replay_results.is_empty() => TargetCaseStatus::ReplayFailure,
        _ => TargetCaseStatus::Complete,
    };
    let mut missing_artifacts = Vec::new();
    if semantic_irs.is_empty() {
        missing_artifacts.push("SemanticIr".to_string());
    }
    if mutation_provenance.is_empty() && !case_plan.mutation_classes.is_empty() {
        missing_artifacts.push("MutationProvenance".to_string());
    }
    if replay_manifests.is_empty() {
        missing_artifacts.push("ReplayManifest".to_string());
    }
    if replay_results.is_empty() {
        missing_artifacts.push("ReplayResult".to_string());
    }
    if oracle_outcomes.is_empty() {
        missing_artifacts.push("OracleOutcome".to_string());
    }
    let observation = LocalTargetCaseObservation {
        case_id: case_plan.id.clone(),
        shard_id: shard_id.clone(),
        family_kind: case_plan.family_kind,
        generator_seed: case_plan.generator_seed,
        mutation_attempt_count: case_plan.mutation_classes.len(),
        status,
        semantic_irs,
        mutation_provenance,
        replay_manifests,
        replay_results,
        oracle_outcomes,
        failure_corpus_entries: failures,
        missing_artifacts,
        claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
    };
    validate_case_observation(&observation)?;
    Ok(observation)
}

fn push_unique_semantic_ir(target: &mut Vec<SemanticIr>, ir: &SemanticIr) -> Result<()> {
    let digest = compute_artifact_digest(ir, Some(ArtifactKind::Other), Some(ArtifactRole::Input))?
        .hex_digest;
    for existing in target.iter() {
        let existing_digest = compute_artifact_digest(
            existing,
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Input),
        )?
        .hex_digest;
        if existing_digest == digest {
            return Ok(());
        }
    }
    target.push(ir.clone());
    Ok(())
}

fn validate_case_observation(case: &LocalTargetCaseObservation) -> Result<()> {
    if case.case_id.trim().is_empty() {
        return Err(ZkBenchError::validation(
            "exploration.target_case.case_id",
            "target case id is empty",
        ));
    }
    if case.claim_boundary != EXPLORATION_CLAIM_BOUNDARY {
        return Err(ZkBenchError::validation(
            "exploration.target_case.claim_boundary",
            "target case observation must remain Level0DesignNote",
        ));
    }
    let mut seen_manifests = BTreeSet::new();
    for (manifest, result) in case.replay_manifests.iter().zip(&case.replay_results) {
        if !seen_manifests.insert(manifest.id.clone()) {
            return Err(ZkBenchError::validation(
                "exploration.target_case.replays",
                "target case contains duplicate replay manifest ids",
            ));
        }
        if result.manifest_id != manifest.id {
            return Err(ZkBenchError::validation(
                "exploration.target_case.replays",
                "replay result does not match replay manifest",
            ));
        }
        if manifest.claim_boundary > ClaimBoundary::Level1LocalReplay
            || result.claim_boundary > ClaimBoundary::Level1LocalReplay
        {
            return Err(ZkBenchError::validation(
                "exploration.target_case.replays.claim_boundary",
                "target case replay exceeded Level1LocalReplay",
            ));
        }
    }
    if case.replay_manifests.len() != case.replay_results.len() {
        return Err(ZkBenchError::validation(
            "exploration.target_case.replays",
            "replay manifest and result counts differ",
        ));
    }
    for entry in &case.failure_corpus_entries {
        if entry.source_soak_case_id != case.case_id {
            return Err(ZkBenchError::validation(
                "exploration.target_case.failure_corpus",
                "failure corpus entry does not match target case",
            ));
        }
        if entry.triage_status == FailureTriageStatus::Quarantined
            && entry.failure_kind == FailureCorpusKind::ClaimBoundaryViolation
        {
            return Err(ZkBenchError::validation(
                "exploration.target_case.failure_corpus",
                "claim-boundary failures cannot be treated as strategy discoveries",
            ));
        }
    }
    Ok(())
}

fn build_primary_metric(
    cases: &[LocalTargetCaseObservation],
    work_units: ExplorationWorkUnits,
) -> ExplorationPrimaryMetric {
    let mut classifications = BTreeSet::new();
    for classification in cases
        .iter()
        .flat_map(|case| case.replay_results.iter())
        .flat_map(|result| result.trace_results.iter())
        .map(|trace| trace.result_classification)
    {
        if is_reproducible_failure_classification(classification) {
            classifications.insert(format!("{classification:?}"));
        }
    }
    let mut failure_classifications = Vec::new();
    for name in classifications {
        if let Some(classification) = parse_result_classification(&name) {
            failure_classifications.push(classification);
        }
    }
    failure_classifications.sort_by_key(|classification| format!("{classification:?}"));
    ExplorationPrimaryMetric {
        metric_id: PRIMARY_METRIC_ID.to_string(),
        failure_classifications,
        work_units,
        claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
    }
}

fn parse_result_classification(name: &str) -> Option<ResultClassification> {
    [
        ResultClassification::ExpectedAcceptRejected,
        ResultClassification::ExpectedRejectAcceptedUnsoundCandidate,
        ResultClassification::ExpectedRejectBackendError,
        ResultClassification::UnexpectedOutcome,
        ResultClassification::MalformedArtifact,
    ]
    .into_iter()
    .find(|classification| format!("{classification:?}") == name)
}

fn validate_equal_allocation(base: &SoakShardPlan, candidate: &SoakShardPlan) -> Result<()> {
    let base_units = plan_work_units(base, 0);
    let candidate_units = plan_work_units(candidate, 0);
    if base_units.allocation_key() != candidate_units.allocation_key() {
        return Err(ZkBenchError::validation(
            "exploration.target_run.equal_budget",
            "candidate plan changed case, shard, or mutation allocation budget",
        ));
    }
    Ok(())
}

fn plan_work_units(plan: &SoakShardPlan, replay_attempt_count: usize) -> ExplorationWorkUnits {
    ExplorationWorkUnits {
        case_count: plan.case_plans.len(),
        shard_count: plan.shard_manifests.len(),
        mutation_attempt_count: plan
            .case_plans
            .iter()
            .map(|case| case.mutation_classes.len())
            .sum(),
        replay_attempt_count,
    }
}

fn select_validation_winner(records: &[BaselinePolicyRecord]) -> Result<BaselinePolicyKind> {
    records
        .iter()
        .min_by(|left, right| compare_records(left, right))
        .map(|record| record.kind)
        .ok_or_else(|| {
            ZkBenchError::validation(
                "exploration.campaign.records",
                "baseline campaign has no policy records",
            )
        })
}

fn compare_records(
    left: &BaselinePolicyRecord,
    right: &BaselinePolicyRecord,
) -> std::cmp::Ordering {
    right
        .validation_run
        .primary_metric
        .value()
        .cmp(&left.validation_run.primary_metric.value())
        .then_with(|| left.policy_digest.cmp(&right.policy_digest))
        .then_with(|| left.kind.cmp(&right.kind))
}

fn build_comparison_report(
    records: &[BaselinePolicyRecord],
    phase: ExplorationPhase,
    validation_winner: BaselinePolicyKind,
) -> Result<BaselineComparisonReport> {
    let mut rows = Vec::new();
    for record in records {
        let run = match phase {
            ExplorationPhase::Validation => &record.validation_run,
            ExplorationPhase::FinalizedAssessment => {
                record.assessment_run.as_ref().ok_or_else(|| {
                    ZkBenchError::validation(
                        "exploration.campaign.comparison",
                        "assessment comparison requested before finalization",
                    )
                })?
            }
        };
        rows.push(BaselineComparisonRow {
            kind: record.kind,
            policy_digest: record.policy_digest.clone(),
            distinct_failure_classification_count: run.primary_metric.value(),
            work_units: run.primary_metric.work_units,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
        });
    }
    rows.sort_by_key(|row| row.kind);
    Ok(BaselineComparisonReport {
        phase,
        metric_id: PRIMARY_METRIC_ID.to_string(),
        rows,
        validation_winner,
        claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
    })
}

fn validate_equal_campaign_allocations(
    records: &[BaselinePolicyRecord],
    phase: ExplorationPhase,
) -> Result<()> {
    let Some(first) = records.first() else {
        return Err(ZkBenchError::validation(
            "exploration.campaign.records",
            "campaign records are empty",
        ));
    };
    let first_run = match phase {
        ExplorationPhase::Validation => &first.validation_run,
        ExplorationPhase::FinalizedAssessment => {
            first.assessment_run.as_ref().ok_or_else(|| {
                ZkBenchError::validation(
                    "exploration.campaign.assessment",
                    "assessment run is missing",
                )
            })?
        }
    };
    let expected = first_run.primary_metric.work_units.allocation_key();
    for record in records {
        let run = match phase {
            ExplorationPhase::Validation => &record.validation_run,
            ExplorationPhase::FinalizedAssessment => {
                record.assessment_run.as_ref().ok_or_else(|| {
                    ZkBenchError::validation(
                        "exploration.campaign.assessment",
                        "assessment run is missing",
                    )
                })?
            }
        };
        if run.primary_metric.work_units.allocation_key() != expected {
            return Err(ZkBenchError::validation(
                "exploration.campaign.equal_budget",
                "baseline records do not share equal allocation work units",
            ));
        }
    }
    Ok(())
}

fn validate_baseline_campaign_result(
    result: &BaselineCampaignResult,
    config: &BaselineCampaignConfig,
) -> Result<()> {
    config.validate()?;
    if result.campaign_id != config.campaign_id || result.config_digest != config.digest()? {
        return Err(ZkBenchError::validation(
            "exploration.campaign.result.identity",
            "baseline result identity does not match config",
        ));
    }
    if result.claim_boundary != EXPLORATION_CLAIM_BOUNDARY {
        return Err(ZkBenchError::validation(
            "exploration.campaign.result.claim_boundary",
            "baseline result must remain Level0DesignNote",
        ));
    }
    result.target_corpus.validate()?;
    if result.finalized != result.checkpoint.finalized {
        return Err(ZkBenchError::validation(
            "exploration.campaign.result.finalized",
            "result and checkpoint finalization states differ",
        ));
    }
    if result.checkpoint.campaign_id != result.campaign_id
        || result.checkpoint.config_digest != result.config_digest
        || result.checkpoint.target_corpus_digest != result.target_corpus.target_corpus_digest
        || result.checkpoint.validation_winner != result.validation_winner
        || result.checkpoint.validation_records != result.records
        || result.checkpoint.validation_comparison != result.validation_comparison
    {
        return Err(ZkBenchError::validation(
            "exploration.campaign.result.checkpoint",
            "campaign checkpoint does not match the result",
        ));
    }
    if result.assessment_comparison.is_some() != result.finalized {
        return Err(ZkBenchError::validation(
            "exploration.campaign.result.assessment_comparison",
            "assessment comparison presence does not match finalization",
        ));
    }
    if result.records.len() != 5 {
        return Err(ZkBenchError::validation(
            "exploration.campaign.result.records",
            "baseline campaign must contain exactly five policy records",
        ));
    }
    for record in &result.records {
        record
            .policy
            .validate(&config.exploration.base_soak_config)?;
        if record.claim_boundary != EXPLORATION_CLAIM_BOUNDARY
            || record.policy_digest != record.policy.digest()?
        {
            return Err(ZkBenchError::validation(
                "exploration.campaign.result.record",
                "baseline policy record identity or boundary is invalid",
            ));
        }
        record.validation_run.validate()?;
        if record.validation_run.phase != ExplorationPhase::Validation {
            return Err(ZkBenchError::validation(
                "exploration.campaign.result.validation_phase",
                "baseline validation run has the wrong phase",
            ));
        }
        if let Some(assessment) = &record.assessment_run {
            assessment.validate()?;
            if assessment.phase != ExplorationPhase::FinalizedAssessment {
                return Err(ZkBenchError::validation(
                    "exploration.campaign.result.assessment_phase",
                    "baseline assessment run has the wrong phase",
                ));
            }
        }
    }
    validate_equal_campaign_allocations(&result.records, ExplorationPhase::Validation)?;
    if result.validation_comparison.phase != ExplorationPhase::Validation
        || result.validation_comparison.rows.len() != result.records.len()
    {
        return Err(ZkBenchError::validation(
            "exploration.campaign.result.validation_comparison",
            "validation comparison is incomplete",
        ));
    }
    if result.finalized {
        validate_equal_campaign_allocations(
            &result.records,
            ExplorationPhase::FinalizedAssessment,
        )?;
        let assessment = result.assessment_comparison.as_ref().ok_or_else(|| {
            ZkBenchError::validation(
                "exploration.campaign.result.assessment_comparison",
                "finalized result is missing assessment comparison",
            )
        })?;
        if assessment.phase != ExplorationPhase::FinalizedAssessment
            || assessment.rows.len() != result.records.len()
        {
            return Err(ZkBenchError::validation(
                "exploration.campaign.result.assessment_comparison",
                "assessment comparison is incomplete",
            ));
        }
    } else if result.records.iter().any(|record| {
        record.assessment_run.is_some()
            || record
                .beam_search_result
                .as_ref()
                .is_some_and(|search| search.finalized)
    }) {
        return Err(ZkBenchError::validation(
            "exploration.campaign.result.assessment_sealing",
            "assessment data is present before campaign finalization",
        ));
    }
    Ok(())
}

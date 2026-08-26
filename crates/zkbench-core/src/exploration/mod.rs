//! Antithesis-inspired deterministic exploration for the local benchmark OS.
//!
//! This module is the named state slice
//! `antithesis-inspired-deterministic-exploration-v1`. It implements a
//! bounded, deterministic outer loop over local explorer policies. Policies
//! are proposal data only: Semantic IR, local replay, evidence, and claim
//! boundaries remain authoritative elsewhere in the crate.
//!
//! No network, provider, model, process, wall-clock, or external-runner
//! behavior is represented here. Exploration artifacts remain local
//! `Level0DesignNote` artifacts; the replay artifacts referenced by an
//! observation retain their existing `Level1LocalReplay` ceiling.

use std::collections::{BTreeMap, BTreeSet};
use std::fmt::Write as _;

use serde::{Deserialize, Serialize};

use crate::adapters::LocalJsonAdapter;
use crate::dsl::OracleOutcome;
use crate::error::{Result, ZkBenchError};
use crate::evidence::{
    compute_artifact_digest, ArtifactKind, ArtifactRole, ClaimBoundary, ExpectedVerdict,
    ResultClassification,
};
use crate::generator::FamilyKind;
use crate::mutation::MutationClass;
use crate::replay::{ReplayFailureMode, ReplayManifest, ReplayResult, ReplayStatus};
use crate::soak::{
    plan_soak_shards, validate_soak_shard_plan, LocalSoakRunner, MockTelemetryClock,
    SoakCaseStatus, SoakReplayObservation, SoakRunConfig, SoakRunRequest, SoakSeedRange,
    SoakShardPlan,
};

mod campaign;
mod operator;
mod suite;
mod suite_operator;

pub use campaign::*;
pub use operator::*;
pub use suite::*;
pub use suite_operator::*;

/// Named state slice for this module.
pub const EXPLORATION_STATE_SLICE: &str = "antithesis-inspired-deterministic-exploration-v1";

/// Exploration artifact schema version.
pub const EXPLORATION_SCHEMA_VERSION: &str = "antithesis-inspired-exploration-v1";

/// Exploration artifacts never exceed this claim boundary.
pub const EXPLORATION_CLAIM_BOUNDARY: ClaimBoundary = ClaimBoundary::Level0DesignNote;

/// Validation or held-out assessment phase.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ExplorationPhase {
    /// Candidate evolution phase.
    Validation,
    /// Explicitly finalized held-out phase.
    FinalizedAssessment,
}

/// Reason a bounded exploration run stopped before its configured budget.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum EarlyStopReason {
    /// No valid candidate was available to continue the frontier.
    NoValidCandidates,
    /// The frontier stopped producing new candidate policies.
    Converged,
    /// The configured iteration budget was consumed.
    BudgetExhausted,
    /// The run was finalized and cannot evolve further.
    Finalized,
}

/// Deterministic queue tie-break policy. The hard guidance order remains
/// validity, coverage, novelty, failures, then cost; this policy only orders
/// otherwise equivalent candidates and proposal traversal.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum QueuePolicy {
    /// Preserve canonical digest order.
    StableDigest,
    /// Traverse families in policy order before digest order.
    RoundRobinFamilies,
    /// Traverse mutation classes in policy order before digest order.
    RoundRobinMutations,
    /// Prefer candidates with more local failure signatures after the hard
    /// guidance vector is tied.
    PreferFailuresOnTie,
}

/// Fixed reducer ordering available to an explorer policy.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum MinimizationStep {
    /// Reduce the generator seed domain.
    ReduceSeedRange,
    /// Isolate one generated family.
    IsolateFamily,
    /// Isolate one mutation pass.
    IsolateMutation,
    /// Isolate one trace.
    IsolateTrace,
}

/// Mutation allocation policy searched by the outer loop.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MutationSchedule {
    /// Mutation classes in deterministic proposal order.
    pub mutation_classes: Vec<MutationClass>,
    /// Maximum classes retained by a candidate schedule.
    pub max_mutations_per_case: usize,
}

impl MutationSchedule {
    /// Build a schedule from the base mutation selection.
    pub fn from_config(config: &SoakRunConfig) -> Self {
        Self {
            mutation_classes: config.normalized_mutations(),
            max_mutations_per_case: config.normalized_mutations().len(),
        }
    }

    /// Return classes with stable first-seen de-duplication and the configured
    /// per-case limit.
    pub fn normalized_classes(&self) -> Vec<MutationClass> {
        let mut seen = BTreeSet::new();
        self.mutation_classes
            .iter()
            .copied()
            .filter(|class| seen.insert(*class))
            .take(self.max_mutations_per_case)
            .collect()
    }
}

/// Deterministic explorer policy.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExplorerPolicy {
    /// Families traversed by this policy.
    pub family_order: Vec<FamilyKind>,
    /// Mutation allocation and order.
    pub mutation_schedule: MutationSchedule,
    /// Queue tie-break policy.
    pub queue_policy: QueuePolicy,
    /// Reducer order.
    pub minimization_order: Vec<MinimizationStep>,
}

impl ExplorerPolicy {
    /// Build the baseline policy from a local soak config.
    pub fn from_config(config: &SoakRunConfig) -> Self {
        Self {
            family_order: config.normalized_families(),
            mutation_schedule: MutationSchedule::from_config(config),
            queue_policy: QueuePolicy::StableDigest,
            minimization_order: vec![
                MinimizationStep::ReduceSeedRange,
                MinimizationStep::IsolateFamily,
                MinimizationStep::IsolateMutation,
                MinimizationStep::IsolateTrace,
            ],
        }
    }

    /// Compute the deterministic policy digest.
    pub fn digest(&self) -> Result<String> {
        Ok(compute_artifact_digest(
            self,
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Manifest),
        )?
        .hex_digest)
    }

    /// Validate that a policy remains inside the base soak scope.
    pub fn validate(&self, config: &SoakRunConfig) -> Result<()> {
        let base_families = config
            .normalized_families()
            .into_iter()
            .collect::<BTreeSet<_>>();
        let policy_families = self.family_order.iter().copied().collect::<BTreeSet<_>>();
        if self.family_order.is_empty() {
            return Err(ZkBenchError::validation(
                "exploration.policy.family_order",
                "policy must select at least one family",
            ));
        }
        if policy_families.len() != self.family_order.len() {
            return Err(ZkBenchError::validation(
                "exploration.policy.family_order",
                "policy family order contains duplicates",
            ));
        }
        if !policy_families.is_subset(&base_families) {
            return Err(ZkBenchError::validation(
                "exploration.policy.family_order",
                "policy selected a family outside the base soak scope",
            ));
        }

        let base_mutations = config
            .normalized_mutations()
            .into_iter()
            .collect::<BTreeSet<_>>();
        let classes = self.mutation_schedule.normalized_classes();
        if classes.is_empty() {
            return Err(ZkBenchError::validation(
                "exploration.policy.mutation_schedule",
                "policy must select at least one mutation class",
            ));
        }
        if self.mutation_schedule.max_mutations_per_case == 0 {
            return Err(ZkBenchError::validation(
                "exploration.policy.mutation_schedule.max_mutations_per_case",
                "mutation schedule limit must be positive",
            ));
        }
        if !classes.iter().all(|class| base_mutations.contains(class)) {
            return Err(ZkBenchError::validation(
                "exploration.policy.mutation_schedule",
                "policy selected a mutation class outside the base soak scope",
            ));
        }

        let mut minimization_steps = BTreeSet::new();
        for step in &self.minimization_order {
            if !minimization_steps.insert(*step) {
                return Err(ZkBenchError::validation(
                    "exploration.policy.minimization_order",
                    "minimization order contains duplicates",
                ));
            }
        }
        if minimization_steps.len() != 4 {
            return Err(ZkBenchError::validation(
                "exploration.policy.minimization_order",
                "minimization order must contain every reducer step exactly once",
            ));
        }
        Ok(())
    }

    fn with_family_order(mut self, family_order: Vec<FamilyKind>) -> Self {
        self.family_order = family_order;
        self
    }

    fn with_mutation_order(mut self, mutation_classes: Vec<MutationClass>) -> Self {
        self.mutation_schedule.mutation_classes = mutation_classes;
        self
    }

    fn candidate_soak_config(
        &self,
        base: &SoakRunConfig,
        seed_range: SoakSeedRange,
    ) -> SoakRunConfig {
        base.clone()
            .with_families(self.family_order.clone())
            .with_mutation_passes(self.mutation_schedule.normalized_classes())
            .with_seed_range(seed_range.start_inclusive..seed_range.end_exclusive)
            .with_output_policy(crate::soak::SoakOutputPolicy::NoPacks)
    }
}

/// Run configuration for one bounded deterministic exploration.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExplorationRunConfig {
    /// Stable logical run id.
    pub run_id: String,
    /// Base local soak configuration. Its seed range is split into validation
    /// and assessment domains without serializing assessment case ids.
    pub base_soak_config: SoakRunConfig,
    /// Number of seeds exposed to validation.
    pub validation_seed_count: usize,
    /// Number of seeds withheld for final assessment.
    pub assessment_seed_count: usize,
    /// Maximum cases each policy may execute in each phase. Zero means the
    /// complete phase plan, preserving the original v1 behavior.
    #[serde(default)]
    pub case_budget: usize,
    /// Maximum retained beam width.
    pub beam_width: usize,
    /// Number of proposal iterations after baseline evaluation.
    pub iteration_budget: usize,
    /// Maximum proposals evaluated per iteration.
    pub candidate_budget_per_iteration: usize,
    /// Fixed deterministic proposal seed.
    pub fixed_seed: u64,
    /// When true, beam proposals retain the base family and mutation counts
    /// so campaign comparisons use equal deterministic allocation budgets.
    #[serde(default)]
    pub equal_work_budget: bool,
    /// Claim boundary for exploration metadata.
    pub claim_boundary: ClaimBoundary,
    /// Nonclaim notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl Default for ExplorationRunConfig {
    fn default() -> Self {
        Self::new(SoakRunConfig::smoke())
    }
}

impl ExplorationRunConfig {
    /// Create a small exploration config using a two-way seed split.
    pub fn new(base_soak_config: SoakRunConfig) -> Self {
        let total = base_soak_config.scope.seed_range.len();
        let validation = total / 2;
        Self {
            run_id: "local_exploration_smoke".to_string(),
            base_soak_config,
            validation_seed_count: validation,
            assessment_seed_count: total.saturating_sub(validation),
            case_budget: 0,
            beam_width: 2,
            iteration_budget: 1,
            candidate_budget_per_iteration: 4,
            fixed_seed: 0,
            equal_work_budget: false,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
            notes: vec![
                "Exploration is local deterministic guidance metadata only.".to_string(),
                "Assessment data is logically sealed until explicit finalization.".to_string(),
            ],
        }
    }

    /// Set the logical run id.
    pub fn with_run_id(mut self, run_id: impl Into<String>) -> Self {
        self.run_id = run_id.into();
        self
    }

    /// Set budgets and fixed proposal seed.
    pub fn with_budgets(
        mut self,
        beam_width: usize,
        iteration_budget: usize,
        candidate_budget_per_iteration: usize,
        fixed_seed: u64,
    ) -> Self {
        self.beam_width = beam_width;
        self.iteration_budget = iteration_budget;
        self.candidate_budget_per_iteration = candidate_budget_per_iteration;
        self.fixed_seed = fixed_seed;
        self
    }

    /// Set the deterministic per-phase case budget. Zero retains every
    /// planned case; a positive value selects the first cases after the
    /// policy's deterministic queue ordering.
    pub fn with_case_budget(mut self, case_budget: usize) -> Self {
        self.case_budget = case_budget;
        self
    }

    /// Require proposal policies to retain the base family and mutation
    /// allocation counts for equal-budget campaign comparisons.
    pub fn with_equal_work_budget(mut self, equal_work_budget: bool) -> Self {
        self.equal_work_budget = equal_work_budget;
        self
    }

    /// Compute the configuration digest used for the seed split and resume
    /// validation.
    pub fn digest(&self) -> Result<String> {
        Ok(compute_artifact_digest(
            self,
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Manifest),
        )?
        .hex_digest)
    }

    /// Validate the configuration and its closed seed partition.
    pub fn validate(&self) -> Result<()> {
        if self.run_id.trim().is_empty() {
            return Err(ZkBenchError::validation(
                "exploration.run_id",
                "run id is empty",
            ));
        }
        self.base_soak_config.validate()?;
        if self.claim_boundary != EXPLORATION_CLAIM_BOUNDARY {
            return Err(ZkBenchError::validation(
                "exploration.claim_boundary",
                "exploration metadata must remain Level0DesignNote",
            ));
        }
        let total = self.base_soak_config.scope.seed_range.len();
        if total < 2 {
            return Err(ZkBenchError::validation(
                "exploration.seed_split",
                "at least two base seeds are required for a sealed split",
            ));
        }
        if self.validation_seed_count == 0 || self.assessment_seed_count == 0 {
            return Err(ZkBenchError::validation(
                "exploration.seed_split",
                "validation and assessment domains must both be non-empty",
            ));
        }
        if self.validation_seed_count + self.assessment_seed_count != total {
            return Err(ZkBenchError::validation(
                "exploration.seed_split",
                "validation and assessment counts must cover the base seed range exactly",
            ));
        }
        if self.case_budget > 0 {
            let family_count = self.base_soak_config.normalized_families().len();
            let validation_cases = family_count.saturating_mul(self.validation_seed_count);
            let assessment_cases = family_count.saturating_mul(self.assessment_seed_count);
            if self.case_budget > validation_cases || self.case_budget > assessment_cases {
                return Err(ZkBenchError::validation(
                    "exploration.case_budget",
                    "case budget must fit both validation and assessment phase plans",
                ));
            }
        }
        if self.beam_width == 0 {
            return Err(ZkBenchError::validation(
                "exploration.beam_width",
                "beam width must be positive",
            ));
        }
        if self.candidate_budget_per_iteration == 0 {
            return Err(ZkBenchError::validation(
                "exploration.candidate_budget_per_iteration",
                "candidate budget must be positive",
            ));
        }
        Ok(())
    }

    /// Return the validation seed range. The range is selected from the
    /// configuration digest; assessment ids are not exposed here.
    pub fn validation_seed_range(&self) -> Result<SoakSeedRange> {
        self.validate()?;
        let start = self.base_soak_config.scope.seed_range.start_inclusive;
        let validation_first = self.digest()?.as_bytes()[0] % 2 == 0;
        let split = if validation_first {
            start + self.validation_seed_count as u64
        } else {
            start + self.assessment_seed_count as u64
        };
        if validation_first {
            Ok(SoakSeedRange::new(start, split))
        } else {
            Ok(SoakSeedRange::new(
                split,
                start + self.validation_seed_count as u64 + self.assessment_seed_count as u64,
            ))
        }
    }

    fn assessment_seed_range(&self) -> Result<SoakSeedRange> {
        self.validate()?;
        let start = self.base_soak_config.scope.seed_range.start_inclusive;
        let validation_first = self.digest()?.as_bytes()[0] % 2 == 0;
        if validation_first {
            Ok(SoakSeedRange::new(
                start + self.validation_seed_count as u64,
                start + self.validation_seed_count as u64 + self.assessment_seed_count as u64,
            ))
        } else {
            Ok(SoakSeedRange::new(
                start,
                start + self.assessment_seed_count as u64,
            ))
        }
    }

    fn candidate_config(
        &self,
        policy: &ExplorerPolicy,
        phase: ExplorationPhase,
    ) -> Result<SoakRunConfig> {
        let seed_range = match phase {
            ExplorationPhase::Validation => self.validation_seed_range()?,
            ExplorationPhase::FinalizedAssessment => self.assessment_seed_range()?,
        };
        policy.validate(&self.base_soak_config)?;
        Ok(policy.candidate_soak_config(&self.base_soak_config, seed_range))
    }

    fn candidate_plan(
        &self,
        policy: &ExplorerPolicy,
        phase: ExplorationPhase,
    ) -> Result<SoakShardPlan> {
        let config = self.candidate_config(policy, phase)?;
        let plan = plan_soak_shards(config)?;
        apply_policy_schedule(plan, policy, self.case_budget)
    }
}

/// Semantic and replay observations used by guidance. No timing or backend
/// performance fields are present by construction.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GuidanceObservation {
    /// Number of case results observed.
    pub case_count: usize,
    /// Number of completed case results.
    pub completed_case_count: usize,
    /// Number of failed case results.
    pub failed_case_count: usize,
    /// Number of replay result ids observed.
    pub replay_result_count: usize,
    /// Families covered by the policy.
    pub covered_families: Vec<FamilyKind>,
    /// Mutation classes covered by the policy.
    pub covered_mutations: Vec<String>,
    /// Stable replay/oracle behavior signatures.
    pub replay_signatures: Vec<String>,
    /// Stable local failure signatures.
    pub failure_signatures: Vec<String>,
    /// Replay result references retained for local triage.
    pub replay_result_ids: Vec<String>,
    /// Case ids retained for local replay lookup.
    pub case_ids: Vec<String>,
    /// Exact local replay trace observations used for semantic guidance.
    #[serde(default)]
    pub replay_trace_observations: Vec<ReplayTraceObservation>,
    /// Claim boundary of the observed local results.
    pub claim_boundary: ClaimBoundary,
}

impl Default for GuidanceObservation {
    fn default() -> Self {
        Self {
            case_count: 0,
            completed_case_count: 0,
            failed_case_count: 0,
            replay_result_count: 0,
            covered_families: Vec::new(),
            covered_mutations: Vec::new(),
            replay_signatures: Vec::new(),
            failure_signatures: Vec::new(),
            replay_result_ids: Vec::new(),
            case_ids: Vec::new(),
            replay_trace_observations: Vec::new(),
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
        }
    }
}

/// Exact semantic and replay facts retained from one local replay trace.
///
/// The observation deliberately carries oracle and classification outcomes,
/// not timing, backend-performance telemetry, model output, network data, or
/// authority to mutate evidence.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReplayTraceObservation {
    /// Replay manifest id.
    pub replay_manifest_id: String,
    /// Replay result id.
    pub replay_result_id: String,
    /// Replay status.
    pub replay_status: ReplayStatus,
    /// Replay failure mode.
    pub replay_failure_mode: ReplayFailureMode,
    /// Trace id.
    pub trace_id: String,
    /// Expected verdict declared by the replay manifest.
    pub expected_verdict: ExpectedVerdict,
    /// Local semantic oracle outcome.
    pub local_oracle_outcome: OracleOutcome,
    /// Local result classification.
    pub result_classification: ResultClassification,
    /// Claim boundary of the underlying local replay.
    pub claim_boundary: ClaimBoundary,
}

/// Lexicographic guidance vector. Validity is a hard gate; cost is minimized
/// only after all preceding fields tie.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct GuidanceVector {
    /// Hard validity gate.
    pub valid: bool,
    /// Family plus mutation coverage count.
    pub coverage: usize,
    /// Number of signatures new to the prior frontier.
    pub novelty: usize,
    /// Distinct failure signature count.
    pub failures: usize,
    /// Replay/case work estimate. Lower is preferred.
    pub cost: usize,
}

impl Default for GuidanceVector {
    fn default() -> Self {
        Self {
            valid: false,
            coverage: 0,
            novelty: 0,
            failures: 0,
            cost: usize::MAX,
        }
    }
}

impl Ord for GuidanceVector {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        self.valid
            .cmp(&other.valid)
            .then_with(|| self.coverage.cmp(&other.coverage))
            .then_with(|| self.novelty.cmp(&other.novelty))
            .then_with(|| self.failures.cmp(&other.failures))
            .then_with(|| other.cost.cmp(&self.cost))
    }
}

impl PartialOrd for GuidanceVector {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

/// Candidate policy proposal and lineage metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExplorationCandidate {
    /// Stable candidate id derived from policy and lineage.
    pub candidate_id: String,
    /// Parent candidate id, when this is not the baseline.
    #[serde(default)]
    pub parent_candidate_id: Option<String>,
    /// Proposal iteration.
    pub iteration: usize,
    /// Policy data.
    pub policy: ExplorerPolicy,
    /// Policy digest.
    pub policy_digest: String,
    /// Fixed deterministic proposal operator label.
    pub proposal_operator: String,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Deterministic failure-reducer input.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FailureReductionInput {
    /// Original replay manifest id. It is never replaced by the reducer.
    pub replay_manifest_id: String,
    /// Failure classification to preserve.
    pub failure_classification: String,
    /// Ordered reduction steps or trace tokens.
    pub steps: Vec<String>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Deterministic failure-reducer result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FailureReductionResult {
    /// Original replay manifest id.
    pub replay_manifest_id: String,
    /// Preserved failure classification.
    pub failure_classification: String,
    /// Reduced ordered steps.
    pub retained_steps: Vec<String>,
    /// Number of attempted removals.
    pub attempted_removals: usize,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Reduce a failure sequence in fixed order. The caller supplies the local
/// replay predicate; a removal is accepted only when the same classification
/// remains true. This keeps the reducer independent of any backend or
/// process-execution authority.
pub fn reduce_failure_sequence<F>(
    input: &FailureReductionInput,
    mut preserves_failure: F,
) -> Result<FailureReductionResult>
where
    F: FnMut(&[String], &str) -> bool,
{
    validate_failure_reduction_input(input)?;
    let mut retained_steps = input.steps.clone();
    let mut attempted_removals: usize = 0;
    let mut index = 0;
    while index < retained_steps.len() {
        attempted_removals = attempted_removals.saturating_add(1);
        let mut candidate = retained_steps.clone();
        candidate.remove(index);
        if preserves_failure(&candidate, &input.failure_classification) {
            retained_steps = candidate;
        } else {
            index += 1;
        }
    }
    Ok(FailureReductionResult {
        replay_manifest_id: input.replay_manifest_id.clone(),
        failure_classification: input.failure_classification.clone(),
        retained_steps,
        attempted_removals,
        claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
    })
}

/// Reduce a real local replay failure by removing selected traces in stable
/// order and replaying the reduced manifest through the local JSON adapter.
///
/// The original manifest id is retained, and a reduction is accepted only if
/// at least one reduced trace reports the exact same classification. The
/// adapter emits in-memory local records only; this function cannot append
/// evidence or modify oracle semantics.
pub fn reduce_local_replay_failure(
    manifest: &ReplayManifest,
    result: &ReplayResult,
    failure_classification: ResultClassification,
) -> Result<FailureReductionResult> {
    if result.manifest_id != manifest.id {
        return Err(ZkBenchError::validation(
            "exploration.failure_reduction.replay_result",
            "replay result manifest id does not match the supplied manifest",
        ));
    }
    let classification = format!("{failure_classification:?}");
    if !result
        .trace_results
        .iter()
        .any(|trace| trace.result_classification == failure_classification)
    {
        return Err(ZkBenchError::validation(
            "exploration.failure_reduction.failure_classification",
            "requested classification is absent from the replay result",
        ));
    }
    let input = FailureReductionInput {
        replay_manifest_id: manifest.id.clone(),
        failure_classification: classification.clone(),
        steps: result
            .trace_results
            .iter()
            .map(|trace| trace.trace_id.clone())
            .collect(),
        claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
    };
    reduce_failure_sequence(&input, |retained_steps, expected_classification| {
        if retained_steps.is_empty() {
            return false;
        }
        let mut reduced_manifest = manifest.clone();
        reduced_manifest
            .selected_traces
            .retain(|trace| retained_steps.iter().any(|step| step == &trace.trace_id));
        reduced_manifest
            .expected_outcomes
            .retain(|outcome| retained_steps.iter().any(|step| step == &outcome.trace_id));
        let Ok(reduced_result) = LocalJsonAdapter::default().replay(&reduced_manifest) else {
            return false;
        };
        reduced_result
            .trace_results
            .iter()
            .any(|trace| format!("{:?}", trace.result_classification) == expected_classification)
    })
}

fn validate_failure_reduction_input(input: &FailureReductionInput) -> Result<()> {
    if input.replay_manifest_id.trim().is_empty() {
        return Err(ZkBenchError::validation(
            "exploration.failure_reduction.replay_manifest_id",
            "replay manifest id is empty",
        ));
    }
    if input.failure_classification.trim().is_empty() {
        return Err(ZkBenchError::validation(
            "exploration.failure_reduction.failure_classification",
            "failure classification is empty",
        ));
    }
    if input.claim_boundary != EXPLORATION_CLAIM_BOUNDARY {
        return Err(ZkBenchError::validation(
            "exploration.failure_reduction.claim_boundary",
            "failure reduction must remain Level0DesignNote",
        ));
    }
    Ok(())
}

/// Candidate evaluation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CandidateEvaluation {
    /// Candidate id.
    pub candidate_id: String,
    /// Phase in which the candidate was evaluated.
    pub phase: ExplorationPhase,
    /// Hard validity result.
    pub valid: bool,
    /// Lexicographic guidance vector.
    pub guidance: GuidanceVector,
    /// Semantic and replay observations.
    pub observation: GuidanceObservation,
    /// Rejection reason when invalid.
    #[serde(default)]
    pub rejection_reason: Option<String>,
    /// Local failure reductions.
    #[serde(default)]
    pub failure_reductions: Vec<FailureReductionResult>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Candidate plus evaluation retained in full lineage.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExplorationLineageRecord {
    /// Candidate proposal.
    pub candidate: ExplorationCandidate,
    /// Candidate evaluation.
    pub evaluation: CandidateEvaluation,
}

/// Current bounded beam frontier.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExplorationFrontier {
    /// Frontier iteration.
    pub iteration: usize,
    /// Selected candidate records in rank order.
    pub records: Vec<ExplorationLineageRecord>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Post-finalization comparison of the selected validation candidate with its
/// sealed assessment evaluation. This is a local diagnostic, not a score or
/// evidence record; it cannot exist before explicit assessment finalization.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExplorationAssessmentReport {
    /// Candidate selected from the validation frontier.
    pub candidate_id: String,
    /// Guidance observed during validation.
    pub validation_guidance: GuidanceVector,
    /// Guidance observed during the sealed assessment replay.
    pub assessment_guidance: GuidanceVector,
    /// Whether the hard validity result changed between phases.
    pub validity_changed: bool,
    /// Assessment coverage minus validation coverage.
    pub coverage_delta: i64,
    /// Assessment novelty minus validation novelty.
    pub novelty_delta: i64,
    /// Assessment failures minus validation failures.
    pub failures_delta: i64,
    /// Assessment replay/case cost minus validation replay/case cost.
    pub cost_delta: i64,
    /// Digest of the validation semantic/replay observation.
    pub validation_observation_digest: String,
    /// Digest of the assessment semantic/replay observation.
    pub assessment_observation_digest: String,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

impl ExplorationAssessmentReport {
    fn from_evaluations(
        validation: &CandidateEvaluation,
        assessment: &CandidateEvaluation,
    ) -> Result<Self> {
        if validation.candidate_id != assessment.candidate_id {
            return Err(ZkBenchError::validation(
                "exploration.assessment_report.candidate_id",
                "validation and assessment evaluations must belong to the same candidate",
            ));
        }
        Ok(Self {
            candidate_id: validation.candidate_id.clone(),
            validation_guidance: validation.guidance,
            assessment_guidance: assessment.guidance,
            validity_changed: validation.valid != assessment.valid,
            coverage_delta: signed_delta(
                assessment.guidance.coverage,
                validation.guidance.coverage,
            ),
            novelty_delta: signed_delta(assessment.guidance.novelty, validation.guidance.novelty),
            failures_delta: signed_delta(
                assessment.guidance.failures,
                validation.guidance.failures,
            ),
            cost_delta: signed_delta(assessment.guidance.cost, validation.guidance.cost),
            validation_observation_digest: guidance_observation_digest(&validation.observation)?,
            assessment_observation_digest: guidance_observation_digest(&assessment.observation)?,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
        })
    }

    fn validate_against(
        &self,
        validation: &CandidateEvaluation,
        assessment: &CandidateEvaluation,
    ) -> Result<()> {
        let expected = Self::from_evaluations(validation, assessment)?;
        if self != &expected {
            return Err(ZkBenchError::validation(
                "exploration.assessment_report.integrity",
                "assessment report does not match its validation and assessment evaluations",
            ));
        }
        Ok(())
    }
}

/// Resumable exploration checkpoint.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExplorationCheckpoint {
    /// Logical run id.
    pub run_id: String,
    /// Configuration digest.
    pub config_digest: String,
    /// Next proposal iteration to evaluate.
    pub next_iteration: usize,
    /// Current validation frontier.
    pub frontier: ExplorationFrontier,
    /// Full candidate lineage.
    pub lineage: Vec<ExplorationLineageRecord>,
    /// Signatures already observed by the frontier.
    #[serde(default)]
    pub seen_signatures: Vec<String>,
    /// Whether assessment finalization has occurred.
    pub finalized: bool,
    /// Final assessment result, present only after finalization.
    #[serde(default)]
    pub assessment_evaluation: Option<CandidateEvaluation>,
    /// Validation-versus-assessment diagnostic, present only after finalization.
    #[serde(default)]
    pub assessment_report: Option<ExplorationAssessmentReport>,
    /// Early-stop status.
    #[serde(default)]
    pub early_stop_reason: Option<EarlyStopReason>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Complete local exploration result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExplorationResult {
    /// Logical run id.
    pub run_id: String,
    /// Configuration digest.
    pub config_digest: String,
    /// Final validation frontier.
    pub validation_frontier: ExplorationFrontier,
    /// Full candidate lineage.
    pub lineage: Vec<ExplorationLineageRecord>,
    /// Resumable checkpoint.
    pub checkpoint: ExplorationCheckpoint,
    /// Final assessment result after explicit finalization.
    #[serde(default)]
    pub assessment_evaluation: Option<CandidateEvaluation>,
    /// Validation-versus-assessment diagnostic, present only after finalization.
    #[serde(default)]
    pub assessment_report: Option<ExplorationAssessmentReport>,
    /// Whether assessment finalization occurred.
    pub finalized: bool,
    /// Early-stop status.
    #[serde(default)]
    pub early_stop_reason: Option<EarlyStopReason>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Versioned exploration sidecar for existing local soak report bundles.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExplorationArtifact {
    /// Schema version.
    pub schema_version: String,
    /// Named state slice.
    pub state_slice: String,
    /// Complete exploration result.
    pub result: ExplorationResult,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Nonclaim notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl ExplorationArtifact {
    /// Build an artifact from a result.
    pub fn from_result(result: ExplorationResult) -> Self {
        Self {
            schema_version: EXPLORATION_SCHEMA_VERSION.to_string(),
            state_slice: EXPLORATION_STATE_SLICE.to_string(),
            result,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
            notes: vec![
                "Exploration artifact is local guidance metadata only.".to_string(),
                "No accepted evidence or backend-performance claim is represented.".to_string(),
            ],
        }
    }
}

/// Deterministic local explorer and bounded beam optimizer.
#[derive(Debug, Clone)]
pub struct DeterministicExplorer {
    config: ExplorationRunConfig,
}

impl DeterministicExplorer {
    /// Validate and create an explorer.
    pub fn new(config: ExplorationRunConfig) -> Result<Self> {
        config.validate()?;
        Ok(Self { config })
    }

    /// Return the run configuration.
    pub fn config(&self) -> &ExplorationRunConfig {
        &self.config
    }

    /// Build the deterministic validation shard plan for one policy. This is
    /// an inspection API for schedule replay; it does not run a case.
    pub fn plan_validation_shards(&self, policy: &ExplorerPolicy) -> Result<SoakShardPlan> {
        self.plan_shards(policy, ExplorationPhase::Validation)
    }

    /// Build a deterministic shard plan for an internal exploration phase.
    ///
    /// Assessment plans are intentionally crate-visible only. Public callers
    /// must reach assessment data through `finalize_assessment`, which keeps
    /// withheld case ids and outcomes behind the one-way finalization boundary.
    pub(crate) fn plan_shards(
        &self,
        policy: &ExplorerPolicy,
        phase: ExplorationPhase,
    ) -> Result<SoakShardPlan> {
        self.config.candidate_plan(policy, phase)
    }

    /// Run the complete validation budget.
    pub fn run_validation(&self) -> Result<ExplorationResult> {
        self.run_validation_with_iteration_limit(self.config.iteration_budget + 1)
    }

    /// Run validation up to, but not including, an iteration limit. This is a
    /// deterministic interruption seam used for checkpoint/resume tests.
    pub fn run_validation_with_iteration_limit(
        &self,
        iteration_limit: usize,
    ) -> Result<ExplorationResult> {
        self.run_loop(None, iteration_limit.min(self.config.iteration_budget + 1))
    }

    /// Resume validation from a checkpoint. Finalized checkpoints are
    /// rejected and cannot evolve further under the same run id.
    pub fn resume_validation(
        &self,
        checkpoint: ExplorationCheckpoint,
    ) -> Result<ExplorationResult> {
        self.validate_checkpoint(&checkpoint)?;
        if checkpoint.finalized {
            return Err(ZkBenchError::validation(
                "exploration.checkpoint.finalized",
                "finalized exploration runs cannot resume validation",
            ));
        }
        self.run_loop(Some(checkpoint), self.config.iteration_budget + 1)
    }

    /// Finalize the best validation candidate exactly once on the withheld
    /// assessment range.
    pub fn finalize_assessment(&self, result: &mut ExplorationResult) -> Result<()> {
        self.validate_result(result)?;
        if result.finalized || result.checkpoint.finalized {
            return Err(ZkBenchError::validation(
                "exploration.finalize_assessment",
                "assessment has already been finalized",
            ));
        }
        let record = result.validation_frontier.records.first().ok_or_else(|| {
            ZkBenchError::validation(
                "exploration.finalize_assessment.frontier",
                "cannot finalize without a validation frontier",
            )
        })?;
        let evaluation = self.evaluate_candidate(
            &record.candidate,
            ExplorationPhase::FinalizedAssessment,
            &BTreeSet::new(),
        )?;
        let assessment_report =
            ExplorationAssessmentReport::from_evaluations(&record.evaluation, &evaluation)?;
        result.assessment_evaluation = Some(evaluation.clone());
        result.assessment_report = Some(assessment_report.clone());
        result.finalized = true;
        result.checkpoint.finalized = true;
        result.checkpoint.assessment_evaluation = Some(evaluation);
        result.checkpoint.assessment_report = Some(assessment_report);
        result.checkpoint.early_stop_reason = Some(EarlyStopReason::Finalized);
        result.early_stop_reason = Some(EarlyStopReason::Finalized);
        self.validate_result(result)?;
        Ok(())
    }

    fn run_loop(
        &self,
        checkpoint: Option<ExplorationCheckpoint>,
        iteration_limit: usize,
    ) -> Result<ExplorationResult> {
        let config_digest = self.config.digest()?;
        let (mut frontier, mut lineage, mut seen_signatures, mut next_iteration) =
            if let Some(checkpoint) = checkpoint {
                (
                    checkpoint.frontier,
                    checkpoint.lineage,
                    checkpoint
                        .seen_signatures
                        .into_iter()
                        .collect::<BTreeSet<_>>(),
                    checkpoint.next_iteration,
                )
            } else {
                let baseline = self.baseline_candidate()?;
                let record =
                    self.evaluate_record(baseline, ExplorationPhase::Validation, &BTreeSet::new())?;
                let mut seen = BTreeSet::new();
                insert_signatures(&mut seen, &record.evaluation.observation);
                let frontier = ExplorationFrontier {
                    iteration: 0,
                    records: vec![record.clone()],
                    claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
                };
                (frontier, vec![record], seen, 1)
            };

        let mut early_stop_reason = None;
        while next_iteration <= self.config.iteration_budget && next_iteration < iteration_limit {
            let children = self.propose_children(&frontier, next_iteration)?;
            if children.is_empty() {
                early_stop_reason = Some(EarlyStopReason::Converged);
                break;
            }
            let mut child_records = Vec::new();
            let batch_seen = seen_signatures.clone();
            for candidate in children {
                child_records.push(self.evaluate_record(
                    candidate,
                    ExplorationPhase::Validation,
                    &batch_seen,
                )?);
            }
            let mut candidates = frontier.records.clone();
            candidates.extend(child_records.clone());
            candidates.sort_by(compare_records);
            candidates.truncate(self.config.beam_width);
            if !candidates.iter().any(|record| record.evaluation.valid) {
                early_stop_reason = Some(EarlyStopReason::NoValidCandidates);
                lineage.extend(child_records);
                break;
            }
            for record in &candidates {
                insert_signatures(&mut seen_signatures, &record.evaluation.observation);
            }
            lineage.extend(child_records);
            frontier = ExplorationFrontier {
                iteration: next_iteration,
                records: candidates,
                claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
            };
            next_iteration += 1;
        }

        if early_stop_reason.is_none() && next_iteration > self.config.iteration_budget {
            early_stop_reason = Some(EarlyStopReason::BudgetExhausted);
        }
        let checkpoint = ExplorationCheckpoint {
            run_id: self.config.run_id.clone(),
            config_digest: config_digest.clone(),
            next_iteration,
            frontier: frontier.clone(),
            lineage: lineage.clone(),
            seen_signatures: seen_signatures.into_iter().collect(),
            finalized: false,
            assessment_evaluation: None,
            assessment_report: None,
            early_stop_reason,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
        };
        let result = ExplorationResult {
            run_id: self.config.run_id.clone(),
            config_digest,
            validation_frontier: frontier,
            lineage,
            checkpoint,
            assessment_evaluation: None,
            assessment_report: None,
            finalized: false,
            early_stop_reason,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
        };
        self.validate_result(&result)?;
        Ok(result)
    }

    fn baseline_candidate(&self) -> Result<ExplorationCandidate> {
        let policy = ExplorerPolicy::from_config(&self.config.base_soak_config);
        self.make_candidate(policy, None, 0, "baseline")
    }

    fn make_candidate(
        &self,
        policy: ExplorerPolicy,
        parent_candidate_id: Option<String>,
        iteration: usize,
        proposal_operator: &str,
    ) -> Result<ExplorationCandidate> {
        let policy_digest = policy.digest()?;
        let mut candidate_id = format!("candidate_{}", &policy_digest[..16]);
        if let Some(parent) = &parent_candidate_id {
            let _ = write!(candidate_id, "_{}_{}", iteration, parent.len());
        }
        Ok(ExplorationCandidate {
            candidate_id,
            parent_candidate_id,
            iteration,
            policy,
            policy_digest,
            proposal_operator: proposal_operator.to_string(),
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
        })
    }

    fn propose_children(
        &self,
        frontier: &ExplorationFrontier,
        iteration: usize,
    ) -> Result<Vec<ExplorationCandidate>> {
        let mut operators = vec![
            "rotate_families",
            "rotate_mutations",
            "toggle_queue_policy",
            "reverse_minimization_order",
        ];
        if !self.config.equal_work_budget {
            operators.insert(2, "drop_last_mutation");
            operators.insert(3, "drop_last_family");
        }
        let mut seen = BTreeSet::new();
        let mut children = Vec::new();
        for (parent_index, parent) in frontier.records.iter().enumerate() {
            let offset =
                (self.config.fixed_seed as usize + iteration + parent_index) % operators.len();
            for operator_index in 0..operators.len() {
                if children.len() >= self.config.candidate_budget_per_iteration {
                    break;
                }
                let operator = operators[(offset + operator_index) % operators.len()];
                let Some(policy) = mutate_policy(&parent.candidate.policy, operator) else {
                    continue;
                };
                let candidate = self.make_candidate(
                    policy,
                    Some(parent.candidate.candidate_id.clone()),
                    iteration,
                    operator,
                )?;
                if seen.insert(candidate.policy_digest.clone()) {
                    children.push(candidate);
                }
            }
            if children.len() >= self.config.candidate_budget_per_iteration {
                break;
            }
        }
        Ok(children)
    }

    fn evaluate_record(
        &self,
        candidate: ExplorationCandidate,
        phase: ExplorationPhase,
        known_signatures: &BTreeSet<String>,
    ) -> Result<ExplorationLineageRecord> {
        let evaluation = self.evaluate_candidate(&candidate, phase, known_signatures)?;
        Ok(ExplorationLineageRecord {
            candidate,
            evaluation,
        })
    }

    fn evaluate_candidate(
        &self,
        candidate: &ExplorationCandidate,
        phase: ExplorationPhase,
        known_signatures: &BTreeSet<String>,
    ) -> Result<CandidateEvaluation> {
        let invalid = |reason: String| CandidateEvaluation {
            candidate_id: candidate.candidate_id.clone(),
            phase,
            valid: false,
            guidance: GuidanceVector::default(),
            observation: GuidanceObservation::default(),
            rejection_reason: Some(reason),
            failure_reductions: Vec::new(),
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
        };
        if let Err(error) = candidate.policy.validate(&self.config.base_soak_config) {
            return Ok(invalid(error.to_string()));
        }
        let plan = match self.config.candidate_plan(&candidate.policy, phase) {
            Ok(plan) => plan,
            Err(error) => return Ok(invalid(error.to_string())),
        };
        let mut case_results = Vec::new();
        let mut replay_observations = Vec::new();
        for manifest in &plan.shard_manifests {
            let mut runner =
                LocalSoakRunner::new(plan.clone()).with_clock(MockTelemetryClock::default());
            match runner.run_request(SoakRunRequest {
                shard_id: manifest.shard_id.clone(),
                resume: false,
            }) {
                Ok(result) => {
                    case_results.extend(result.case_results);
                    replay_observations.extend(result.replay_observations);
                }
                Err(error) => return Ok(invalid(error.to_string())),
            }
        }
        let mut observation = GuidanceObservation {
            covered_families: candidate.policy.family_order.clone(),
            covered_mutations: candidate
                .policy
                .mutation_schedule
                .normalized_classes()
                .iter()
                .map(|class| format!("{class:?}"))
                .collect(),
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
            ..GuidanceObservation::default()
        };
        let mut valid = !case_results.is_empty();
        for case in &case_results {
            observation.case_count += 1;
            observation.case_ids.push(case.case_id.clone());
            observation
                .replay_result_ids
                .extend(case.replay_result_ids.clone());
            let case_signature = format!(
                "case={};family={:?};status={:?};mutations={:?};replays={:?}",
                case.case_id,
                case.family_kind,
                case.status,
                case.mutation_ids,
                case.replay_result_ids
            );
            observation.replay_signatures.push(case_signature);
            match case.status {
                SoakCaseStatus::Completed
                | SoakCaseStatus::CompletedWithLocalRejections
                | SoakCaseStatus::SkippedByResume => {
                    observation.completed_case_count += 1;
                }
                _ => {
                    valid = false;
                    observation.failed_case_count += 1;
                }
            }
            for failure in &case.failures {
                let failure_signature = format!(
                    "kind={:?};phase={};mutation={:?};trace={:?};message={}",
                    failure.failure_kind,
                    failure.phase,
                    failure.mutation_class,
                    failure.trace_id,
                    failure.message
                );
                observation.failure_signatures.push(failure_signature);
            }
        }
        for replay in &replay_observations {
            append_replay_observation(&mut observation, replay);
        }
        observation.case_ids.sort();
        observation.replay_result_ids.sort();
        observation.replay_signatures.sort();
        observation.failure_signatures.sort();
        observation.covered_families.sort();
        observation.covered_mutations.sort();
        observation
            .replay_trace_observations
            .sort_by(|left, right| {
                left.replay_manifest_id
                    .cmp(&right.replay_manifest_id)
                    .then_with(|| left.replay_result_id.cmp(&right.replay_result_id))
                    .then_with(|| left.trace_id.cmp(&right.trace_id))
            });
        observation.replay_result_count = observation.replay_result_ids.len();
        observation.replay_signatures.dedup();
        observation.failure_signatures.dedup();
        let novel = observation
            .replay_signatures
            .iter()
            .filter(|signature| !known_signatures.contains(*signature))
            .count();
        let guidance = GuidanceVector {
            valid,
            coverage: observation.covered_families.len() + observation.covered_mutations.len(),
            novelty: novel,
            failures: observation.failure_signatures.len(),
            cost: observation.case_count + observation.replay_result_count,
        };
        Ok(CandidateEvaluation {
            candidate_id: candidate.candidate_id.clone(),
            phase,
            valid,
            guidance,
            observation,
            rejection_reason: if valid {
                None
            } else {
                Some("one or more local case results failed".to_string())
            },
            failure_reductions: Vec::new(),
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
        })
    }

    fn validate_checkpoint(&self, checkpoint: &ExplorationCheckpoint) -> Result<()> {
        if checkpoint.claim_boundary != EXPLORATION_CLAIM_BOUNDARY {
            return Err(ZkBenchError::validation(
                "exploration.checkpoint.claim_boundary",
                "checkpoint must remain Level0DesignNote",
            ));
        }
        if checkpoint.run_id != self.config.run_id {
            return Err(ZkBenchError::validation(
                "exploration.checkpoint.run_id",
                "checkpoint run id does not match config",
            ));
        }
        if checkpoint.config_digest != self.config.digest()? {
            return Err(ZkBenchError::validation(
                "exploration.checkpoint.config_digest",
                "checkpoint config digest does not match config",
            ));
        }
        validate_assessment_state(
            "exploration.checkpoint.assessment_state",
            checkpoint.finalized,
            &checkpoint.frontier,
            checkpoint.assessment_evaluation.as_ref(),
            checkpoint.assessment_report.as_ref(),
        )?;
        Ok(())
    }

    fn validate_result(&self, result: &ExplorationResult) -> Result<()> {
        if result.claim_boundary != EXPLORATION_CLAIM_BOUNDARY {
            return Err(ZkBenchError::validation(
                "exploration.result.claim_boundary",
                "result must remain Level0DesignNote",
            ));
        }
        if result.run_id != self.config.run_id || result.config_digest != self.config.digest()? {
            return Err(ZkBenchError::validation(
                "exploration.result.identity",
                "result identity does not match config",
            ));
        }
        self.validate_checkpoint(&result.checkpoint)?;
        if result.finalized != result.checkpoint.finalized {
            return Err(ZkBenchError::validation(
                "exploration.result.finalized",
                "result and checkpoint finalization states differ",
            ));
        }
        validate_assessment_state(
            "exploration.result.assessment_state",
            result.finalized,
            &result.validation_frontier,
            result.assessment_evaluation.as_ref(),
            result.assessment_report.as_ref(),
        )?;
        if result.assessment_evaluation != result.checkpoint.assessment_evaluation {
            return Err(ZkBenchError::validation(
                "exploration.result.assessment_evaluation",
                "result and checkpoint assessment evaluations differ",
            ));
        }
        if result.assessment_report != result.checkpoint.assessment_report {
            return Err(ZkBenchError::validation(
                "exploration.result.assessment_report",
                "result and checkpoint assessment reports differ",
            ));
        }
        Ok(())
    }
}

fn validate_assessment_state(
    path: &str,
    finalized: bool,
    validation_frontier: &ExplorationFrontier,
    assessment_evaluation: Option<&CandidateEvaluation>,
    assessment_report: Option<&ExplorationAssessmentReport>,
) -> Result<()> {
    if !finalized {
        if assessment_evaluation.is_some() || assessment_report.is_some() {
            return Err(ZkBenchError::validation(
                path,
                "assessment evaluation and report are sealed before finalization",
            ));
        }
        return Ok(());
    }

    let assessment = assessment_evaluation.ok_or_else(|| {
        ZkBenchError::validation(path, "finalized state is missing assessment evaluation")
    })?;
    let report = assessment_report.ok_or_else(|| {
        ZkBenchError::validation(path, "finalized state is missing assessment report")
    })?;
    if assessment.phase != ExplorationPhase::FinalizedAssessment {
        return Err(ZkBenchError::validation(
            path,
            "finalized assessment evaluation has the wrong phase",
        ));
    }
    let validation = validation_frontier.records.first().ok_or_else(|| {
        ZkBenchError::validation(path, "finalized state has an empty validation frontier")
    })?;
    if validation.evaluation.candidate_id != assessment.candidate_id {
        return Err(ZkBenchError::validation(
            path,
            "assessment evaluation does not belong to the selected validation candidate",
        ));
    }
    report.validate_against(&validation.evaluation, assessment)
}

fn signed_delta(after: usize, before: usize) -> i64 {
    let max = i64::MAX as usize;
    (after.min(max) as i64).saturating_sub(before.min(max) as i64)
}

fn guidance_observation_digest(observation: &GuidanceObservation) -> Result<String> {
    Ok(compute_artifact_digest(
        observation,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    )?
    .hex_digest)
}

fn mutate_policy(policy: &ExplorerPolicy, operator: &str) -> Option<ExplorerPolicy> {
    match operator {
        "rotate_families" if policy.family_order.len() > 1 => {
            let mut next = policy.family_order.clone();
            next.rotate_left(1);
            Some(policy.clone().with_family_order(next))
        }
        "rotate_mutations" if policy.mutation_schedule.mutation_classes.len() > 1 => {
            let mut next = policy.mutation_schedule.mutation_classes.clone();
            next.rotate_left(1);
            Some(policy.clone().with_mutation_order(next))
        }
        "drop_last_mutation" if policy.mutation_schedule.normalized_classes().len() > 1 => {
            let mut next = policy.mutation_schedule.mutation_classes.clone();
            next.pop();
            let mut result = policy.clone().with_mutation_order(next);
            result.mutation_schedule.max_mutations_per_case =
                result.mutation_schedule.mutation_classes.len();
            Some(result)
        }
        "drop_last_family" if policy.family_order.len() > 1 => {
            let mut next = policy.family_order.clone();
            next.pop();
            Some(policy.clone().with_family_order(next))
        }
        "toggle_queue_policy" => {
            let mut result = policy.clone();
            result.queue_policy = match policy.queue_policy {
                QueuePolicy::StableDigest => QueuePolicy::RoundRobinFamilies,
                QueuePolicy::RoundRobinFamilies => QueuePolicy::RoundRobinMutations,
                QueuePolicy::RoundRobinMutations => QueuePolicy::PreferFailuresOnTie,
                QueuePolicy::PreferFailuresOnTie => QueuePolicy::StableDigest,
            };
            Some(result)
        }
        "reverse_minimization_order" => {
            let mut result = policy.clone();
            result.minimization_order.reverse();
            Some(result)
        }
        _ => None,
    }
}

fn compare_records(
    left: &ExplorationLineageRecord,
    right: &ExplorationLineageRecord,
) -> std::cmp::Ordering {
    right
        .evaluation
        .guidance
        .cmp(&left.evaluation.guidance)
        .then_with(|| {
            left.candidate
                .policy_digest
                .cmp(&right.candidate.policy_digest)
        })
        .then_with(|| {
            left.candidate
                .candidate_id
                .cmp(&right.candidate.candidate_id)
        })
}

fn insert_signatures(seen: &mut BTreeSet<String>, observation: &GuidanceObservation) {
    seen.extend(observation.replay_signatures.iter().cloned());
    seen.extend(observation.failure_signatures.iter().cloned());
}

fn append_replay_observation(
    observation: &mut GuidanceObservation,
    replay: &SoakReplayObservation,
) {
    for trace in &replay.result.trace_results {
        observation
            .replay_trace_observations
            .push(ReplayTraceObservation {
                replay_manifest_id: replay.manifest.id.clone(),
                replay_result_id: replay.result.id.clone(),
                replay_status: replay.result.status,
                replay_failure_mode: replay.result.failure_mode,
                trace_id: trace.trace_id.clone(),
                expected_verdict: trace.expected_verdict,
                local_oracle_outcome: trace.local_oracle_outcome.clone(),
                result_classification: trace.result_classification,
                claim_boundary: replay.claim_boundary,
            });
        observation.replay_signatures.push(format!(
            "manifest={};result={};status={:?};failure_mode={:?};trace={};expected={:?};oracle={:?};classification={:?}",
            replay.manifest.id,
            replay.result.id,
            replay.result.status,
            replay.result.failure_mode,
            trace.trace_id,
            trace.expected_verdict,
            trace.local_oracle_outcome,
            trace.result_classification,
        ));
    }
}

fn apply_policy_schedule(
    mut plan: SoakShardPlan,
    policy: &ExplorerPolicy,
    case_budget: usize,
) -> Result<SoakShardPlan> {
    let family_rank = policy
        .family_order
        .iter()
        .enumerate()
        .map(|(index, family)| (*family, index))
        .collect::<BTreeMap<_, _>>();
    let mutation_rank = policy
        .mutation_schedule
        .normalized_classes()
        .iter()
        .enumerate()
        .map(|(index, mutation)| (*mutation, index))
        .collect::<BTreeMap<_, _>>();

    for case in &mut plan.case_plans {
        case.mutation_classes.sort_by_key(|mutation| {
            (
                mutation_rank.get(mutation).copied().unwrap_or(usize::MAX),
                *mutation,
            )
        });
    }

    match policy.queue_policy {
        QueuePolicy::StableDigest | QueuePolicy::PreferFailuresOnTie => {
            plan.case_plans
                .sort_by(|left, right| left.id.cmp(&right.id));
        }
        QueuePolicy::RoundRobinFamilies => {
            plan.case_plans.sort_by_key(|case| {
                (
                    family_rank
                        .get(&case.family_kind)
                        .copied()
                        .unwrap_or(usize::MAX),
                    case.generator_seed,
                    case.id.clone(),
                )
            });
        }
        QueuePolicy::RoundRobinMutations => {
            plan.case_plans.sort_by_key(|case| {
                (
                    case.mutation_classes
                        .first()
                        .and_then(|mutation| mutation_rank.get(mutation).copied())
                        .unwrap_or(usize::MAX),
                    family_rank
                        .get(&case.family_kind)
                        .copied()
                        .unwrap_or(usize::MAX),
                    case.generator_seed,
                    case.id.clone(),
                )
            });
        }
    }

    if case_budget > 0 {
        plan.case_plans.truncate(case_budget);
    }

    let shard_count = plan.shard_manifests.len();
    if shard_count == 0 {
        return Err(ZkBenchError::validation(
            "exploration.schedule.shard_count",
            "scheduled exploration plan must contain at least one shard",
        ));
    }
    let mut assignments = vec![Vec::new(); shard_count];
    for (index, case) in plan.case_plans.iter().enumerate() {
        assignments[index % shard_count].push(case.id.clone());
    }
    for (manifest, assigned_case_ids) in plan.shard_manifests.iter_mut().zip(assignments) {
        manifest.expected_case_count = assigned_case_ids.len();
        manifest.assigned_case_ids = assigned_case_ids;
    }
    validate_soak_shard_plan(&plan)?;
    Ok(plan)
}

/// Validate an exploration artifact.
pub fn validate_exploration_artifact(artifact: &ExplorationArtifact) -> Result<()> {
    if artifact.schema_version != EXPLORATION_SCHEMA_VERSION {
        return Err(ZkBenchError::validation(
            "exploration.artifact.schema_version",
            "unsupported exploration artifact schema version",
        ));
    }
    if artifact.state_slice != EXPLORATION_STATE_SLICE {
        return Err(ZkBenchError::validation(
            "exploration.artifact.state_slice",
            "exploration artifact state slice does not match",
        ));
    }
    if artifact.claim_boundary != EXPLORATION_CLAIM_BOUNDARY {
        return Err(ZkBenchError::validation(
            "exploration.artifact.claim_boundary",
            "exploration artifact must remain Level0DesignNote",
        ));
    }
    if artifact.result.claim_boundary != EXPLORATION_CLAIM_BOUNDARY {
        return Err(ZkBenchError::validation(
            "exploration.artifact.result.claim_boundary",
            "exploration result must remain Level0DesignNote",
        ));
    }
    validate_assessment_state(
        "exploration.artifact.result.assessment_state",
        artifact.result.finalized,
        &artifact.result.validation_frontier,
        artifact.result.assessment_evaluation.as_ref(),
        artifact.result.assessment_report.as_ref(),
    )?;
    validate_assessment_state(
        "exploration.artifact.checkpoint.assessment_state",
        artifact.result.checkpoint.finalized,
        &artifact.result.checkpoint.frontier,
        artifact.result.checkpoint.assessment_evaluation.as_ref(),
        artifact.result.checkpoint.assessment_report.as_ref(),
    )?;
    if artifact.result.assessment_evaluation != artifact.result.checkpoint.assessment_evaluation {
        return Err(ZkBenchError::validation(
            "exploration.artifact.assessment_evaluation",
            "result and checkpoint assessment evaluations differ",
        ));
    }
    if artifact.result.assessment_report != artifact.result.checkpoint.assessment_report {
        return Err(ZkBenchError::validation(
            "exploration.artifact.assessment_report",
            "result and checkpoint assessment reports differ",
        ));
    }
    Ok(())
}

/// Serialize an exploration artifact using deterministic crate-local JSON.
pub fn serialize_exploration_artifact_json(artifact: &ExplorationArtifact) -> Result<String> {
    validate_exploration_artifact(artifact)?;
    serde_json::to_string_pretty(artifact).map_err(|error| {
        ZkBenchError::serialization("serialize_exploration_artifact_json", error.to_string())
    })
}

/// Deserialize and validate an exploration artifact.
pub fn deserialize_exploration_artifact_json(json: &str) -> Result<ExplorationArtifact> {
    let artifact: ExplorationArtifact = serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("deserialize_exploration_artifact_json", error.to_string())
    })?;
    validate_exploration_artifact(&artifact)?;
    Ok(artifact)
}

/// Compute the digest of a validated exploration artifact.
pub fn compute_exploration_artifact_digest(artifact: &ExplorationArtifact) -> Result<String> {
    validate_exploration_artifact(artifact)?;
    Ok(compute_artifact_digest(
        artifact,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    )?
    .hex_digest)
}

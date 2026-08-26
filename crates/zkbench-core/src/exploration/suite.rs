//! Independent sealed campaign assessment for deterministic exploration.
//!
//! This module is the named state slice
//! `antithesis-inspired-deterministic-exploration-v1-independent-assessment-suite`.
//! It compares the bounded `BeamSearch` candidate with fixed policies across
//! disjoint local seed domains. A candidate is promoted only when it strictly
//! improves the frozen primary metric over every fixed baseline in the minimum
//! number of finalized campaigns. Assessment results remain absent until the
//! one-way `finalize_assessment` operation.
//!
//! The suite is local, provider-free, and diagnostic. It does not append
//! evidence, alter oracle semantics, emit accepted benchmark evidence, or
//! claim production or scientific validity.

use std::collections::{BTreeMap, BTreeSet};

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{compute_artifact_digest, ArtifactKind, ArtifactRole, ClaimBoundary};

use super::{
    serialize_baseline_campaign_result_json, BaselineCampaignConfig, BaselineCampaignResult,
    BaselineCampaignRunner, BaselinePolicyKind, ExplorationPhase, ExplorationWorkUnits,
    EXPLORATION_CLAIM_BOUNDARY, PRIMARY_METRIC_ID,
};

/// Named independent-assessment state slice.
pub const INDEPENDENT_SUITE_STATE_SLICE: &str =
    "antithesis-inspired-deterministic-exploration-v1-independent-assessment-suite";

/// Independent-suite schema version.
pub const INDEPENDENT_SUITE_SCHEMA_VERSION: &str =
    "antithesis-inspired-independent-assessment-suite-v1";

/// Fixed candidate policy admitted by the promotion gate.
pub const INDEPENDENT_SUITE_CANDIDATE: BaselinePolicyKind = BaselinePolicyKind::BeamSearch;

/// Configuration for repeated independent local campaigns.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct IndependentCampaignSuiteConfig {
    /// Stable suite id.
    pub suite_id: String,
    /// Canonically ordered campaigns.
    pub campaigns: Vec<BaselineCampaignConfig>,
    /// Minimum number of strict assessment improvements required for promotion.
    pub minimum_assessment_improvements: usize,
    /// Candidate policy evaluated against fixed baselines.
    pub candidate_policy: BaselinePolicyKind,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Nonclaim notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl IndependentCampaignSuiteConfig {
    /// Build a suite with `BeamSearch` as the candidate and a unanimous gate.
    pub fn new(suite_id: impl Into<String>, mut campaigns: Vec<BaselineCampaignConfig>) -> Self {
        campaigns.sort_by(|left, right| left.campaign_id.cmp(&right.campaign_id));
        let minimum_assessment_improvements = campaigns.len();
        Self {
            suite_id: suite_id.into(),
            campaigns,
            minimum_assessment_improvements,
            candidate_policy: INDEPENDENT_SUITE_CANDIDATE,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
            notes: vec![
                "Independent campaign suite is local strategy-development metadata only."
                    .to_string(),
                "Promotion requires strict improvement on sealed assessment campaigns.".to_string(),
                "No evidence ledger or benchmark claim is produced.".to_string(),
            ],
        }
    }

    /// Set the minimum strict assessment improvements required for promotion.
    pub fn with_minimum_assessment_improvements(mut self, count: usize) -> Self {
        self.minimum_assessment_improvements = count;
        self
    }

    /// Validate suite identity, disjoint seed domains, and equal allocation.
    pub fn validate(&self) -> Result<()> {
        if self.suite_id.trim().is_empty() {
            return Err(ZkBenchError::validation(
                "exploration.independent_suite.suite_id",
                "independent suite id is empty",
            ));
        }
        if self.claim_boundary != EXPLORATION_CLAIM_BOUNDARY {
            return Err(ZkBenchError::validation(
                "exploration.independent_suite.claim_boundary",
                "independent suites must remain Level0DesignNote",
            ));
        }
        if self.campaigns.len() < 2 {
            return Err(ZkBenchError::validation(
                "exploration.independent_suite.campaigns",
                "independent suite requires at least two campaigns",
            ));
        }
        if self.minimum_assessment_improvements == 0
            || self.minimum_assessment_improvements > self.campaigns.len()
        {
            return Err(ZkBenchError::validation(
                "exploration.independent_suite.minimum_assessment_improvements",
                "promotion threshold must be within the campaign count",
            ));
        }
        if self.candidate_policy != INDEPENDENT_SUITE_CANDIDATE {
            return Err(ZkBenchError::validation(
                "exploration.independent_suite.candidate_policy",
                "only BeamSearch is admitted as the promotion candidate",
            ));
        }

        let mut campaign_ids = BTreeSet::new();
        let mut config_digests = BTreeSet::new();
        let mut seed_domains = Vec::new();
        let mut allocation_keys = BTreeSet::new();
        for (index, campaign) in self.campaigns.iter().enumerate() {
            campaign.validate()?;
            if index > 0 && self.campaigns[index - 1].campaign_id >= campaign.campaign_id {
                return Err(ZkBenchError::validation(
                    "exploration.independent_suite.campaigns",
                    "campaigns must be in canonical campaign-id order",
                ));
            }
            if !campaign_ids.insert(campaign.campaign_id.clone()) {
                return Err(ZkBenchError::validation(
                    "exploration.independent_suite.campaigns",
                    "campaign ids must be unique",
                ));
            }
            if !config_digests.insert(campaign.digest()?) {
                return Err(ZkBenchError::validation(
                    "exploration.independent_suite.campaigns",
                    "campaign configuration digests must be unique",
                ));
            }
            let seed_range = &campaign.exploration.base_soak_config.scope.seed_range;
            if seed_range.is_empty() {
                return Err(ZkBenchError::validation(
                    "exploration.independent_suite.seed_domains",
                    "campaign seed domains must be non-empty",
                ));
            }
            seed_domains.push((
                seed_range.start_inclusive,
                seed_range.end_exclusive,
                campaign.campaign_id.clone(),
            ));
            let corpus = super::LocalTargetCorpus::from_exploration_config(&campaign.exploration)?;
            allocation_keys.insert((
                corpus.plan.case_plans.len(),
                corpus.plan.shard_manifests.len(),
                corpus
                    .plan
                    .case_plans
                    .iter()
                    .map(|case| case.mutation_classes.len())
                    .sum::<usize>(),
            ));
        }
        seed_domains.sort_by_key(|domain| (domain.0, domain.1));
        for pair in seed_domains.windows(2) {
            if pair[1].0 < pair[0].1 {
                return Err(ZkBenchError::validation(
                    "exploration.independent_suite.seed_domains",
                    "campaign seed domains must be disjoint",
                ));
            }
        }
        if allocation_keys.len() != 1 {
            return Err(ZkBenchError::validation(
                "exploration.independent_suite.equal_budget",
                "campaigns must share equal case, shard, and mutation budgets",
            ));
        }
        Ok(())
    }

    /// Compute the deterministic suite configuration digest.
    pub fn digest(&self) -> Result<String> {
        Ok(compute_artifact_digest(
            self,
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Manifest),
        )?
        .hex_digest)
    }
}

/// Aggregated policy metrics across independent campaigns.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct IndependentPolicyAggregateRow {
    /// Policy kind.
    pub kind: BaselinePolicyKind,
    /// Per-campaign policy digests in canonical campaign order.
    pub policy_digests: Vec<String>,
    /// Per-campaign primary metric values.
    pub metric_values: Vec<usize>,
    /// Sum of primary metric values across campaigns.
    pub total_metric_value: usize,
    /// Campaigns where this policy strictly beat every fixed baseline.
    pub strict_improvement_count: usize,
    /// Per-campaign work units.
    pub work_units_per_campaign: ExplorationWorkUnits,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Deterministic comparison across independent campaigns.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct IndependentCampaignComparisonReport {
    /// Phase represented by this report.
    pub phase: ExplorationPhase,
    /// Frozen primary metric id.
    pub metric_id: String,
    /// Number of independent campaigns.
    pub campaign_count: usize,
    /// Candidate policy used for strict-improvement counts.
    pub candidate_policy: BaselinePolicyKind,
    /// Rows in stable policy order.
    pub rows: Vec<IndependentPolicyAggregateRow>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Explicit promotion-gate result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct StrategyPromotionGate {
    /// Candidate policy.
    pub candidate_policy: BaselinePolicyKind,
    /// Required strict assessment improvements.
    pub required_assessment_improvements: usize,
    /// Observed strict assessment improvements.
    pub observed_assessment_improvements: usize,
    /// Whether the candidate passed the local gate.
    pub promoted: bool,
    /// Deterministic reason.
    pub reason: String,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Resumable validation checkpoint for an independent campaign suite.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct IndependentCampaignSuiteCheckpoint {
    /// Suite id.
    pub suite_id: String,
    /// Suite configuration digest.
    pub config_digest: String,
    /// Validation campaigns only.
    pub validation_campaigns: Vec<BaselineCampaignResult>,
    /// Validation comparison.
    pub validation_comparison: IndependentCampaignComparisonReport,
    /// One-way finalization marker.
    pub finalized: bool,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Complete independent campaign suite result.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct IndependentCampaignSuiteResult {
    /// Schema version.
    pub schema_version: String,
    /// Suite id.
    pub suite_id: String,
    /// Suite configuration digest.
    pub config_digest: String,
    /// Validation campaigns only before finalization.
    pub validation_campaigns: Vec<BaselineCampaignResult>,
    /// Validation comparison across campaigns.
    pub validation_comparison: IndependentCampaignComparisonReport,
    /// Resumable validation checkpoint.
    pub checkpoint: IndependentCampaignSuiteCheckpoint,
    /// Assessment campaigns, present only after finalization.
    #[serde(default)]
    pub assessment_campaigns: Option<Vec<BaselineCampaignResult>>,
    /// Assessment comparison, present only after finalization.
    #[serde(default)]
    pub assessment_comparison: Option<IndependentCampaignComparisonReport>,
    /// Promotion gate, present only after finalization.
    #[serde(default)]
    pub promotion_gate: Option<StrategyPromotionGate>,
    /// One-way finalization marker.
    pub finalized: bool,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Nonclaim notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Runner for repeated independent local campaigns.
#[derive(Debug, Clone)]
pub struct IndependentCampaignSuiteRunner {
    config: IndependentCampaignSuiteConfig,
}

impl IndependentCampaignSuiteRunner {
    /// Validate and create a suite runner.
    pub fn new(config: IndependentCampaignSuiteConfig) -> Result<Self> {
        config.validate()?;
        Ok(Self { config })
    }

    /// Return the suite configuration.
    pub fn config(&self) -> &IndependentCampaignSuiteConfig {
        &self.config
    }

    /// Run every campaign on validation domains only.
    pub fn run_validation(&self) -> Result<IndependentCampaignSuiteResult> {
        let mut validation_campaigns = Vec::new();
        for campaign_config in &self.config.campaigns {
            validation_campaigns
                .push(BaselineCampaignRunner::new(campaign_config.clone())?.run_validation()?);
        }
        validation_campaigns.sort_by(|left, right| left.campaign_id.cmp(&right.campaign_id));
        let validation_comparison = build_comparison(
            &validation_campaigns,
            ExplorationPhase::Validation,
            self.config.candidate_policy,
        )?;
        let checkpoint = IndependentCampaignSuiteCheckpoint {
            suite_id: self.config.suite_id.clone(),
            config_digest: self.config.digest()?,
            validation_campaigns: validation_campaigns.clone(),
            validation_comparison: validation_comparison.clone(),
            finalized: false,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
        };
        let result = IndependentCampaignSuiteResult {
            schema_version: INDEPENDENT_SUITE_SCHEMA_VERSION.to_string(),
            suite_id: self.config.suite_id.clone(),
            config_digest: checkpoint.config_digest.clone(),
            validation_campaigns,
            validation_comparison,
            checkpoint,
            assessment_campaigns: None,
            assessment_comparison: None,
            promotion_gate: None,
            finalized: false,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
            notes: self.config.notes.clone(),
        };
        validate_suite_result(&result, &self.config)?;
        Ok(result)
    }

    /// Resume validation from a retained checkpoint without exposing assessment data.
    pub fn resume_validation(
        &self,
        checkpoint: IndependentCampaignSuiteCheckpoint,
    ) -> Result<IndependentCampaignSuiteResult> {
        self.validate_checkpoint(&checkpoint)?;
        let result = IndependentCampaignSuiteResult {
            schema_version: INDEPENDENT_SUITE_SCHEMA_VERSION.to_string(),
            suite_id: checkpoint.suite_id.clone(),
            config_digest: checkpoint.config_digest.clone(),
            validation_campaigns: checkpoint.validation_campaigns.clone(),
            validation_comparison: checkpoint.validation_comparison.clone(),
            checkpoint,
            assessment_campaigns: None,
            assessment_comparison: None,
            promotion_gate: None,
            finalized: false,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
            notes: self.config.notes.clone(),
        };
        validate_suite_result(&result, &self.config)?;
        Ok(result)
    }

    /// Finalize all held-out assessments exactly once.
    pub fn finalize_assessment(&self, result: &mut IndependentCampaignSuiteResult) -> Result<()> {
        validate_suite_result(result, &self.config)?;
        if result.finalized {
            return Err(ZkBenchError::validation(
                "exploration.independent_suite.finalize_assessment",
                "independent campaign suite assessment has already been finalized",
            ));
        }
        let mut assessment_campaigns = Vec::new();
        for (campaign_config, validation) in self
            .config
            .campaigns
            .iter()
            .zip(&result.validation_campaigns)
        {
            let runner = BaselineCampaignRunner::new(campaign_config.clone())?;
            let mut finalized = validation.clone();
            runner.finalize_assessment(&mut finalized)?;
            assessment_campaigns.push(finalized);
        }
        assessment_campaigns.sort_by(|left, right| left.campaign_id.cmp(&right.campaign_id));
        let assessment_comparison = build_comparison(
            &assessment_campaigns,
            ExplorationPhase::FinalizedAssessment,
            self.config.candidate_policy,
        )?;
        let observed_assessment_improvements = assessment_comparison
            .rows
            .iter()
            .find(|row| row.kind == self.config.candidate_policy)
            .map(|row| row.strict_improvement_count)
            .ok_or_else(|| {
                ZkBenchError::validation(
                    "exploration.independent_suite.promotion_gate",
                    "candidate policy row is missing from assessment comparison",
                )
            })?;
        let promoted =
            observed_assessment_improvements >= self.config.minimum_assessment_improvements;
        let reason = if promoted {
            format!(
                "candidate strictly improved the primary metric in {} sealed assessment campaigns",
                observed_assessment_improvements
            )
        } else {
            format!(
                "candidate strictly improved the primary metric in {} of {} required sealed assessment campaigns",
                observed_assessment_improvements,
                self.config.minimum_assessment_improvements
            )
        };
        result.assessment_campaigns = Some(assessment_campaigns);
        result.assessment_comparison = Some(assessment_comparison);
        result.promotion_gate = Some(StrategyPromotionGate {
            candidate_policy: self.config.candidate_policy,
            required_assessment_improvements: self.config.minimum_assessment_improvements,
            observed_assessment_improvements,
            promoted,
            reason,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
        });
        result.finalized = true;
        result.checkpoint.finalized = true;
        validate_suite_result(result, &self.config)
    }

    fn validate_checkpoint(&self, checkpoint: &IndependentCampaignSuiteCheckpoint) -> Result<()> {
        if checkpoint.suite_id != self.config.suite_id
            || checkpoint.config_digest != self.config.digest()?
            || checkpoint.finalized
            || checkpoint.claim_boundary != EXPLORATION_CLAIM_BOUNDARY
        {
            return Err(ZkBenchError::validation(
                "exploration.independent_suite.checkpoint.identity",
                "independent suite checkpoint does not match active config",
            ));
        }
        if checkpoint.validation_campaigns.len() != self.config.campaigns.len() {
            return Err(ZkBenchError::validation(
                "exploration.independent_suite.checkpoint.validation_campaigns",
                "independent suite checkpoint campaign count is invalid",
            ));
        }
        Ok(())
    }
}

/// Serialize a suite result as deterministic local JSON.
pub fn serialize_independent_campaign_suite_json(
    result: &IndependentCampaignSuiteResult,
) -> Result<String> {
    if result.claim_boundary != EXPLORATION_CLAIM_BOUNDARY {
        return Err(ZkBenchError::validation(
            "exploration.independent_suite.serialize.claim_boundary",
            "independent suite result must remain Level0DesignNote",
        ));
    }
    if result.checkpoint.suite_id != result.suite_id
        || result.checkpoint.config_digest != result.config_digest
        || result.checkpoint.validation_campaigns != result.validation_campaigns
        || result.checkpoint.validation_comparison != result.validation_comparison
        || result.checkpoint.finalized != result.finalized
        || result.checkpoint.claim_boundary != EXPLORATION_CLAIM_BOUNDARY
    {
        return Err(ZkBenchError::validation(
            "exploration.independent_suite.result.checkpoint",
            "independent suite checkpoint does not match result",
        ));
    }
    serde_json::to_string_pretty(result).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_independent_campaign_suite_json",
            error.to_string(),
        )
    })
}

/// Deserialize and validate a suite result against its retained config.
pub fn deserialize_independent_campaign_suite_json(
    json: &str,
    config: &IndependentCampaignSuiteConfig,
) -> Result<IndependentCampaignSuiteResult> {
    let result: IndependentCampaignSuiteResult = serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_independent_campaign_suite_json",
            error.to_string(),
        )
    })?;
    validate_suite_result(&result, config)?;
    Ok(result)
}

fn build_comparison(
    campaigns: &[BaselineCampaignResult],
    phase: ExplorationPhase,
    candidate_policy: BaselinePolicyKind,
) -> Result<IndependentCampaignComparisonReport> {
    if campaigns.is_empty() {
        return Err(ZkBenchError::validation(
            "exploration.independent_suite.comparison",
            "comparison requires at least one campaign",
        ));
    }
    let mut per_policy: BTreeMap<BaselinePolicyKind, Vec<(String, usize, ExplorationWorkUnits)>> =
        BTreeMap::new();
    for campaign in campaigns {
        for record in &campaign.records {
            let run = match phase {
                ExplorationPhase::Validation => &record.validation_run,
                ExplorationPhase::FinalizedAssessment => {
                    record.assessment_run.as_ref().ok_or_else(|| {
                        ZkBenchError::validation(
                            "exploration.independent_suite.comparison",
                            "assessment comparison requested before campaign finalization",
                        )
                    })?
                }
            };
            per_policy.entry(record.kind).or_default().push((
                record.policy_digest.clone(),
                run.primary_metric.value(),
                run.primary_metric.work_units,
            ));
        }
    }
    let mut rows = Vec::new();
    for (kind, values) in per_policy {
        if values.len() != campaigns.len() {
            return Err(ZkBenchError::validation(
                "exploration.independent_suite.comparison",
                "every policy must have one observation per campaign",
            ));
        }
        let work_units_per_campaign = values[0].2;
        if values
            .iter()
            .any(|value| value.2 != work_units_per_campaign)
        {
            return Err(ZkBenchError::validation(
                "exploration.independent_suite.equal_budget",
                "policy work units differ across independent campaigns",
            ));
        }
        let metric_values = values.iter().map(|value| value.1).collect::<Vec<_>>();
        rows.push(IndependentPolicyAggregateRow {
            kind,
            policy_digests: values.iter().map(|value| value.0.clone()).collect(),
            total_metric_value: metric_values.iter().sum(),
            metric_values,
            strict_improvement_count: 0,
            work_units_per_campaign,
            claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
        });
    }
    rows.sort_by_key(|row| row.kind);
    let fixed_baseline_values = rows
        .iter()
        .filter(|row| row.kind != candidate_policy)
        .map(|row| row.metric_values.clone())
        .collect::<Vec<_>>();
    let candidate_values = rows
        .iter()
        .find(|row| row.kind == candidate_policy)
        .map(|row| row.metric_values.clone())
        .ok_or_else(|| {
            ZkBenchError::validation(
                "exploration.independent_suite.comparison",
                "candidate policy is missing from comparison",
            )
        })?;
    let strict_improvement_count = candidate_values
        .iter()
        .enumerate()
        .filter(|(index, candidate_value)| {
            fixed_baseline_values
                .iter()
                .all(|baseline| **candidate_value > baseline[*index])
        })
        .count();
    if let Some(candidate_row) = rows.iter_mut().find(|row| row.kind == candidate_policy) {
        candidate_row.strict_improvement_count = strict_improvement_count;
    }
    Ok(IndependentCampaignComparisonReport {
        phase,
        metric_id: PRIMARY_METRIC_ID.to_string(),
        campaign_count: campaigns.len(),
        candidate_policy,
        rows,
        claim_boundary: EXPLORATION_CLAIM_BOUNDARY,
    })
}

fn validate_suite_result(
    result: &IndependentCampaignSuiteResult,
    config: &IndependentCampaignSuiteConfig,
) -> Result<()> {
    config.validate()?;
    if result.schema_version != INDEPENDENT_SUITE_SCHEMA_VERSION
        || result.suite_id != config.suite_id
        || result.config_digest != config.digest()?
    {
        return Err(ZkBenchError::validation(
            "exploration.independent_suite.result.identity",
            "independent suite result identity does not match config",
        ));
    }
    if result.claim_boundary != EXPLORATION_CLAIM_BOUNDARY {
        return Err(ZkBenchError::validation(
            "exploration.independent_suite.result.claim_boundary",
            "independent suite result must remain Level0DesignNote",
        ));
    }
    if result.validation_campaigns.len() != config.campaigns.len() {
        return Err(ZkBenchError::validation(
            "exploration.independent_suite.result.validation_campaigns",
            "validation campaign count does not match config",
        ));
    }
    for (campaign, campaign_config) in result.validation_campaigns.iter().zip(&config.campaigns) {
        if campaign.campaign_id != campaign_config.campaign_id
            || campaign.config_digest != campaign_config.digest()?
            || campaign.finalized
            || campaign.assessment_comparison.is_some()
            || campaign
                .records
                .iter()
                .any(|record| record.assessment_run.is_some())
        {
            return Err(ZkBenchError::validation(
                "exploration.independent_suite.result.validation_sealing",
                "validation suite result contains assessment data",
            ));
        }
        serialize_baseline_campaign_result_json(campaign)?;
    }
    let expected_validation = build_comparison(
        &result.validation_campaigns,
        ExplorationPhase::Validation,
        config.candidate_policy,
    )?;
    if result.validation_comparison != expected_validation {
        return Err(ZkBenchError::validation(
            "exploration.independent_suite.result.validation_comparison",
            "validation comparison does not match campaign results",
        ));
    }
    if !result.finalized {
        if result.assessment_campaigns.is_some()
            || result.assessment_comparison.is_some()
            || result.promotion_gate.is_some()
        {
            return Err(ZkBenchError::validation(
                "exploration.independent_suite.result.assessment_sealing",
                "assessment data is present before suite finalization",
            ));
        }
        return Ok(());
    }
    let assessment_campaigns = result.assessment_campaigns.as_ref().ok_or_else(|| {
        ZkBenchError::validation(
            "exploration.independent_suite.result.assessment_campaigns",
            "finalized suite is missing assessment campaigns",
        )
    })?;
    if assessment_campaigns.len() != config.campaigns.len()
        || assessment_campaigns
            .iter()
            .any(|campaign| !campaign.finalized)
    {
        return Err(ZkBenchError::validation(
            "exploration.independent_suite.result.assessment_campaigns",
            "assessment campaign set is incomplete or unfinalized",
        ));
    }
    for (campaign, campaign_config) in assessment_campaigns.iter().zip(&config.campaigns) {
        if campaign.campaign_id != campaign_config.campaign_id
            || campaign.config_digest != campaign_config.digest()?
        {
            return Err(ZkBenchError::validation(
                "exploration.independent_suite.result.assessment_identity",
                "assessment campaign identity does not match config",
            ));
        }
        serialize_baseline_campaign_result_json(campaign)?;
    }
    let assessment_comparison = result.assessment_comparison.as_ref().ok_or_else(|| {
        ZkBenchError::validation(
            "exploration.independent_suite.result.assessment_comparison",
            "finalized suite is missing assessment comparison",
        )
    })?;
    let expected_assessment = build_comparison(
        assessment_campaigns,
        ExplorationPhase::FinalizedAssessment,
        config.candidate_policy,
    )?;
    if assessment_comparison != &expected_assessment {
        return Err(ZkBenchError::validation(
            "exploration.independent_suite.result.assessment_comparison",
            "assessment comparison does not match campaign results",
        ));
    }
    let gate = result.promotion_gate.as_ref().ok_or_else(|| {
        ZkBenchError::validation(
            "exploration.independent_suite.result.promotion_gate",
            "finalized suite is missing promotion gate",
        )
    })?;
    let candidate_row = expected_assessment
        .rows
        .iter()
        .find(|row| row.kind == config.candidate_policy)
        .ok_or_else(|| {
            ZkBenchError::validation(
                "exploration.independent_suite.result.promotion_gate",
                "candidate row is missing from assessment comparison",
            )
        })?;
    if gate.candidate_policy != config.candidate_policy
        || gate.required_assessment_improvements != config.minimum_assessment_improvements
        || gate.observed_assessment_improvements != candidate_row.strict_improvement_count
        || gate.promoted
            != (candidate_row.strict_improvement_count >= config.minimum_assessment_improvements)
        || gate.claim_boundary != EXPLORATION_CLAIM_BOUNDARY
    {
        return Err(ZkBenchError::validation(
            "exploration.independent_suite.result.promotion_gate",
            "promotion gate does not match assessment comparison",
        ));
    }
    let expected_reason = if gate.promoted {
        format!(
            "candidate strictly improved the primary metric in {} sealed assessment campaigns",
            gate.observed_assessment_improvements
        )
    } else {
        format!(
            "candidate strictly improved the primary metric in {} of {} required sealed assessment campaigns",
            gate.observed_assessment_improvements, gate.required_assessment_improvements
        )
    };
    if gate.reason != expected_reason {
        return Err(ZkBenchError::validation(
            "exploration.independent_suite.result.promotion_gate.reason",
            "promotion gate reason is not canonical",
        ));
    }
    Ok(())
}

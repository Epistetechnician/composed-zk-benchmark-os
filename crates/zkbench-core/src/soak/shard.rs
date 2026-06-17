//! Deterministic shard planning for local soak runs.

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{compute_artifact_digest, ArtifactKind, ArtifactRole, ClaimBoundary};
use crate::generator::{FamilyKind, GeneratorTunables};
use crate::mutation::MutationClass;

use super::config::{validate_soak_run_config, SoakOutputPolicy, SoakRunConfig};

/// Deterministic shard id.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub struct SoakShardId {
    /// Stable id value.
    pub value: String,
}

impl SoakShardId {
    /// Build from a shard index.
    pub fn from_index(index: usize) -> Self {
        Self {
            value: format!("shard-{index:04}"),
        }
    }
}

/// Stable case id.
pub type SoakCaseId = String;

/// Planned local soak case.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakCasePlan {
    /// Stable case id.
    pub id: SoakCaseId,
    /// Family kind.
    pub family_kind: FamilyKind,
    /// Generator seed.
    pub generator_seed: u64,
    /// Generator tunables.
    pub generator_tunables: GeneratorTunables,
    /// Mutation classes to attempt.
    pub mutation_classes: Vec<MutationClass>,
    /// Trace selection policy.
    pub trace_selection: String,
    /// Output policy.
    pub output_policy: SoakOutputPolicy,
    /// Claim boundary for this plan artifact.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Full deterministic shard plan.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakShardPlan {
    /// Source config.
    pub config: SoakRunConfig,
    /// SHA-256 digest of the source config.
    pub config_digest: String,
    /// Planned cases in deterministic order.
    pub case_plans: Vec<SoakCasePlan>,
    /// Shard manifests.
    pub shard_manifests: Vec<SoakShardManifest>,
    /// Claim boundary for the plan artifact.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Shard manifest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakShardManifest {
    /// Shard id.
    pub shard_id: SoakShardId,
    /// Zero-based shard index.
    pub shard_index: usize,
    /// Total shard count.
    pub shard_count: usize,
    /// Source config digest.
    pub config_digest: String,
    /// Assigned case ids.
    pub assigned_case_ids: Vec<SoakCaseId>,
    /// Expected case count.
    pub expected_case_count: usize,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Output policy.
    pub output_policy: SoakOutputPolicy,
    /// Resume token.
    #[serde(default)]
    pub resume_token: Option<SoakShardResumeToken>,
    /// Relative artifact refs.
    #[serde(default)]
    pub relative_artifact_refs: Vec<String>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Shard execution status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SoakShardStatus {
    /// Planned but not run.
    Planned,
    /// Running.
    Running,
    /// Completed without local failures.
    Completed,
    /// Completed with recorded local failures or warnings.
    CompletedWithFailures,
    /// Failed at shard level.
    Failed,
    /// Resumable checkpoint exists.
    Resumable,
}

/// Shard progress.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakShardProgress {
    /// Total case count.
    pub total_cases: usize,
    /// Completed case count.
    pub completed_cases: usize,
    /// Failed case count.
    pub failed_cases: usize,
    /// Skipped case count.
    pub skipped_cases: usize,
}

impl SoakShardProgress {
    /// Empty progress for a manifest.
    pub fn new(total_cases: usize) -> Self {
        Self {
            total_cases,
            completed_cases: 0,
            failed_cases: 0,
            skipped_cases: 0,
        }
    }
}

/// Resume token for a deterministic shard.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakShardResumeToken {
    /// Stable token value.
    pub value: String,
}

impl SoakShardResumeToken {
    /// Build a token from shard id and config digest.
    pub fn new(shard_id: &SoakShardId, config_digest: &str) -> Self {
        let prefix_len = config_digest.len().min(12);
        let digest_prefix = &config_digest[..prefix_len];
        Self {
            value: format!("resume_{}_{}", shard_id.value, digest_prefix),
        }
    }
}

/// Shard execution summary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakShardSummary {
    /// Shard id.
    pub shard_id: SoakShardId,
    /// Status.
    pub status: SoakShardStatus,
    /// Progress.
    pub progress: SoakShardProgress,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Shard validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakShardValidationIssue {
    /// Issue path.
    pub path: String,
    /// Issue message.
    pub message: String,
}

/// Shard validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakShardValidation {
    /// True when no issues were found.
    pub valid: bool,
    /// Issues.
    pub issues: Vec<SoakShardValidationIssue>,
}

/// Deterministic shard planner.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SoakShardPlanner {
    config: SoakRunConfig,
}

impl SoakShardPlanner {
    /// Create a new planner.
    pub fn new(config: SoakRunConfig) -> Self {
        Self { config }
    }

    /// Build a deterministic shard plan.
    pub fn plan(&self) -> Result<SoakShardPlan> {
        plan_soak_shards(self.config.clone())
    }
}

/// Plan deterministic local soak shards.
pub fn plan_soak_shards(config: SoakRunConfig) -> Result<SoakShardPlan> {
    validate_soak_run_config(&config)?;
    let config_digest = compute_artifact_digest(
        &config,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    )?
    .hex_digest;

    let families = config.normalized_families();
    let mutations = config.normalized_mutations();
    let mut case_plans = Vec::new();
    for family in families {
        for seed in config.scope.seed_range.values() {
            let id = format!("soak_case_{}_seed_{seed:016x}", family.id_segment());
            case_plans.push(SoakCasePlan {
                id,
                family_kind: family,
                generator_seed: seed,
                generator_tunables: config.scope.generator_tunables.clone(),
                mutation_classes: mutations.clone(),
                trace_selection: "all_generated_and_primary_mutation_traces".to_string(),
                output_policy: config.output_policy.clone(),
                claim_boundary: ClaimBoundary::Level0DesignNote,
                notes: vec![
                    "Local soak case plan only.".to_string(),
                    "Local soak telemetry is not official benchmark evidence.".to_string(),
                ],
            });
        }
    }
    case_plans.sort_by(|left, right| left.id.cmp(&right.id));

    let shard_count = config.shard_config.shard_count;
    let mut assignments = vec![Vec::<SoakCaseId>::new(); shard_count];
    for (index, case) in case_plans.iter().enumerate() {
        let shard_index = index % shard_count;
        assignments[shard_index].push(case.id.clone());
    }

    let mut shard_manifests = Vec::new();
    for (index, assigned_case_ids) in assignments.into_iter().enumerate() {
        if assigned_case_ids.len() > config.limits.max_cases_per_shard {
            return Err(ZkBenchError::soak(
                "soak.shard_plan.assignments",
                format!(
                    "shard {index} case count {} exceeds max_cases_per_shard {}",
                    assigned_case_ids.len(),
                    config.limits.max_cases_per_shard
                ),
            ));
        }
        let shard_id = SoakShardId::from_index(index);
        let resume_token = SoakShardResumeToken::new(&shard_id, &config_digest);
        shard_manifests.push(SoakShardManifest {
            shard_id: shard_id.clone(),
            shard_index: index,
            shard_count,
            config_digest: config_digest.clone(),
            expected_case_count: assigned_case_ids.len(),
            assigned_case_ids,
            claim_boundary: ClaimBoundary::Level0DesignNote,
            output_policy: config.output_policy.clone(),
            resume_token: Some(resume_token),
            relative_artifact_refs: vec![
                format!("shards/{}/shard_manifest.json", shard_id.value),
                format!("shards/{}/checkpoint.json", shard_id.value),
                format!("shards/{}/telemetry.json", shard_id.value),
                format!("shards/{}/health_report.json", shard_id.value),
                format!("shards/{}/failure_corpus_index.json", shard_id.value),
            ],
            notes: vec![
                "Resumable shard manifest for a local soak run.".to_string(),
                "Shard manifests are Level0DesignNote artifacts.".to_string(),
            ],
        });
    }

    let plan = SoakShardPlan {
        config,
        config_digest,
        case_plans,
        shard_manifests,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec![
            "Deterministic shard plan; no system randomness or wall-clock ids are used."
                .to_string(),
            "Local soak telemetry is not official benchmark evidence.".to_string(),
        ],
    };
    validate_soak_shard_plan(&plan)?;
    Ok(plan)
}

/// Validate a full shard plan.
pub fn validate_soak_shard_plan(plan: &SoakShardPlan) -> Result<()> {
    let mut seen = std::collections::BTreeSet::new();
    for manifest in &plan.shard_manifests {
        let validation = validate_soak_shard_manifest(manifest);
        if !validation.valid {
            return Err(ZkBenchError::soak(
                "soak.shard_plan.manifests",
                format!("invalid shard manifest: {:?}", validation.issues),
            ));
        }
        if manifest.config_digest != plan.config_digest {
            return Err(ZkBenchError::soak(
                "soak.shard_plan.config_digest",
                "shard manifest config digest does not match plan config digest",
            ));
        }
        for case_id in &manifest.assigned_case_ids {
            if !seen.insert(case_id.clone()) {
                return Err(ZkBenchError::soak(
                    "soak.shard_plan.assigned_case_ids",
                    format!("case id {case_id} was assigned more than once"),
                ));
            }
        }
    }
    let planned = plan
        .case_plans
        .iter()
        .map(|case| case.id.clone())
        .collect::<std::collections::BTreeSet<_>>();
    if seen != planned {
        return Err(ZkBenchError::soak(
            "soak.shard_plan.assigned_case_ids",
            "assigned case ids do not match planned case ids",
        ));
    }
    Ok(())
}

/// Validate a shard manifest.
pub fn validate_soak_shard_manifest(manifest: &SoakShardManifest) -> SoakShardValidation {
    let mut issues = Vec::new();
    if manifest.shard_id.value.trim().is_empty() {
        issues.push(issue("manifest.shard_id", "shard id is empty"));
    }
    if manifest.shard_index >= manifest.shard_count {
        issues.push(issue(
            "manifest.shard_index",
            "shard index must be less than shard count",
        ));
    }
    if manifest.expected_case_count != manifest.assigned_case_ids.len() {
        issues.push(issue(
            "manifest.expected_case_count",
            "expected case count does not match assigned case ids",
        ));
    }
    let mut seen_case_ids = std::collections::BTreeSet::new();
    for (index, case_id) in manifest.assigned_case_ids.iter().enumerate() {
        if case_id.trim().is_empty() {
            issues.push(issue(
                format!("manifest.assigned_case_ids[{index}]"),
                "assigned case id is empty",
            ));
        }
        if !seen_case_ids.insert(case_id.clone()) {
            issues.push(issue(
                format!("manifest.assigned_case_ids[{index}]"),
                "assigned case id is duplicated",
            ));
        }
    }
    if manifest.claim_boundary != ClaimBoundary::Level0DesignNote {
        issues.push(issue(
            "manifest.claim_boundary",
            "shard manifest must remain Level0DesignNote",
        ));
    }
    for (index, artifact_ref) in manifest.relative_artifact_refs.iter().enumerate() {
        if artifact_ref.trim().is_empty() {
            issues.push(issue(
                format!("manifest.relative_artifact_refs[{index}]"),
                "artifact ref is empty",
            ));
        } else if artifact_ref.starts_with('/')
            || artifact_ref.contains("..")
            || artifact_ref.contains('\\')
        {
            issues.push(issue(
                format!("manifest.relative_artifact_refs[{index}]"),
                "artifact refs must be portable relative paths",
            ));
        }
    }
    SoakShardValidation {
        valid: issues.is_empty(),
        issues,
    }
}

fn issue(path: impl Into<String>, message: impl Into<String>) -> SoakShardValidationIssue {
    SoakShardValidationIssue {
        path: path.into(),
        message: message.into(),
    }
}

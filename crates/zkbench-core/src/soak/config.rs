//! Local soak run configuration.

use std::ops::Range;

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::ClaimBoundary;
use crate::generator::{FamilyKind, GeneratorTunables};
use crate::mutation::MutationClass;

/// Local soak run configuration id.
pub type SoakRunConfigId = String;

/// Local soak run configuration version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakRunConfigVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for SoakRunConfigVersion {
    fn default() -> Self {
        Self {
            value: "phase-k-local-soak-config-v0".to_string(),
        }
    }
}

/// Local soak run profile.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum SoakRunProfile {
    /// Tiny profile safe for unit and integration tests.
    Smoke,
    /// Focused profile for a small family or mutation class slice.
    Focused,
    /// Stable local regression profile.
    Regression,
    /// Larger local-only profile requiring explicit opt-in.
    NightlyLocal,
    /// Caller-provided profile.
    Custom,
}

/// Deterministic seed range.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakSeedRange {
    /// Inclusive first seed.
    pub start_inclusive: u64,
    /// Exclusive end seed.
    pub end_exclusive: u64,
}

impl SoakSeedRange {
    /// Construct a deterministic seed range.
    pub fn new(start_inclusive: u64, end_exclusive: u64) -> Self {
        Self {
            start_inclusive,
            end_exclusive,
        }
    }

    /// Seed count.
    pub fn len(&self) -> usize {
        if self.end_exclusive <= self.start_inclusive {
            0
        } else {
            (self.end_exclusive - self.start_inclusive) as usize
        }
    }

    /// True when no seeds are included.
    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }

    /// Enumerate seeds in stable order.
    pub fn values(&self) -> Vec<u64> {
        (self.start_inclusive..self.end_exclusive).collect()
    }
}

impl Default for SoakSeedRange {
    fn default() -> Self {
        Self::new(0, 2)
    }
}

/// Families included in a local soak run.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakFamilySelection {
    /// Selected family kinds.
    pub families: Vec<FamilyKind>,
}

impl SoakFamilySelection {
    /// Implemented local v0 families in deterministic order.
    pub fn implemented_v0() -> Self {
        Self {
            families: vec![
                FamilyKind::BaselineFsm,
                FamilyKind::BranchingFsm,
                FamilyKind::BoundedCounterLoop,
            ],
        }
    }

    /// Return selected families sorted and deduplicated.
    pub fn normalized(&self) -> Vec<FamilyKind> {
        let mut families = self.families.clone();
        families.sort();
        families.dedup();
        families
    }
}

impl Default for SoakFamilySelection {
    fn default() -> Self {
        Self::implemented_v0()
    }
}

/// Mutation passes included in a local soak run.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakMutationSelection {
    /// Selected mutation classes.
    pub mutation_classes: Vec<MutationClass>,
}

impl SoakMutationSelection {
    /// Implemented Phase D/E mutation classes in deterministic order.
    pub fn implemented_v0() -> Self {
        Self {
            mutation_classes: vec![
                MutationClass::MissingConstraints,
                MutationClass::CorruptedGuards,
                MutationClass::BadCounters,
            ],
        }
    }

    /// Return selected mutation classes sorted and deduplicated.
    pub fn normalized(&self) -> Vec<MutationClass> {
        let mut classes = self.mutation_classes.clone();
        classes.sort();
        classes.dedup();
        classes
    }
}

impl Default for SoakMutationSelection {
    fn default() -> Self {
        Self::implemented_v0()
    }
}

/// Shard count configuration.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakShardConfig {
    /// Number of deterministic shards.
    pub shard_count: usize,
}

impl Default for SoakShardConfig {
    fn default() -> Self {
        Self { shard_count: 2 }
    }
}

/// Soak output policy.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum SoakOutputPolicy {
    /// Write no benchmark packs.
    NoPacks,
    /// Write representative sampled packs up to a local limit.
    SampledPacks {
        /// Maximum sampled packs.
        max_packs: usize,
    },
    /// Write only packs for failed cases.
    FailurePacksOnly {
        /// Maximum failure packs.
        max_failure_packs: usize,
    },
    /// Write every pack while staying inside the configured limit.
    AllPacksWithinLimit {
        /// Maximum packs.
        max_packs: usize,
    },
}

impl SoakOutputPolicy {
    /// Test-safe sampled policy.
    pub fn sampled_packs_and_failures() -> Self {
        Self::SampledPacks { max_packs: 2 }
    }

    /// Maximum pack writes requested by this policy.
    pub fn max_pack_writes_requested(&self) -> usize {
        match self {
            Self::NoPacks => 0,
            Self::SampledPacks { max_packs } | Self::AllPacksWithinLimit { max_packs } => {
                *max_packs
            }
            Self::FailurePacksOnly { max_failure_packs } => *max_failure_packs,
        }
    }
}

impl Default for SoakOutputPolicy {
    fn default() -> Self {
        Self::NoPacks
    }
}

/// Telemetry collection policy.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakTelemetryPolicy {
    /// Collect internal local pipeline timings.
    pub collect_internal_durations: bool,
    /// Require all telemetry to stay internal-only.
    pub require_internal_only: bool,
    /// Require labels to avoid ZK backend performance terms.
    pub reject_zk_backend_performance_labels: bool,
}

impl Default for SoakTelemetryPolicy {
    fn default() -> Self {
        Self {
            collect_internal_durations: true,
            require_internal_only: true,
            reject_zk_backend_performance_labels: true,
        }
    }
}

/// Claim-boundary policy for Phase K artifacts.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakClaimBoundaryPolicy {
    /// Soak configs, shard plans, telemetry, reports, and corpus indexes stay here.
    pub soak_artifact_claim_boundary: ClaimBoundary,
    /// Local replay artifacts may reach this boundary.
    pub local_replay_claim_boundary_max: ClaimBoundary,
    /// Level2 or higher actual evidence is forbidden.
    pub forbid_level2_or_above: bool,
}

impl Default for SoakClaimBoundaryPolicy {
    fn default() -> Self {
        Self {
            soak_artifact_claim_boundary: ClaimBoundary::Level0DesignNote,
            local_replay_claim_boundary_max: ClaimBoundary::Level1LocalReplay,
            forbid_level2_or_above: true,
        }
    }
}

/// Local soak safety limits.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakLimits {
    /// Maximum family count.
    pub max_families: usize,
    /// Maximum seed count.
    pub max_seeds: usize,
    /// Maximum generated instance count.
    pub max_instances: usize,
    /// Maximum mutation applications.
    pub max_mutations: usize,
    /// Maximum trace evaluations.
    pub max_traces: usize,
    /// Maximum shard count.
    pub max_shards: usize,
    /// Maximum cases per shard.
    pub max_cases_per_shard: usize,
    /// Maximum pack writes.
    pub max_pack_writes: usize,
    /// Maximum failure corpus entries.
    pub max_failure_corpus_entries: usize,
    /// Output byte hint only.
    pub max_output_bytes_hint: usize,
    /// Internal duration hint only.
    pub max_internal_duration_ms_hint: u64,
}

impl SoakLimits {
    /// Small limits safe for normal tests.
    pub fn smoke() -> Self {
        Self::default()
    }

    /// Explicit larger local-only limits for future long local jobs.
    pub fn nightly_local_explicit() -> Self {
        Self {
            max_families: 3,
            max_seeds: 256,
            max_instances: 768,
            max_mutations: 2304,
            max_traces: 4096,
            max_shards: 64,
            max_cases_per_shard: 128,
            max_pack_writes: 128,
            max_failure_corpus_entries: 256,
            max_output_bytes_hint: 256 * 1024 * 1024,
            max_internal_duration_ms_hint: 12 * 60 * 60 * 1000,
        }
    }
}

impl Default for SoakLimits {
    fn default() -> Self {
        Self {
            max_families: 3,
            max_seeds: 8,
            max_instances: 24,
            max_mutations: 72,
            max_traces: 160,
            max_shards: 8,
            max_cases_per_shard: 8,
            max_pack_writes: 2,
            max_failure_corpus_entries: 16,
            max_output_bytes_hint: 1024 * 1024,
            max_internal_duration_ms_hint: 30_000,
        }
    }
}

/// Soak pipeline scope.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct SoakRunScope {
    /// Selected families.
    pub family_selection: SoakFamilySelection,
    /// Seed range.
    pub seed_range: SoakSeedRange,
    /// Selected mutation passes.
    pub mutation_selection: SoakMutationSelection,
    /// Generator tunables shared by planned cases.
    pub generator_tunables: GeneratorTunables,
}

/// Full local soak run configuration.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SoakRunConfig {
    /// Config id.
    pub id: SoakRunConfigId,
    /// Config schema version.
    pub version: SoakRunConfigVersion,
    /// Profile.
    pub profile: SoakRunProfile,
    /// Pipeline scope.
    pub scope: SoakRunScope,
    /// Shard config.
    pub shard_config: SoakShardConfig,
    /// Output policy.
    pub output_policy: SoakOutputPolicy,
    /// Telemetry policy.
    pub telemetry_policy: SoakTelemetryPolicy,
    /// Claim-boundary policy.
    pub claim_boundary_policy: SoakClaimBoundaryPolicy,
    /// Safety limits.
    pub limits: SoakLimits,
    /// Claim boundary for the config artifact.
    pub claim_boundary: ClaimBoundary,
    /// Explicit opt-in for `NightlyLocal`.
    pub allow_nightly_local: bool,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl SoakRunConfig {
    /// Test-safe smoke config.
    pub fn smoke() -> Self {
        build_smoke_soak_config()
    }

    /// Stable regression config that remains local-only.
    pub fn regression() -> Self {
        build_regression_soak_config()
    }

    /// Set selected families.
    pub fn with_families(mut self, families: Vec<FamilyKind>) -> Self {
        self.scope.family_selection = SoakFamilySelection { families };
        self
    }

    /// Set seed range.
    pub fn with_seed_range(mut self, range: Range<u64>) -> Self {
        self.scope.seed_range = SoakSeedRange::new(range.start, range.end);
        self
    }

    /// Set mutation passes.
    pub fn with_mutation_passes(mut self, mutation_classes: Vec<MutationClass>) -> Self {
        self.scope.mutation_selection = SoakMutationSelection { mutation_classes };
        self
    }

    /// Set shard count.
    pub fn with_shard_count(mut self, shard_count: usize) -> Self {
        self.shard_config.shard_count = shard_count;
        self
    }

    /// Set output policy.
    pub fn with_output_policy(mut self, output_policy: SoakOutputPolicy) -> Self {
        self.output_policy = output_policy;
        self
    }

    /// Set safety limits.
    pub fn with_limits(mut self, limits: SoakLimits) -> Self {
        self.limits = limits;
        self
    }

    /// Explicitly allow a larger NightlyLocal profile.
    pub fn allow_nightly_local(mut self, allow: bool) -> Self {
        self.allow_nightly_local = allow;
        self
    }

    /// Validate this config.
    pub fn validate(&self) -> Result<()> {
        validate_soak_run_config(self)
    }

    /// Return deterministic family selection.
    pub fn normalized_families(&self) -> Vec<FamilyKind> {
        self.scope.family_selection.normalized()
    }

    /// Return deterministic mutation selection.
    pub fn normalized_mutations(&self) -> Vec<MutationClass> {
        self.scope.mutation_selection.normalized()
    }

    /// Planned case count before sharding.
    pub fn planned_case_count(&self) -> usize {
        self.normalized_families()
            .len()
            .saturating_mul(self.scope.seed_range.len())
    }

    /// Planned mutation application count.
    pub fn planned_mutation_count(&self) -> usize {
        self.planned_case_count()
            .saturating_mul(self.normalized_mutations().len())
    }
}

/// Build a smoke soak config.
pub fn build_smoke_soak_config() -> SoakRunConfig {
    SoakRunConfig {
        id: "phase_k_smoke_soak_config".to_string(),
        version: SoakRunConfigVersion::default(),
        profile: SoakRunProfile::Smoke,
        scope: SoakRunScope::default(),
        shard_config: SoakShardConfig::default(),
        output_policy: SoakOutputPolicy::NoPacks,
        telemetry_policy: SoakTelemetryPolicy::default(),
        claim_boundary_policy: SoakClaimBoundaryPolicy::default(),
        limits: SoakLimits::smoke(),
        claim_boundary: ClaimBoundary::Level0DesignNote,
        allow_nightly_local: false,
        notes: vec![
            "Local soak telemetry is not official benchmark evidence.".to_string(),
            "Internal timing telemetry is not ZK backend performance.".to_string(),
        ],
    }
}

/// Build a local regression soak config.
pub fn build_regression_soak_config() -> SoakRunConfig {
    SoakRunConfig {
        id: "phase_k_regression_soak_config".to_string(),
        profile: SoakRunProfile::Regression,
        scope: SoakRunScope {
            seed_range: SoakSeedRange::new(0, 4),
            ..SoakRunScope::default()
        },
        shard_config: SoakShardConfig { shard_count: 4 },
        output_policy: SoakOutputPolicy::FailurePacksOnly {
            max_failure_packs: 2,
        },
        ..build_smoke_soak_config()
    }
}

/// Validate a soak run config.
pub fn validate_soak_run_config(config: &SoakRunConfig) -> Result<()> {
    if config.id.trim().is_empty() {
        return Err(ZkBenchError::soak(
            "soak.config.id",
            "soak config id is empty",
        ));
    }
    if config.claim_boundary != ClaimBoundary::Level0DesignNote {
        return Err(ZkBenchError::soak(
            "soak.config.claim_boundary",
            "soak config must remain Level0DesignNote",
        ));
    }
    if config.claim_boundary_policy.soak_artifact_claim_boundary != ClaimBoundary::Level0DesignNote
    {
        return Err(ZkBenchError::soak(
            "soak.config.claim_boundary_policy.soak_artifact_claim_boundary",
            "Phase K soak artifacts must remain Level0DesignNote",
        ));
    }
    if config.claim_boundary_policy.local_replay_claim_boundary_max
        > ClaimBoundary::Level1LocalReplay
    {
        return Err(ZkBenchError::soak(
            "soak.config.claim_boundary_policy.local_replay_claim_boundary_max",
            "local replay artifacts must remain Level1LocalReplay or lower",
        ));
    }
    if matches!(config.profile, SoakRunProfile::NightlyLocal) && !config.allow_nightly_local {
        return Err(ZkBenchError::soak(
            "soak.config.profile",
            "NightlyLocal requires explicit allow_nightly_local(true)",
        ));
    }

    let families = config.normalized_families();
    if families.is_empty() {
        return Err(ZkBenchError::soak(
            "soak.config.scope.family_selection",
            "at least one family is required",
        ));
    }
    if families.len() > config.limits.max_families {
        return Err(ZkBenchError::soak(
            "soak.config.scope.family_selection",
            format!(
                "family count {} exceeds max_families {}",
                families.len(),
                config.limits.max_families
            ),
        ));
    }
    if let Some(family) = families.iter().find(|family| !family.is_implemented()) {
        return Err(ZkBenchError::soak(
            "soak.config.scope.family_selection",
            format!("{family:?} is not implemented for local soak runs"),
        ));
    }
    if config.scope.seed_range.is_empty() {
        return Err(ZkBenchError::soak(
            "soak.config.scope.seed_range",
            "seed range must not be empty",
        ));
    }
    if config.scope.seed_range.len() > config.limits.max_seeds {
        return Err(ZkBenchError::soak(
            "soak.config.scope.seed_range",
            format!(
                "seed count {} exceeds max_seeds {}",
                config.scope.seed_range.len(),
                config.limits.max_seeds
            ),
        ));
    }
    let mutations = config.normalized_mutations();
    if mutations.is_empty() {
        return Err(ZkBenchError::soak(
            "soak.config.scope.mutation_selection",
            "at least one mutation class is required",
        ));
    }
    if let Some(class) = mutations
        .iter()
        .find(|class| !mutation_class_is_implemented(**class))
    {
        return Err(ZkBenchError::soak(
            "soak.config.scope.mutation_selection",
            format!("{class:?} is not implemented for Phase K local soak runs"),
        ));
    }
    if config.shard_config.shard_count == 0 {
        return Err(ZkBenchError::soak(
            "soak.config.shard_config.shard_count",
            "shard count must be greater than zero",
        ));
    }
    if config.shard_config.shard_count > config.limits.max_shards {
        return Err(ZkBenchError::soak(
            "soak.config.shard_config.shard_count",
            format!(
                "shard count {} exceeds max_shards {}",
                config.shard_config.shard_count, config.limits.max_shards
            ),
        ));
    }
    if config.planned_case_count() > config.limits.max_instances {
        return Err(ZkBenchError::soak(
            "soak.config.scope",
            format!(
                "planned case count {} exceeds max_instances {}",
                config.planned_case_count(),
                config.limits.max_instances
            ),
        ));
    }
    if config.planned_mutation_count() > config.limits.max_mutations {
        return Err(ZkBenchError::soak(
            "soak.config.scope",
            format!(
                "planned mutation count {} exceeds max_mutations {}",
                config.planned_mutation_count(),
                config.limits.max_mutations
            ),
        ));
    }
    if config.output_policy.max_pack_writes_requested() > config.limits.max_pack_writes {
        return Err(ZkBenchError::soak(
            "soak.config.output_policy",
            format!(
                "pack write request {} exceeds max_pack_writes {}",
                config.output_policy.max_pack_writes_requested(),
                config.limits.max_pack_writes
            ),
        ));
    }
    Ok(())
}

pub(crate) fn mutation_class_is_implemented(class: MutationClass) -> bool {
    matches!(
        class,
        MutationClass::MissingConstraints
            | MutationClass::CorruptedGuards
            | MutationClass::BadCounters
    )
}

// Operator-facing soak campaign runner.
//
// Wraps the existing shipped `plan_soak_shards` and `run_soak_campaign`
// library surface so an operator can run an approved, repo-external local
// soak campaign without writing Rust. This is NOT a general command-line
// tool: it takes no CLI flags, uses no argument-parsing dependency, and reads
// every input from a fixed authorized set of environment variables.
//
// A successful run produces `Level0DesignNote` local soak telemetry only. It
// is not official benchmark evidence, not accepted evidence, not external
// replay evidence, not ZK backend performance, not formal evidence, not
// proof, not semantic correctness, not production readiness, and not global
// software-agent uniqueness.

use std::collections::BTreeMap;
use std::path::PathBuf;
use std::process::ExitCode;

use serde::Serialize;

use zkbench_core::{
    build_regression_soak_config, build_smoke_soak_config, plan_soak_shards, run_soak_campaign,
    validate_soak_campaign_config, ClaimBoundary, FamilyKind, LocalSoakRunnerConfig, MutationClass,
    SoakCampaignApproval, SoakCampaignArtifactRootPolicy, SoakCampaignConfig, SoakRunConfig,
};

/// Fixed acknowledgement literal. Operators must echo this exactly via
/// `ZKBENCH_SOAK_ACK` to acknowledge that this binary produces local soak
/// telemetry only and writes outputs only under the declared artifact root.
const FIXED_ACK: &str =
    "I acknowledge this soak campaign produces local Level0DesignNote telemetry only.";

/// Required nonclaim strings, mirrored from the shipped soak library.
const NONCLAIM_TELEMETRY: &str = "Local soak telemetry is not official benchmark evidence.";
const NONCLAIM_TIMING: &str = "Internal timing telemetry is not ZK backend performance.";

/// Authorized environment variable names. The source-contract test asserts
/// the example reads no other `std::env::var` keys.
const ENV_ACK: &str = "ZKBENCH_SOAK_ACK";
const ENV_CAMPAIGN_ID: &str = "ZKBENCH_SOAK_CAMPAIGN_ID";
const ENV_ARTIFACT_ROOT: &str = "ZKBENCH_SOAK_ARTIFACT_ROOT";
const ENV_APPROVED_BY: &str = "ZKBENCH_SOAK_APPROVED_BY";
const ENV_APPROVAL_STATEMENT: &str = "ZKBENCH_SOAK_APPROVAL_STATEMENT";
const ENV_PROFILE: &str = "ZKBENCH_SOAK_PROFILE";
const ENV_FAMILIES: &str = "ZKBENCH_SOAK_FAMILIES";
const ENV_SEED_START: &str = "ZKBENCH_SOAK_SEED_START";
const ENV_SEED_END: &str = "ZKBENCH_SOAK_SEED_END";
const ENV_SHARD_COUNT: &str = "ZKBENCH_SOAK_SHARD_COUNT";

#[derive(Debug, Serialize)]
struct OperatorSoakSummary {
    campaign_id: String,
    claim_boundary: String,
    profile: String,
    shard_count: usize,
    case_count: usize,
    replay_completed_count: usize,
    replay_failed_count: usize,
    traces_evaluated: usize,
    local_oracle_accepted_count: usize,
    local_oracle_rejected_count: usize,
    local_oracle_capability_gap_count: usize,
    mutation_variant_count: usize,
    mutation_no_target_count: usize,
    pack_write_count: usize,
    failure_count: usize,
    nonclaims: Vec<&'static str>,
}

fn fail(message: &str) -> ! {
    eprintln!("operator_soak_campaign: {message}");
    std::process::exit(1);
}

fn require_env(name: &str) -> String {
    match std::env::var(name) {
        Ok(value) if !value.trim().is_empty() => value,
        Ok(_) => fail(&format!("{name} must be non-empty")),
        Err(_) => fail(&format!("{name} must be set")),
    }
}

fn optional_env(name: &str) -> Option<String> {
    match std::env::var(name) {
        Ok(value) if !value.trim().is_empty() => Some(value),
        _ => None,
    }
}

fn build_family_lookup() -> BTreeMap<String, FamilyKind> {
    [
        FamilyKind::BaselineFsm,
        FamilyKind::BranchingFsm,
        FamilyKind::BoundedCounterLoop,
        FamilyKind::NestedLoop,
        FamilyKind::GuardHeavyMachine,
        FamilyKind::RecursiveEnvelope,
        FamilyKind::MemoryHeavyStateMachine,
        FamilyKind::PublicPrivateBoundaryStress,
        FamilyKind::ZkMlControlFlowMixed,
    ]
    .into_iter()
    .map(|kind| (kind.id_segment().to_string(), kind))
    .collect()
}

fn parse_families(raw: &str) -> Vec<FamilyKind> {
    let lookup = build_family_lookup();
    let mut families = Vec::new();
    for segment in raw.split(',').map(str::trim).filter(|s| !s.is_empty()) {
        match lookup.get(segment) {
            Some(kind) => families.push(*kind),
            None => fail(&format!(
                "ZKBENCH_SOAK_FAMILIES contains unknown family id segment '{segment}'"
            )),
        }
    }
    if families.is_empty() {
        fail("ZKBENCH_SOAK_FAMILIES must list at least one family id segment");
    }
    families
}

fn parse_usize(name: &str, raw: &str) -> usize {
    raw.parse::<usize>()
        .unwrap_or_else(|_| fail(&format!("{name} must be a non-negative integer")))
}

fn build_config() -> SoakRunConfig {
    let profile = optional_env(ENV_PROFILE).unwrap_or_else(|| "smoke".to_string());
    let mut config = match profile.as_str() {
        "smoke" => build_smoke_soak_config(),
        "regression" => build_regression_soak_config(),
        other => fail(&format!(
            "ZKBENCH_SOAK_PROFILE must be 'smoke' or 'regression', got '{other}'"
        )),
    };

    if let Some(raw) = optional_env(ENV_FAMILIES) {
        config = config.with_families(parse_families(&raw));
    }
    let seed_start = optional_env(ENV_SEED_START)
        .map(|raw| parse_usize(ENV_SEED_START, &raw))
        .unwrap_or(0);
    let seed_end = optional_env(ENV_SEED_END)
        .map(|raw| parse_usize(ENV_SEED_END, &raw))
        .unwrap_or(4);
    if seed_end <= seed_start {
        fail(&format!(
            "{ENV_SEED_END} ({seed_end}) must be greater than {ENV_SEED_START} ({seed_start})"
        ));
    }
    config = config.with_seed_range(seed_start as u64..seed_end as u64);
    if let Some(raw) = optional_env(ENV_SHARD_COUNT) {
        let shard_count = parse_usize(ENV_SHARD_COUNT, &raw);
        if shard_count == 0 {
            fail(&format!("{ENV_SHARD_COUNT} must be at least 1"));
        }
        config = config.with_shard_count(shard_count);
    }

    config
        .validate()
        .unwrap_or_else(|err| fail(&format!("soak run config validation failed: {err:?}")));
    config
}

fn build_campaign_config(
    campaign_id: String,
    artifact_root: PathBuf,
    approved_by: String,
    approval_statement: String,
) -> SoakCampaignConfig {
    let campaign_config = SoakCampaignConfig {
        campaign_id: campaign_id.clone(),
        approval: SoakCampaignApproval {
            approved_by,
            approval_statement,
            approved_at_ms: 0,
        },
        artifact_root_policy: SoakCampaignArtifactRootPolicy {
            artifact_root,
            declared_outside_repo_or_ignored: true,
        },
        runner_config: LocalSoakRunnerConfig::default(),
        notes: vec![NONCLAIM_TELEMETRY.to_string(), NONCLAIM_TIMING.to_string()],
    };
    validate_soak_campaign_config(&campaign_config)
        .unwrap_or_else(|err| fail(&format!("soak campaign config validation failed: {err:?}")));
    campaign_config
}

fn build_summary(
    campaign_id: String,
    profile: String,
    case_count: usize,
    result: &zkbench_core::SoakCampaignResult,
) -> OperatorSoakSummary {
    let mut replay_completed_count = 0usize;
    let mut replay_failed_count = 0usize;
    let mut traces_evaluated = 0usize;
    let mut local_oracle_accepted_count = 0usize;
    let mut local_oracle_rejected_count = 0usize;
    let mut local_oracle_capability_gap_count = 0usize;
    let mut mutation_variant_count = 0usize;
    let mut mutation_no_target_count = 0usize;
    let mut pack_write_count = 0usize;
    let mut failure_count = 0usize;

    for outcome in &result.shard_outcomes {
        let counters = &outcome.run_result.telemetry_report.snapshot.counters;
        replay_completed_count += counters.local_replay_completed_count;
        replay_failed_count += counters.local_replay_failed_count;
        traces_evaluated += counters.traces_evaluated;
        local_oracle_accepted_count += counters.local_oracle_accepted_count;
        local_oracle_rejected_count += counters.local_oracle_rejected_count;
        local_oracle_capability_gap_count += counters.local_oracle_capability_gap_count;
        mutation_variant_count += counters.mutation_variant_count;
        mutation_no_target_count += counters.mutation_no_target_count;
        pack_write_count += counters.pack_write_count;
        failure_count += counters.failure_count;
    }

    OperatorSoakSummary {
        campaign_id,
        claim_boundary: format!("{:?}", result.claim_boundary),
        profile,
        shard_count: result.shard_outcomes.len(),
        case_count,
        replay_completed_count,
        replay_failed_count,
        traces_evaluated,
        local_oracle_accepted_count,
        local_oracle_rejected_count,
        local_oracle_capability_gap_count,
        mutation_variant_count,
        mutation_no_target_count,
        pack_write_count,
        failure_count,
        nonclaims: vec![NONCLAIM_TELEMETRY, NONCLAIM_TIMING],
    }
}

fn main() -> ExitCode {
    let ack = require_env(ENV_ACK);
    if ack != FIXED_ACK {
        fail(&format!(
            "{ENV_ACK} did not match the required acknowledgement literal"
        ));
    }

    let campaign_id = require_env(ENV_CAMPAIGN_ID);
    let artifact_root = PathBuf::from(require_env(ENV_ARTIFACT_ROOT));
    let approved_by = require_env(ENV_APPROVED_BY);
    let approval_statement = require_env(ENV_APPROVAL_STATEMENT);
    let profile = optional_env(ENV_PROFILE).unwrap_or_else(|| "smoke".to_string());

    if !artifact_root.is_absolute() {
        fail(&format!(
            "{ENV_ARTIFACT_ROOT} must be an absolute path, got '{}'",
            artifact_root.display()
        ));
    }

    let config = build_config();
    let case_count_estimate = config.planned_case_count();
    let plan = plan_soak_shards(config)
        .unwrap_or_else(|err| fail(&format!("shard planning failed: {err:?}")));
    let case_count = plan.case_plans.len();
    // Defensive double-check that the planner agreed with the config estimate.
    if case_count != case_count_estimate {
        fail(&format!(
            "shard planner case count {case_count} disagrees with config estimate {case_count_estimate}"
        ));
    }

    let campaign_config = build_campaign_config(
        campaign_id.clone(),
        artifact_root,
        approved_by,
        approval_statement,
    );

    let result = run_soak_campaign(&campaign_config, plan)
        .unwrap_or_else(|err| fail(&format!("soak campaign failed: {err:?}")));

    if result.contains_zk_backend_performance_claims() {
        fail("internal invariant violation: campaign must not claim ZK backend performance");
    }
    if result.claim_boundary > ClaimBoundary::Level0DesignNote {
        fail("internal invariant violation: campaign exceeded Level0DesignNote");
    }

    let summary = build_summary(campaign_id, profile, case_count, &result);
    match serde_json::to_string_pretty(&summary) {
        Ok(json) => println!("{json}"),
        Err(err) => fail(&format!("summary serialization failed: {err}")),
    }

    // Reference the MutationClass import so the example documents the
    // mutation-selection surface even when ZKBENCH_SOAK_FAMILIES is unset;
    // the default profile already carries a safe mutation set.
    let _ = MutationClass::BadCounters;

    ExitCode::SUCCESS
}

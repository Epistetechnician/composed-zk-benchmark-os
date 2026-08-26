//! Provider-free operator example for the local strategy campaign state slice.
//!
//! This is a one-command validation/assessment workflow over the repository
//! owned local target corpus. It uses fixed equal work units, fresh local
//! replay per policy, and one-way assessment finalization. It writes no files,
//! uses no network, and emits no accepted evidence or benchmark claim.

use zkbench_core::{
    build_smoke_soak_config, BaselineCampaignConfig, BaselineCampaignRunner, ExplorationRunConfig,
    FamilyKind, MutationClass,
};

fn main() {
    let base = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm, FamilyKind::BranchingFsm])
        .with_mutation_passes(vec![
            MutationClass::MissingConstraints,
            MutationClass::CorruptedGuards,
        ])
        .with_seed_range(0..4)
        .with_shard_count(2);
    let exploration = ExplorationRunConfig::new(base)
        .with_run_id("operator_exploration_baseline_matrix")
        .with_budgets(2, 1, 4, 17);
    let config = BaselineCampaignConfig::new(exploration)
        .with_campaign_id("operator_exploration_baseline_matrix");
    let runner = BaselineCampaignRunner::new(config).expect("campaign config must validate");
    let mut result = runner
        .run_validation()
        .expect("local baseline validation must complete");
    println!(
        "run={} phase=validation policies={} winner={:?} metric={} claim_boundary={:?}",
        result.campaign_id,
        result.records.len(),
        result.validation_winner,
        result.validation_comparison.metric_id,
        result.claim_boundary
    );
    runner
        .finalize_assessment(&mut result)
        .expect("held-out local assessment must finalize");
    let assessment = result
        .assessment_comparison
        .as_ref()
        .expect("assessment comparison must exist after finalization");
    println!(
        "run={} phase=assessment policies={} validation_winner={:?} rows={} finalized={} claim_boundary={:?}",
        result.campaign_id,
        result.records.len(),
        result.validation_winner,
        assessment.rows.len(),
        result.finalized,
        result.claim_boundary
    );
}

//! Provider-free independent campaign assessment example.
//!
//! This example runs two disjoint local seed domains with equal budgets, then
//! explicitly finalizes held-out assessment domains and prints the typed
//! promotion gate. It writes no files, uses no network, and emits no accepted
//! evidence or benchmark claim.

use zkbench_core::{
    BaselineCampaignConfig, ExplorationRunConfig, FamilyKind, IndependentCampaignSuiteConfig,
    IndependentCampaignSuiteRunner, MutationClass,
};

fn campaign(start: u64, end: u64, suffix: &str) -> BaselineCampaignConfig {
    let base = zkbench_core::build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm, FamilyKind::BranchingFsm])
        .with_mutation_passes(vec![
            MutationClass::MissingConstraints,
            MutationClass::CorruptedGuards,
        ])
        .with_seed_range(start..end)
        .with_shard_count(2);
    BaselineCampaignConfig::new(
        ExplorationRunConfig::new(base)
            .with_run_id(format!("operator_assessment_suite_{suffix}"))
            .with_budgets(2, 1, 4, 17),
    )
    .with_campaign_id(format!("operator_assessment_suite_campaign_{suffix}"))
}

fn main() {
    let config = IndependentCampaignSuiteConfig::new(
        "operator_assessment_suite",
        vec![campaign(0, 4, "a"), campaign(4, 8, "b")],
    );
    let runner = IndependentCampaignSuiteRunner::new(config)
        .expect("independent campaign suite must validate");
    let mut result = runner
        .run_validation()
        .expect("validation campaigns must complete");
    println!(
        "suite={} phase=validation campaigns={} candidate={:?}",
        result.suite_id,
        result.validation_comparison.campaign_count,
        result.validation_comparison.candidate_policy,
    );
    runner
        .finalize_assessment(&mut result)
        .expect("assessment campaigns must finalize");
    let gate = result
        .promotion_gate
        .as_ref()
        .expect("finalized suite must contain a promotion gate");
    println!(
        "suite={} phase=assessment candidate={:?} improvements={}/{} promoted={} claim_boundary={:?}",
        result.suite_id,
        gate.candidate_policy,
        gate.observed_assessment_improvements,
        gate.required_assessment_improvements,
        gate.promoted,
        gate.claim_boundary,
    );
}

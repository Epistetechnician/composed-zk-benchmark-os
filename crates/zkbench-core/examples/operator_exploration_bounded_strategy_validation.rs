//! Provider-free bounded strategy validation with explicit policy metrics.
//!
//! This example evaluates the fixed baselines and BeamSearch on a smaller
//! deterministic case budget. The case budget is applied after policy ordering
//! so the search surface can affect which local cases are reached. Assessment
//! results remain sealed until explicit finalization.

use zkbench_core::{
    BaselineCampaignConfig, ExplorationPhase, ExplorationRunConfig, IndependentCampaignSuiteConfig,
    IndependentCampaignSuiteRunner,
};

fn campaign(start: u64, end: u64, suffix: &str) -> BaselineCampaignConfig {
    let base = zkbench_core::build_regression_soak_config()
        .with_seed_range(start..end)
        .with_shard_count(2);
    BaselineCampaignConfig::new(
        ExplorationRunConfig::new(base)
            .with_run_id(format!("bounded_strategy_validation_{suffix}"))
            .with_budgets(2, 1, 4, 17)
            .with_case_budget(3),
    )
    .with_campaign_id(format!("bounded_strategy_validation_campaign_{suffix}"))
}

fn print_rows(phase: ExplorationPhase, rows: &[zkbench_core::IndependentPolicyAggregateRow]) {
    for row in rows {
        println!(
            "phase={phase:?} policy={:?} metrics={:?} total={} strict_improvements={}",
            row.kind, row.metric_values, row.total_metric_value, row.strict_improvement_count
        );
    }
}

fn main() {
    let config = IndependentCampaignSuiteConfig::new(
        "bounded_strategy_validation",
        vec![campaign(0, 4, "a"), campaign(4, 8, "b")],
    );
    let runner = IndependentCampaignSuiteRunner::new(config)
        .expect("bounded independent strategy suite must validate");
    let mut result = runner
        .run_validation()
        .expect("bounded validation campaigns must complete");
    print_rows(
        ExplorationPhase::Validation,
        &result.validation_comparison.rows,
    );
    println!(
        "validation_candidate_policy={:?}",
        result.validation_comparison.candidate_policy
    );

    runner
        .finalize_assessment(&mut result)
        .expect("bounded assessment campaigns must finalize");
    let assessment = result
        .assessment_comparison
        .as_ref()
        .expect("assessment comparison must exist after finalization");
    print_rows(ExplorationPhase::FinalizedAssessment, &assessment.rows);
    let gate = result
        .promotion_gate
        .as_ref()
        .expect("finalized suite must contain a promotion gate");
    println!(
        "assessment_candidate={:?} improvements={}/{} promoted={} claim_boundary={:?}",
        gate.candidate_policy,
        gate.observed_assessment_improvements,
        gate.required_assessment_improvements,
        gate.promoted,
        gate.claim_boundary,
    );
}

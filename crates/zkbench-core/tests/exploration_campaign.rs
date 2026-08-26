//! Tests for state slice
//! `antithesis-inspired-deterministic-exploration-v1-real-target-campaign-matrix`.

use std::collections::BTreeSet;

use zkbench_core::{
    deserialize_baseline_campaign_result_json, serialize_baseline_campaign_result_json,
    BaselineCampaignConfig, BaselineCampaignRunner, BaselinePolicyKind, DeterministicExplorer,
    ExplorationRunConfig, ExplorerPolicy, FamilyKind, LocalTargetAdapter, LocalTargetCorpus,
    MutationClass, PRIMARY_METRIC_ID,
};

fn campaign_config() -> BaselineCampaignConfig {
    let base = zkbench_core::build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm, FamilyKind::BranchingFsm])
        .with_mutation_passes(vec![
            MutationClass::MissingConstraints,
            MutationClass::CorruptedGuards,
        ])
        .with_seed_range(0..4)
        .with_shard_count(2);
    BaselineCampaignConfig::new(
        ExplorationRunConfig::new(base)
            .with_run_id("baseline_campaign_test")
            .with_budgets(2, 1, 4, 17),
    )
    .with_campaign_id("baseline_campaign_test_matrix")
}

#[test]
fn target_adapter_retains_ir_mutation_replay_oracle_and_corpus_provenance() {
    let config = campaign_config();
    let corpus = LocalTargetCorpus::from_exploration_config(&config.exploration)
        .expect("target corpus should build");
    let adapter = LocalTargetAdapter::new(corpus).expect("adapter should build");
    let explorer =
        DeterministicExplorer::new(config.exploration.clone()).expect("explorer should build");
    let policy = ExplorerPolicy::from_config(&config.exploration.base_soak_config);
    let run = adapter
        .run_validation_policy(&explorer, &policy)
        .expect("target policy should run");

    assert_eq!(run.primary_metric.metric_id, PRIMARY_METRIC_ID);
    assert!(!run.case_observations.is_empty());
    assert!(run
        .case_observations
        .iter()
        .all(|case| !case.semantic_irs.is_empty()));
    assert!(run
        .case_observations
        .iter()
        .all(|case| !case.replay_manifests.is_empty()));
    assert!(run
        .case_observations
        .iter()
        .all(|case| !case.replay_results.is_empty()));
    assert!(run
        .case_observations
        .iter()
        .all(|case| !case.oracle_outcomes.is_empty()));
    assert!(run
        .case_observations
        .iter()
        .all(|case| case.replay_manifests.len() == case.replay_results.len()));
    assert!(run
        .case_observations
        .iter()
        .any(|case| !case.mutation_provenance.is_empty()));
    assert!(run
        .case_observations
        .iter()
        .any(|case| !case.failure_corpus_entries.is_empty()));
    assert!(run.primary_metric.work_units.case_count > 0);
    run.validate().expect("target run should validate");
}

#[test]
fn baseline_matrix_is_equal_budget_deterministic_and_seals_assessment() {
    let config = campaign_config();
    let runner = BaselineCampaignRunner::new(config.clone()).expect("campaign should validate");
    let first = runner
        .run_validation()
        .expect("validation campaign should run");
    let second = runner
        .run_validation()
        .expect("second validation campaign should run");

    assert_eq!(first.records.len(), 5);
    assert!(first.assessment_comparison.is_none());
    assert!(!first.finalized);
    assert!(first
        .records
        .iter()
        .all(|record| record.assessment_run.is_none()));
    assert_eq!(
        first.validation_winner,
        first.validation_comparison.validation_winner
    );
    assert!(first
        .records
        .iter()
        .all(|record| record.validation_run.primary_metric.metric_id == PRIMARY_METRIC_ID));
    let allocation_keys = first
        .records
        .iter()
        .map(|record| record.validation_run.primary_metric.work_units)
        .map(|units| {
            (
                units.case_count,
                units.shard_count,
                units.mutation_attempt_count,
            )
        })
        .collect::<BTreeSet<_>>();
    assert_eq!(allocation_keys.len(), 1);

    let first_json = serialize_baseline_campaign_result_json(&first)
        .expect("validation result should serialize");
    let second_json = serialize_baseline_campaign_result_json(&second)
        .expect("second validation result should serialize");
    assert_eq!(first_json, second_json);
    let resumed = runner
        .resume_validation(first.checkpoint.clone())
        .expect("validation checkpoint should resume");
    assert_eq!(
        serialize_baseline_campaign_result_json(&first).expect("first JSON"),
        serialize_baseline_campaign_result_json(&resumed).expect("resumed JSON")
    );
    let decoded = deserialize_baseline_campaign_result_json(&first_json, &config)
        .expect("validation result should deserialize");
    assert_eq!(
        first_json,
        serialize_baseline_campaign_result_json(&decoded).expect("round trip")
    );

    let validation_case_ids = first
        .records
        .iter()
        .find(|record| record.kind == BaselinePolicyKind::StableDigest)
        .expect("stable baseline should exist")
        .validation_run
        .case_observations
        .iter()
        .map(|case| case.case_id.clone())
        .collect::<BTreeSet<_>>();
    let retained_validation_corpus_case_ids = first
        .target_corpus
        .plan
        .case_plans
        .iter()
        .map(|case| case.id.clone())
        .collect::<BTreeSet<_>>();

    let mut finalized = first;
    runner
        .finalize_assessment(&mut finalized)
        .expect("assessment should finalize");
    assert!(finalized.finalized);
    assert!(finalized.assessment_comparison.is_some());
    assert!(finalized
        .records
        .iter()
        .all(|record| record.assessment_run.is_some()));
    let assessment_case_ids = finalized
        .records
        .iter()
        .find(|record| record.kind == BaselinePolicyKind::StableDigest)
        .expect("stable baseline should exist")
        .assessment_run
        .as_ref()
        .expect("assessment should exist")
        .case_observations
        .iter()
        .map(|case| case.case_id.clone())
        .collect::<BTreeSet<_>>();
    assert!(validation_case_ids.is_disjoint(&assessment_case_ids));
    assert!(retained_validation_corpus_case_ids.is_disjoint(&assessment_case_ids));
    assert!(assessment_case_ids
        .iter()
        .all(|case_id| !first_json.contains(case_id)));
    assert!(finalized
        .records
        .iter()
        .filter_map(|record| record.beam_search_result.as_ref())
        .all(|search| search.finalized));
    assert!(runner.finalize_assessment(&mut finalized).is_err());
}

#[test]
fn target_adapter_rejects_policy_that_changes_equal_allocation_budget() {
    let config = campaign_config();
    let corpus = LocalTargetCorpus::from_exploration_config(&config.exploration)
        .expect("target corpus should build");
    let adapter = LocalTargetAdapter::new(corpus).expect("adapter should build");
    let explorer =
        DeterministicExplorer::new(config.exploration.clone()).expect("explorer should build");
    let mut policy = ExplorerPolicy::from_config(&config.exploration.base_soak_config);
    policy.family_order.pop();
    assert!(adapter.run_validation_policy(&explorer, &policy).is_err());
}

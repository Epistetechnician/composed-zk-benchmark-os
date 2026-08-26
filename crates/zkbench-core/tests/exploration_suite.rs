//! Tests for state slice
//! `antithesis-inspired-deterministic-exploration-v1-independent-assessment-suite`.

use std::collections::BTreeSet;

use zkbench_core::{
    deserialize_independent_campaign_suite_json, serialize_independent_campaign_suite_json,
    BaselineCampaignConfig, BaselinePolicyKind, ExplorationRunConfig, FamilyKind,
    IndependentCampaignSuiteConfig, IndependentCampaignSuiteRunner, MutationClass,
};

fn campaign_config(start: u64, end: u64, suffix: &str) -> BaselineCampaignConfig {
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
            .with_run_id(format!("independent_suite_{suffix}"))
            .with_budgets(2, 1, 4, 17),
    )
    .with_campaign_id(format!("independent_suite_campaign_{suffix}"))
}

fn suite_config() -> IndependentCampaignSuiteConfig {
    IndependentCampaignSuiteConfig::new(
        "independent_suite_test",
        vec![campaign_config(0, 4, "a"), campaign_config(4, 8, "b")],
    )
    .with_minimum_assessment_improvements(2)
}

#[test]
fn independent_suite_is_deterministic_and_seals_assessment_until_finalization() {
    let config = suite_config();
    let runner = IndependentCampaignSuiteRunner::new(config.clone()).expect("suite validates");
    let first = runner
        .run_validation()
        .expect("validation suite should run");
    let second = runner
        .run_validation()
        .expect("second validation suite should run");
    let first_json = serialize_independent_campaign_suite_json(&first)
        .expect("validation suite should serialize");
    let second_json = serialize_independent_campaign_suite_json(&second)
        .expect("second validation suite should serialize");

    assert_eq!(first_json, second_json);
    assert!(!first.finalized);
    assert!(first.assessment_campaigns.is_none());
    assert!(first.assessment_comparison.is_none());
    assert!(first.promotion_gate.is_none());
    let resumed = runner
        .resume_validation(first.checkpoint.clone())
        .expect("suite checkpoint should resume");
    assert_eq!(
        first_json,
        serialize_independent_campaign_suite_json(&resumed)
            .expect("resumed suite should serialize")
    );
    assert_eq!(first.validation_campaigns.len(), 2);
    assert!(first.validation_campaigns.iter().all(|campaign| campaign
        .validation_comparison
        .rows
        .len()
        == 5));

    let mut finalized = first;
    runner
        .finalize_assessment(&mut finalized)
        .expect("assessment suite should finalize");
    assert!(finalized.finalized);
    assert_eq!(
        finalized.assessment_campaigns.as_ref().map(Vec::len),
        Some(2)
    );
    let gate = finalized
        .promotion_gate
        .as_ref()
        .expect("finalized suite should contain a promotion gate");
    assert_eq!(gate.candidate_policy, BaselinePolicyKind::BeamSearch);
    assert_eq!(gate.required_assessment_improvements, 2);
    assert_eq!(gate.observed_assessment_improvements, 0);
    assert!(!gate.promoted);

    let assessment_case_ids = finalized
        .assessment_campaigns
        .as_ref()
        .expect("assessment campaigns should exist")
        .iter()
        .flat_map(|campaign| {
            campaign
                .records
                .iter()
                .find(|record| record.kind == BaselinePolicyKind::StableDigest)
                .expect("stable baseline should exist")
                .assessment_run
                .as_ref()
                .expect("assessment run should exist")
                .case_observations
                .iter()
                .map(|case| case.case_id.clone())
                .collect::<Vec<_>>()
        })
        .collect::<BTreeSet<_>>();
    assert!(assessment_case_ids
        .iter()
        .all(|case_id| !first_json.contains(case_id)));

    let finalized_json = serialize_independent_campaign_suite_json(&finalized)
        .expect("finalized suite should serialize");
    let decoded = deserialize_independent_campaign_suite_json(&finalized_json, &config)
        .expect("finalized suite should deserialize");
    assert_eq!(
        finalized_json,
        serialize_independent_campaign_suite_json(&decoded).unwrap()
    );
    assert!(runner.finalize_assessment(&mut finalized).is_err());
}

#[test]
fn independent_suite_rejects_overlapping_domains_and_invalid_thresholds() {
    let overlap = IndependentCampaignSuiteConfig::new(
        "overlap",
        vec![campaign_config(0, 4, "a"), campaign_config(3, 7, "b")],
    );
    assert!(IndependentCampaignSuiteRunner::new(overlap).is_err());

    let invalid_threshold = suite_config().with_minimum_assessment_improvements(3);
    assert!(IndependentCampaignSuiteRunner::new(invalid_threshold).is_err());

    let single = IndependentCampaignSuiteConfig::new("single", vec![campaign_config(0, 4, "a")]);
    assert!(IndependentCampaignSuiteRunner::new(single).is_err());
}

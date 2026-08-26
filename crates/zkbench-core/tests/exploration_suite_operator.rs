//! Tests for state slice
//! `antithesis-inspired-deterministic-exploration-v1-independent-assessment-suite-operator`.

use std::collections::BTreeSet;
use std::fs;

use tempfile::tempdir;
use zkbench_core::{
    BaselineCampaignConfig, ExplorationRunConfig, FamilyKind, IndependentCampaignSuiteConfig,
    IndependentCampaignSuiteRunner, IndependentSuiteOperatorStore, MutationClass,
    SUITE_OPERATOR_FINALIZED_PATH, SUITE_OPERATOR_VALIDATION_PATH,
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
            .with_run_id(format!("suite_operator_{suffix}"))
            .with_budgets(2, 1, 4, 17),
    )
    .with_campaign_id(format!("suite_operator_campaign_{suffix}"))
}

fn suite_config() -> IndependentCampaignSuiteConfig {
    IndependentCampaignSuiteConfig::new(
        "suite_operator_test",
        vec![campaign_config(0, 4, "a"), campaign_config(4, 8, "b")],
    )
    .with_minimum_assessment_improvements(2)
}

#[test]
fn operator_persists_resume_and_one_way_finalization_without_pre_sealing_assessment() {
    let directory = tempdir().expect("temporary suite operator root should exist");
    let store = IndependentSuiteOperatorStore::new(directory.path())
        .expect("suite operator root should validate");
    let config = suite_config();

    let validation = store
        .run_validation(&config)
        .expect("suite validation should run");
    let validation_path = directory.path().join(SUITE_OPERATOR_VALIDATION_PATH);
    let validation_bytes = fs::read(&validation_path).expect("validation bytes should exist");
    assert!(!validation.finalized);
    assert!(!directory
        .path()
        .join(SUITE_OPERATOR_FINALIZED_PATH)
        .exists());
    assert!(store
        .read_report()
        .expect("validation report should exist")
        .promoted
        .is_none());
    let validation_report = store.read_report().expect("validation report should read");
    assert_eq!(validation_report.rows, validation_report.validation_rows);
    assert_eq!(validation_report.validation_rows.len(), 5);
    assert!(validation_report.assessment_rows.is_none());
    assert!(validation_report.policy_deltas.is_none());

    let resumed = store
        .resume_validation(&config)
        .expect("suite validation should resume");
    assert_eq!(validation, resumed);
    assert_eq!(validation_bytes, fs::read(&validation_path).unwrap());

    let validation_manifest = store
        .read_manifest()
        .expect("validation manifest should exist");
    assert!(!validation_manifest.finalized);
    assert!(validation_manifest
        .artifacts
        .iter()
        .all(|artifact| artifact.relative_path != SUITE_OPERATOR_FINALIZED_PATH));

    let validation_ids = resumed
        .validation_campaigns
        .iter()
        .flat_map(|campaign| {
            campaign
                .records
                .iter()
                .flat_map(|record| record.validation_run.case_observations.iter())
                .map(|case| case.case_id.clone())
        })
        .collect::<BTreeSet<_>>();
    let validation_text = String::from_utf8(validation_bytes).unwrap();
    assert!(validation_ids
        .iter()
        .all(|case_id| validation_text.contains(case_id)));

    let finalized = store
        .finalize_assessment(&config)
        .expect("suite assessment should finalize");
    assert!(finalized.finalized);
    assert!(finalized
        .assessment_campaigns
        .as_ref()
        .is_some_and(|campaigns| campaigns.len() == 2));
    let assessment_ids = finalized
        .assessment_campaigns
        .as_ref()
        .unwrap()
        .iter()
        .flat_map(|campaign| {
            campaign
                .records
                .iter()
                .flat_map(|record| {
                    record
                        .assessment_run
                        .as_ref()
                        .unwrap()
                        .case_observations
                        .iter()
                })
                .map(|case| case.case_id.clone())
        })
        .collect::<BTreeSet<_>>();
    assert!(assessment_ids
        .iter()
        .all(|case_id| !validation_text.contains(case_id)));
    let final_report = store.read_report().expect("final report should exist");
    assert!(final_report.finalized);
    assert_eq!(
        final_report.rows,
        final_report.assessment_rows.clone().unwrap()
    );
    assert_eq!(final_report.validation_rows.len(), 5);
    let deltas = final_report.policy_deltas.expect("final scorecard deltas");
    assert_eq!(deltas.len(), 5);
    assert!(deltas
        .iter()
        .all(|delta| delta.validation_metric_values.len() == 2
            && delta.assessment_metric_values.len() == 2
            && delta.assessment_minus_validation.len() == 2));
    assert!(
        store
            .read_manifest()
            .expect("final manifest should exist")
            .finalized
    );
    assert!(store.finalize_assessment(&config).is_err());
    assert!(store.run_validation(&config).is_err());
}

#[test]
fn operator_manifest_is_canonical_and_config_identity_is_fail_closed() {
    let directory = tempdir().expect("temporary suite operator root should exist");
    let store = IndependentSuiteOperatorStore::new(directory.path())
        .expect("suite operator root should validate");
    let config = suite_config();
    store
        .run_validation(&config)
        .expect("suite validation should run");
    let manifest = store.read_manifest().expect("manifest should be readable");
    let paths = manifest
        .artifacts
        .iter()
        .map(|artifact| artifact.relative_path.clone())
        .collect::<Vec<_>>();
    let mut sorted = paths.clone();
    sorted.sort();
    assert_eq!(paths, sorted);
    assert!(paths.contains(&"suite-config.json".to_string()));
    assert!(paths.contains(&"suite-report.json".to_string()));
    assert!(!paths.contains(&"suite-manifest.json".to_string()));

    let changed = IndependentCampaignSuiteConfig::new(
        "different_suite",
        vec![campaign_config(0, 4, "a"), campaign_config(4, 8, "b")],
    )
    .with_minimum_assessment_improvements(2);
    assert!(store.read_active_result(&changed).is_err());
    assert!(IndependentSuiteOperatorStore::new("/").is_err());
}

#[test]
fn operator_runner_and_store_share_the_same_deterministic_validation_result() {
    let directory = tempdir().expect("temporary suite operator root should exist");
    let store = IndependentSuiteOperatorStore::new(directory.path())
        .expect("suite operator root should validate");
    let config = suite_config();
    let direct = IndependentCampaignSuiteRunner::new(config.clone())
        .expect("suite config should validate")
        .run_validation()
        .expect("direct validation should run");
    let retained = store
        .run_validation(&config)
        .expect("stored validation should run");
    assert_eq!(direct, retained);
    assert_eq!(store.read_config().unwrap(), config);
}

#[test]
fn operator_readers_reject_tampered_report_and_manifest_bytes() {
    let directory = tempdir().expect("temporary suite operator root should exist");
    let store = IndependentSuiteOperatorStore::new(directory.path())
        .expect("suite operator root should validate");
    store
        .run_validation(&suite_config())
        .expect("suite validation should run");
    fs::write(
        directory.path().join("suite-report.json"),
        b"{\"schema_version\":\"tampered\"}",
    )
    .expect("tampered report should be writable in the test root");
    assert!(store.read_report().is_err());
    assert!(store.read_manifest().is_err());
}

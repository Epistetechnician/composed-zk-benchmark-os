use std::fs;

use tempfile::tempdir;
use zkbench_core::{
    build_smoke_soak_config, collect_baseline_failure_corpus,
    deserialize_baseline_campaign_result_json, serialize_baseline_campaign_result_json,
    BaselineCampaignConfig, ExplorationOperatorReport, ExplorationOperatorStore,
    ExplorationRunConfig, FamilyKind, MutationClass, OPERATOR_FINALIZED_PATH,
    OPERATOR_MANIFEST_PATH, OPERATOR_REPORT_JSON_PATH, OPERATOR_VALIDATION_PATH,
};

fn config() -> BaselineCampaignConfig {
    let base = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm, FamilyKind::BranchingFsm])
        .with_mutation_passes(vec![
            MutationClass::MissingConstraints,
            MutationClass::CorruptedGuards,
        ])
        .with_seed_range(0..4)
        .with_shard_count(2);
    BaselineCampaignConfig::new(
        ExplorationRunConfig::new(base)
            .with_run_id("exploration_operator_test")
            .with_budgets(2, 1, 4, 17),
    )
    .with_campaign_id("exploration_operator_test")
}

#[test]
fn operator_workflow_retains_deterministic_artifacts_and_seals_assessment() {
    let directory = tempdir().expect("temporary operator root");
    let store = ExplorationOperatorStore::new(directory.path()).expect("store validates");
    let campaign_config = config();

    let validation = store
        .run_validation(&campaign_config)
        .expect("validation should run");
    assert_eq!(
        store.read_config().expect("retained config should read"),
        campaign_config
    );
    let validation_bytes = fs::read(directory.path().join(OPERATOR_VALIDATION_PATH))
        .expect("validation artifact should exist");
    assert!(!validation.finalized);
    assert!(!directory.path().join(OPERATOR_FINALIZED_PATH).exists());
    assert!(directory.path().join(OPERATOR_REPORT_JSON_PATH).exists());
    assert!(directory.path().join(OPERATOR_MANIFEST_PATH).exists());

    let resumed = store
        .resume_validation(&campaign_config)
        .expect("resume should be exact");
    assert_eq!(
        validation_bytes,
        fs::read(directory.path().join(OPERATOR_VALIDATION_PATH))
            .expect("validation artifact should remain byte-identical")
    );
    assert_eq!(
        serialize_baseline_campaign_result_json(&validation).expect("serialize validation"),
        serialize_baseline_campaign_result_json(&resumed).expect("serialize resumed")
    );

    let report = ExplorationOperatorReport::from_result(&resumed).expect("report should validate");
    assert!(!report.finalized);
    assert!(!report.render_markdown().contains("FinalizedAssessment"));

    let corpus = store
        .failure_corpus(&campaign_config)
        .expect("validation corpus should be retained");
    assert_eq!(
        corpus,
        collect_baseline_failure_corpus(&resumed).expect("corpus should be deterministic")
    );

    let finalized = store
        .finalize_assessment(&campaign_config)
        .expect("assessment should finalize once");
    assert!(finalized.finalized);
    assert!(directory.path().join(OPERATOR_FINALIZED_PATH).exists());
    let finalized_report = ExplorationOperatorReport::from_result(&finalized)
        .expect("finalized report should validate");
    assert!(finalized_report.finalized);
    assert_eq!(
        finalized_report.phase,
        zkbench_core::ExplorationPhase::FinalizedAssessment
    );
    assert!(store.finalize_assessment(&campaign_config).is_err());

    let finalized_json = fs::read_to_string(directory.path().join(OPERATOR_FINALIZED_PATH))
        .expect("finalized artifact should be readable");
    let decoded = deserialize_baseline_campaign_result_json(&finalized_json, &campaign_config)
        .expect("finalized artifact should validate on readback");
    assert_eq!(decoded, finalized);
}

#[test]
fn operator_root_and_entry_paths_fail_closed() {
    assert!(ExplorationOperatorStore::new("../unsafe").is_err());
    let directory = tempdir().expect("temporary operator root");
    let store = ExplorationOperatorStore::new(directory.path()).expect("store validates");
    let campaign_config = config();
    store
        .run_validation(&campaign_config)
        .expect("validation should run");
    assert!(store
        .export_minimized_replay(&campaign_config, "../escape")
        .is_err());
}

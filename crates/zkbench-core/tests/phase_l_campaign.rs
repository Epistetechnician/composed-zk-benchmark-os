use std::fs;

use tempfile::tempdir;
use zkbench_core::{
    load_regression_corpus, quick_three_family_smoke, run_soak_campaign, soak_config_from_plan,
    ClaimBoundary, RegressionFailureKind, ReportBundleReviewPlan, ReportBundleSampleStrategy,
    SoakCampaignConfig,
};

#[test]
fn quick_campaign_writes_sampled_reports_and_updates_regression_corpus() {
    let artifacts = tempdir().expect("artifacts tempdir should be available");
    let config = SoakCampaignConfig {
        campaign_id: "test_quick_smoke".to_string(),
        soak_config: soak_config_from_plan(quick_three_family_smoke()),
        review_plan: ReportBundleReviewPlan {
            sample_strategy: ReportBundleSampleStrategy::All,
            require_score_report: true,
            require_readme_warnings: true,
            claim_boundary_cap: ClaimBoundary::Level1LocalReplay,
        },
        artifacts_root: artifacts.path().to_string_lossy().to_string(),
    };

    let report = run_soak_campaign(&config).expect("campaign should run");
    let campaign_dir = artifacts.path().join("campaigns").join("test_quick_smoke");

    assert_eq!(report.soak_report.total_failures, 0);
    assert!(report.review_report.valid);
    assert_eq!(
        report.sampled_report_count,
        report.soak_report.total_packs_written
    );
    assert_eq!(report.failure_pack_count, 0);
    assert!(campaign_dir.join("campaign_report.json").is_file());
    assert!(campaign_dir.join("report_bundle_review.json").is_file());
    assert!(campaign_dir.join("soak_execution_report.json").is_file());

    let sampled = fs::read_dir(campaign_dir.join("sampled_reports"))
        .expect("sampled reports dir should exist")
        .count();
    assert_eq!(sampled, report.sampled_report_count);

    let corpus = load_regression_corpus(artifacts.path().join("regression_corpus/corpus.json"))
        .expect("corpus should load");
    assert!(
        corpus
            .entries
            .iter()
            .any(|entry| entry.failure_kind == RegressionFailureKind::MutationPassSkipped),
        "branching FSM cells should record skipped BadCounters passes"
    );
}

#[test]
fn campaign_artifacts_remain_level0_metadata() {
    let artifacts = tempdir().expect("artifacts tempdir should be available");
    let config = SoakCampaignConfig {
        campaign_id: "test_level0".to_string(),
        soak_config: soak_config_from_plan(quick_three_family_smoke()),
        review_plan: ReportBundleReviewPlan::default(),
        artifacts_root: artifacts.path().to_string_lossy().to_string(),
    };
    let report = run_soak_campaign(&config).expect("campaign should run");
    assert_eq!(report.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(
        report.review_report.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
}

use tempfile::tempdir;
use zkbench_core::{
    review_soak_report_bundles, run_local_soak, ClaimBoundary, ReportBundleReviewPlan,
    ReportBundleSampleStrategy, SoakConfig,
};

#[test]
fn phase_l_soak_packs_remain_level1_local_replay() {
    let soak_dir = tempdir().expect("soak tempdir should be available");
    let soak_report =
        run_local_soak(&SoakConfig::default(), soak_dir.path()).expect("soak should run");

    assert_eq!(
        soak_report.config.plan.claim_boundary_cap,
        ClaimBoundary::Level1LocalReplay
    );
    assert!(soak_report
        .notes
        .iter()
        .any(|note| note.contains("not official benchmark evidence")));

    let review_report = review_soak_report_bundles(
        soak_dir.path(),
        &soak_report,
        &ReportBundleReviewPlan {
            sample_strategy: ReportBundleSampleStrategy::All,
            ..ReportBundleReviewPlan::default()
        },
    )
    .expect("review should run");

    assert_eq!(
        review_report.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(review_report.valid);
    assert!(review_report
        .notes
        .iter()
        .any(|note| note.contains("Level1LocalReplay")));
}

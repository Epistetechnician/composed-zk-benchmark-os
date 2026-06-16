//! Export deterministic Phase L soak artifacts to a caller-provided directory.
//!
//! Usage:
//!   cargo run -p zkbench-core --example phase_l_soak -- <output_root>

use std::env;
use std::fs;
use std::path::PathBuf;

use zkbench_core::{
    review_soak_report_bundles, run_local_soak, serialize_report_bundle_review_report_json,
    ClaimBoundary, ReportBundleReviewPlan, ReportBundleSampleStrategy, SoakConfig,
};

fn main() {
    let output_root = env::args()
        .nth(1)
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from(".context/autoresearch/soak_runs/latest"));

    if output_root.exists() {
        fs::remove_dir_all(&output_root).expect("output root should be removable when re-running");
    }

    let config = SoakConfig::default();
    let soak_report = run_local_soak(&config, &output_root).expect("local soak should run");

    let review_plan = ReportBundleReviewPlan {
        sample_strategy: ReportBundleSampleStrategy::All,
        require_score_report: true,
        require_readme_warnings: true,
        claim_boundary_cap: ClaimBoundary::Level1LocalReplay,
    };
    let review_report = review_soak_report_bundles(&output_root, &soak_report, &review_plan)
        .expect("review should run");

    let review_json = serialize_report_bundle_review_report_json(&review_report)
        .expect("review report should serialize");
    fs::write(output_root.join("report_bundle_review.json"), review_json)
        .expect("review report should write");

    println!(
        "phase_l_soak: packs_written={}",
        soak_report.total_packs_written
    );
    println!("phase_l_soak: review_valid={}", review_report.valid);
    println!("phase_l_soak: output_root={}", output_root.display());
}

//! Run a quick Phase L soak campaign and curate regression corpus artifacts.
//!
//! Usage:
//!   cargo run -p zkbench-core --example phase_l_campaign
//!   cargo run -p zkbench-core --example phase_l_campaign -- quick_smoke
//!   cargo run -p zkbench-core --example phase_l_campaign -- quick_full [campaign_id]

use std::env;

use zkbench_core::{
    quick_campaign_config, quick_three_family_smoke, run_soak_campaign,
    serialize_soak_campaign_report_json, soak_config_from_plan, ClaimBoundary,
    ReportBundleReviewPlan, ReportBundleSampleStrategy, SoakCampaignConfig,
};

fn main() {
    let mode = env::args()
        .nth(1)
        .unwrap_or_else(|| "quick_full".to_string());
    let campaign_id = env::args()
        .nth(2)
        .unwrap_or_else(|| default_campaign_id(&mode));
    let artifacts_root = env::var("PHASE_L_ARTIFACTS_ROOT")
        .unwrap_or_else(|_| ".context/phase-l-artifacts".to_string());

    let soak_config = match mode.as_str() {
        "quick_smoke" => soak_config_from_plan(quick_three_family_smoke()),
        _ => quick_campaign_config(),
    };

    let config = SoakCampaignConfig {
        campaign_id,
        soak_config,
        review_plan: ReportBundleReviewPlan {
            sample_strategy: ReportBundleSampleStrategy::All,
            require_score_report: true,
            require_readme_warnings: true,
            claim_boundary_cap: ClaimBoundary::Level1LocalReplay,
        },
        artifacts_root,
    };

    let report = run_soak_campaign(&config).expect("soak campaign should run");
    let json =
        serialize_soak_campaign_report_json(&report).expect("campaign report should serialize");

    println!("phase_l_campaign: id={}", report.campaign_id);
    println!(
        "phase_l_campaign: packs_written={}",
        report.soak_report.total_packs_written
    );
    println!(
        "phase_l_campaign: review_valid={}",
        report.review_report.valid
    );
    println!(
        "phase_l_campaign: sampled_reports={}",
        report.sampled_report_count
    );
    println!(
        "phase_l_campaign: failure_packs={}",
        report.failure_pack_count
    );
    println!(
        "phase_l_campaign: corpus_entries_added={}",
        report.corpus_entries_added
    );
    println!(
        "phase_l_campaign: artifacts={}/{}",
        config.artifacts_root, report.campaign_relative_path
    );
    println!("{json}");
}

fn default_campaign_id(mode: &str) -> String {
    // Deterministic-ish id without wall-clock timestamps in the default path.
    format!("{mode}_v0")
}

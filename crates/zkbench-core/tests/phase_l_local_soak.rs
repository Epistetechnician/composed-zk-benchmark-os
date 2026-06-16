use std::fs;
use std::path::Path;

use tempfile::tempdir;
use zkbench_core::{
    deserialize_report_bundle_review_report_json, deserialize_soak_execution_report_json,
    review_soak_report_bundles, run_local_soak, serialize_report_bundle_review_report_json,
    serialize_soak_execution_report_json, BenchmarkPackReader, ClaimBoundary,
    ReportBundleReviewPlan, ReportBundleSampleStrategy, SoakConfig, SoakPlan,
};

#[test]
fn local_soak_writes_deterministic_packs_for_all_families_and_seeds() {
    let config = SoakConfig {
        plan: SoakPlan {
            family_kinds: vec![
                zkbench_core::FamilyKind::BaselineFsm,
                zkbench_core::FamilyKind::BranchingFsm,
                zkbench_core::FamilyKind::BoundedCounterLoop,
            ],
            seeds: vec![11, 17],
            apply_mutations: true,
            claim_boundary_cap: ClaimBoundary::Level1LocalReplay,
        },
        packs_subdirectory: "packs".to_string(),
        include_score_report: true,
    };

    let left = tempdir().expect("left soak tempdir should be available");
    let right = tempdir().expect("right soak tempdir should be available");

    let left_report = run_local_soak(&config, left.path()).expect("left soak should run");
    let right_report = run_local_soak(&config, right.path()).expect("right soak should run");

    assert_eq!(left_report, right_report);
    assert_eq!(left_report.total_failures, 0);
    assert_eq!(left_report.total_packs_written, 6);
    assert_eq!(left_report.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert!(left_report
        .pack_descriptors
        .iter()
        .all(|descriptor| descriptor.replay_result_count >= 1));
    assert!(left_report
        .pack_descriptors
        .iter()
        .any(|descriptor| descriptor.mutation_passes_skipped > 0));

    let left_json = serialize_soak_execution_report_json(&left_report)
        .expect("left soak report should serialize");
    let right_json = serialize_soak_execution_report_json(&right_report)
        .expect("right soak report should serialize");
    assert_eq!(left_json, right_json);

    let round_trip =
        deserialize_soak_execution_report_json(&left_json).expect("soak report should deserialize");
    assert_eq!(round_trip, left_report);

    for descriptor in &left_report.pack_descriptors {
        let left_pack = left.path().join(&descriptor.pack_root_relative);
        let right_pack = right.path().join(&descriptor.pack_root_relative);
        let left_pack_json =
            fs::read(left_pack.join("pack.json")).expect("left pack.json should be readable");
        let right_pack_json =
            fs::read(right_pack.join("pack.json")).expect("right pack.json should be readable");
        assert_eq!(
            left_pack_json, right_pack_json,
            "pack.json should be byte-identical for {}",
            descriptor.pack_id
        );

        let reader = BenchmarkPackReader::read(&left_pack).expect("pack reader should load pack");
        assert_eq!(
            reader.manifest().claim_boundary,
            ClaimBoundary::Level1LocalReplay
        );
        assert!(reader.validate().valid);
    }

    let soak_report_bytes = fs::read(left.path().join("soak_execution_report.json"))
        .expect("soak execution report should be written");
    let soak_report_bytes_again = fs::read(right.path().join("soak_execution_report.json"))
        .expect("right soak execution report should be written");
    assert_eq!(soak_report_bytes, soak_report_bytes_again);
}

#[test]
fn sampled_report_bundle_review_passes_for_soak_packs() {
    let config = SoakConfig::default();
    let soak_dir = tempdir().expect("soak tempdir should be available");
    let soak_report = run_local_soak(&config, soak_dir.path()).expect("soak should run");

    let review_plan = ReportBundleReviewPlan {
        sample_strategy: ReportBundleSampleStrategy::EveryNth { stride: 2 },
        require_score_report: true,
        require_readme_warnings: true,
        claim_boundary_cap: ClaimBoundary::Level1LocalReplay,
    };
    let review_report = review_soak_report_bundles(soak_dir.path(), &soak_report, &review_plan)
        .expect("sampled review should run");

    assert_eq!(
        review_report.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(review_report.valid);
    assert_eq!(review_report.packs_failed, 0);
    assert!(review_report.packs_sampled > 0);
    assert!(review_report
        .findings
        .iter()
        .all(|finding| finding.severity != zkbench_core::ReportBundleReviewFindingSeverity::Error));

    let review_json = serialize_report_bundle_review_report_json(&review_report)
        .expect("review report should serialize");
    let round_trip = deserialize_report_bundle_review_report_json(&review_json)
        .expect("review report should deserialize");
    assert_eq!(round_trip, review_report);
}

#[test]
fn phase_l_source_contains_no_process_command_api() {
    let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let soak_source = read_source_tree(&manifest_dir.join("src/soak"));
    let review_source = read_source_tree(&manifest_dir.join("src/pack/report_bundle_review.rs"));

    assert!(!soak_source.contains("std::process::Command"));
    assert!(!soak_source.contains("Command::new"));
    assert!(!review_source.contains("std::process::Command"));
    assert!(!review_source.contains("Command::new"));
}

fn read_source_tree(path: &Path) -> String {
    if path.is_file() {
        return fs::read_to_string(path).unwrap_or_default();
    }
    let mut output = String::new();
    if let Ok(entries) = fs::read_dir(path) {
        let mut paths = entries
            .filter_map(Result::ok)
            .map(|entry| entry.path())
            .collect::<Vec<_>>();
        paths.sort();
        for entry in paths {
            output.push_str(&read_source_tree(&entry));
            output.push('\n');
        }
    }
    output
}

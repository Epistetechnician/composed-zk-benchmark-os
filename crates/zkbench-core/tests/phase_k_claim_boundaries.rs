use std::fs;
use std::path::Path;

use zkbench_core::{
    build_local_replay_manifest_for_instance, build_smoke_soak_config, generate_instance,
    plan_soak_shards, score_report_from_local_mutation_evidence, ClaimBoundary, FamilyKind,
    GeneratorConfig, InstanceParams, LocalMutationEvidenceSummary, LocalSoakRunner,
    MockTelemetryClock, MutationClass, SoakShardId,
};

#[test]
fn phase_k_reports_do_not_create_level2_actual_evidence() {
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1);
    let plan = plan_soak_shards(config).expect("plan should build");
    let mut runner = LocalSoakRunner::new(plan).with_clock(MockTelemetryClock::default());
    let result = runner
        .run_shard(SoakShardId::from_index(0))
        .expect("run should complete");

    assert_eq!(result.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(
        result.health_report.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert_eq!(
        result.failure_corpus_index.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert_eq!(
        result.telemetry_report.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(result.failure_corpus_index.entries.iter().all(|entry| {
        entry.claim_boundary < ClaimBoundary::Level2ReproducibleBenchmarkArtifact
    }));
}

#[test]
fn local_replay_artifacts_remain_level1_at_most() {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(3),
        InstanceParams::default(),
    )
    .expect("instance should generate");
    let manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    assert!(manifest.claim_boundary <= ClaimBoundary::Level1LocalReplay);
}

#[test]
fn internal_timing_telemetry_is_not_scoring_performance() {
    let score = score_report_from_local_mutation_evidence(LocalMutationEvidenceSummary {
        local_accepted_traces: 1,
        local_rejected_traces: 1,
        mutation_variants_generated: 1,
        outcome_changes_observed: 1,
        unsound_acceptance_candidates: 0,
    });
    assert!(score.performance.is_none());
    assert!(score.formal_evidence.is_none());
}

#[test]
fn source_contains_no_process_execution_api_in_phase_k_slice() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("src");
    let mut hits = Vec::new();
    scan_files(&root, &mut |path, text| {
        if text.contains("std::process::Command") || text.contains("Command::new") {
            hits.push(path.display().to_string());
        }
    });
    assert!(hits.is_empty(), "process execution API hits: {hits:?}");
}

#[test]
fn phase_k_fixture_scan_has_no_backend_performance_or_official_claims() {
    let fixtures = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures");
    let mut hits = Vec::new();
    scan_files(&fixtures, &mut |path, text| {
        let is_negative_fixture = path
            .file_name()
            .and_then(|name| name.to_str())
            .map(|name| name.contains("official_claim"))
            .unwrap_or(false);
        if is_negative_fixture {
            return;
        }
        for forbidden in [
            "prover_time",
            "verifier_time",
            "proof_size",
            "zk_harness_time",
            "constraint_count",
            "SOTA result",
        ] {
            if text.contains(forbidden) {
                hits.push(format!("{}:{forbidden}", path.display()));
            }
        }
    });
    assert!(hits.is_empty(), "forbidden fixture text: {hits:?}");
}

fn scan_files(root: &Path, visit: &mut impl FnMut(&Path, &str)) {
    let entries = fs::read_dir(root).expect("directory should be readable");
    for entry in entries {
        let entry = entry.expect("directory entry should be readable");
        let path = entry.path();
        if path.is_dir() {
            scan_files(&path, visit);
        } else {
            let text = fs::read_to_string(&path).unwrap_or_default();
            visit(&path, &text);
        }
    }
}

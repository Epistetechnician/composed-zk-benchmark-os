//! Tests for state slice `antithesis-inspired-deterministic-exploration-v1`.

use std::collections::BTreeSet;
use std::fs;

use tempfile::tempdir;

use zkbench_core::{
    build_smoke_soak_config, build_soak_report_bundle_with_exploration,
    deserialize_exploration_artifact_json, deserialize_soak_report_bundle_json, plan_soak_shards,
    read_soak_report_bundle, reduce_failure_sequence, reduce_local_replay_failure,
    serialize_exploration_artifact_json, serialize_soak_report_bundle_json,
    write_soak_report_bundle, ClaimBoundary, DeterministicExplorer, ExplorationArtifact,
    ExplorationRunConfig, ExplorerPolicy, FailureReductionInput, FamilyKind, GuidanceVector,
    LocalSoakRunner, MinimizationStep, MockTelemetryClock, MutationClass, QueuePolicy,
    SoakArtifactRole, SoakRunRequest,
};

fn test_config() -> ExplorationRunConfig {
    let base = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm, FamilyKind::BranchingFsm])
        .with_mutation_passes(vec![
            MutationClass::MissingConstraints,
            MutationClass::CorruptedGuards,
        ])
        .with_seed_range(0..4)
        .with_shard_count(2);
    ExplorationRunConfig::new(base)
        .with_run_id("exploration_test")
        .with_budgets(2, 1, 4, 17)
}

fn valid_bundle(exploration: Option<ExplorationArtifact>) -> zkbench_core::SoakReportBundle {
    let plan = plan_soak_shards(test_config().base_soak_config.clone()).expect("plan should build");
    let mut telemetry_reports = Vec::new();
    let mut health_reports = Vec::new();
    let mut failure_corpus_indexes = Vec::new();
    for manifest in &plan.shard_manifests {
        let mut runner =
            LocalSoakRunner::new(plan.clone()).with_clock(MockTelemetryClock::default());
        let result = runner
            .run_request(SoakRunRequest {
                shard_id: manifest.shard_id.clone(),
                resume: false,
            })
            .expect("shard should run");
        telemetry_reports.push(result.telemetry_report);
        health_reports.push(result.health_report);
        failure_corpus_indexes.push(result.failure_corpus_index);
    }
    build_soak_report_bundle_with_exploration(
        "exploration_filesystem_bundle",
        plan,
        telemetry_reports,
        health_reports,
        failure_corpus_indexes,
        exploration,
    )
    .expect("bundle should build")
}

#[test]
fn identical_validation_runs_have_identical_artifacts() {
    let explorer = DeterministicExplorer::new(test_config()).expect("config should validate");
    let first = explorer
        .run_validation()
        .expect("first run should complete");
    let second = explorer
        .run_validation()
        .expect("second run should complete");
    let first_json = serde_json::to_vec(&ExplorationArtifact::from_result(first))
        .expect("first artifact should serialize");
    let second_json = serde_json::to_vec(&ExplorationArtifact::from_result(second))
        .expect("second artifact should serialize");
    assert_eq!(first_json, second_json);
}

#[test]
fn checkpoint_resume_matches_uninterrupted_validation() {
    let explorer = DeterministicExplorer::new(test_config()).expect("config should validate");
    let uninterrupted = explorer.run_validation().expect("full run should complete");
    let prefix = explorer
        .run_validation_with_iteration_limit(1)
        .expect("prefix should complete");
    let resumed = explorer
        .resume_validation(prefix.checkpoint)
        .expect("resume should complete");
    assert_eq!(
        serde_json::to_vec(&uninterrupted).expect("uninterrupted serialization"),
        serde_json::to_vec(&resumed).expect("resumed serialization")
    );
}

#[test]
fn assessment_is_sealed_until_explicit_finalization_and_disjoint() {
    let explorer = DeterministicExplorer::new(test_config()).expect("config should validate");
    let mut result = explorer
        .run_validation()
        .expect("validation should complete");
    assert!(result.assessment_evaluation.is_none());
    assert!(result.assessment_report.is_none());
    assert!(result.checkpoint.assessment_report.is_none());
    assert!(!result.finalized);
    let validation_ids = result
        .validation_frontier
        .records
        .first()
        .expect("frontier should contain baseline")
        .evaluation
        .observation
        .case_ids
        .iter()
        .cloned()
        .collect::<BTreeSet<_>>();

    explorer
        .finalize_assessment(&mut result)
        .expect("assessment should finalize once");
    let assessment_ids = result
        .assessment_evaluation
        .as_ref()
        .expect("assessment should exist after finalization")
        .observation
        .case_ids
        .iter()
        .cloned()
        .collect::<BTreeSet<_>>();
    assert!(!validation_ids.is_empty());
    assert!(!assessment_ids.is_empty());
    assert!(validation_ids.is_disjoint(&assessment_ids));
    assert!(result.finalized);
    let report = result
        .assessment_report
        .as_ref()
        .expect("assessment report should exist after finalization");
    assert_eq!(
        report.candidate_id,
        result
            .assessment_evaluation
            .as_ref()
            .expect("assessment should exist")
            .candidate_id
    );
    assert_eq!(
        report.validation_guidance,
        result
            .validation_frontier
            .records
            .first()
            .expect("frontier should contain selected candidate")
            .evaluation
            .guidance
    );
    assert!(!report.validation_observation_digest.is_empty());
    assert!(!report.assessment_observation_digest.is_empty());
    assert!(explorer.finalize_assessment(&mut result).is_err());
}

#[test]
fn tampered_assessment_report_is_rejected() {
    let explorer = DeterministicExplorer::new(test_config()).expect("config should validate");
    let mut result = explorer
        .run_validation()
        .expect("validation should complete");
    explorer
        .finalize_assessment(&mut result)
        .expect("assessment should finalize once");

    let mut artifact = ExplorationArtifact::from_result(result);
    artifact.result.assessment_report = None;
    assert!(serialize_exploration_artifact_json(&artifact).is_err());
}

#[test]
fn policy_validation_rejects_duplicates_and_out_of_scope_classes() {
    let config = test_config();
    let mut policy = ExplorerPolicy::from_config(&config.base_soak_config);
    policy.family_order.push(FamilyKind::BaselineFsm);
    assert!(policy.validate(&config.base_soak_config).is_err());

    let mut out_of_scope = ExplorerPolicy::from_config(&config.base_soak_config);
    out_of_scope.mutation_schedule.mutation_classes = vec![MutationClass::BadCounters];
    assert!(out_of_scope.validate(&config.base_soak_config).is_err());
}

#[test]
fn guidance_vector_uses_required_lexicographic_order() {
    let valid_low_coverage = GuidanceVector {
        valid: true,
        coverage: 1,
        novelty: 10,
        failures: 10,
        cost: 1,
    };
    let invalid_high_coverage = GuidanceVector {
        valid: false,
        coverage: 100,
        novelty: 100,
        failures: 100,
        cost: 0,
    };
    assert!(valid_low_coverage > invalid_high_coverage);

    let high_coverage = GuidanceVector {
        valid: true,
        coverage: 3,
        novelty: 0,
        failures: 0,
        cost: 100,
    };
    let low_cost = GuidanceVector {
        valid: true,
        coverage: 3,
        novelty: 0,
        failures: 0,
        cost: 1,
    };
    assert!(low_cost > high_coverage);
}

#[test]
fn reducer_preserves_manifest_and_failure_classification() {
    let input = FailureReductionInput {
        replay_manifest_id: "manifest_case_a".to_string(),
        failure_classification: "oracle-mismatch".to_string(),
        steps: vec![
            "family".to_string(),
            "mutation".to_string(),
            "trace".to_string(),
        ],
        claim_boundary: zkbench_core::ClaimBoundary::Level0DesignNote,
    };
    let reduced = reduce_failure_sequence(&input, |steps, classification| {
        classification == "oracle-mismatch" && !steps.is_empty()
    })
    .expect("reducer should complete");
    assert_eq!(reduced.replay_manifest_id, input.replay_manifest_id);
    assert_eq!(reduced.failure_classification, input.failure_classification);
    assert_eq!(reduced.retained_steps, vec!["trace"]);
}

#[test]
fn reducer_replays_real_manifest_and_preserves_local_classification() {
    let plan = plan_soak_shards(test_config().base_soak_config).expect("plan should build");
    let mut runner = LocalSoakRunner::new(plan.clone()).with_clock(MockTelemetryClock::default());
    let run = runner
        .run_request(SoakRunRequest {
            shard_id: plan.shard_manifests[0].shard_id.clone(),
            resume: false,
        })
        .expect("shard should run");
    let replay = run
        .replay_observations
        .first()
        .expect("runner should retain a replay observation");
    let classification = replay
        .result
        .trace_results
        .first()
        .expect("replay should retain a trace result")
        .result_classification;

    let reduced = reduce_local_replay_failure(&replay.manifest, &replay.result, classification)
        .expect("real replay should reduce");
    assert_eq!(reduced.replay_manifest_id, replay.manifest.id);
    assert_eq!(
        reduced.failure_classification,
        format!("{classification:?}")
    );
    assert!(!reduced.retained_steps.is_empty());
    assert!(reduced.attempted_removals >= reduced.retained_steps.len());
}

#[test]
fn exploration_sidecar_round_trips_through_validated_json() {
    let explorer = DeterministicExplorer::new(test_config()).expect("config should validate");
    let artifact = ExplorationArtifact::from_result(
        explorer
            .run_validation()
            .expect("validation should complete"),
    );
    let json = serialize_exploration_artifact_json(&artifact).expect("artifact should serialize");
    let restored = deserialize_exploration_artifact_json(&json).expect("artifact should restore");
    assert_eq!(artifact, restored);
}

#[test]
fn policy_surface_contains_deterministic_queue_and_reducer_controls() {
    let config = test_config();
    let mut policy = ExplorerPolicy::from_config(&config.base_soak_config);
    policy.queue_policy = QueuePolicy::RoundRobinMutations;
    policy.minimization_order.reverse();
    assert_eq!(policy.minimization_order.len(), 4);
    assert!(policy
        .minimization_order
        .contains(&MinimizationStep::IsolateTrace));
    assert!(policy.validate(&config.base_soak_config).is_ok());
}

#[test]
fn queue_and_mutation_schedules_change_operational_plan_order() {
    let explorer = DeterministicExplorer::new(test_config()).expect("config should validate");
    let stable_policy = ExplorerPolicy::from_config(&test_config().base_soak_config);
    let stable = explorer
        .plan_validation_shards(&stable_policy)
        .expect("stable plan should build");

    let mut family_policy = stable_policy.clone();
    family_policy.queue_policy = QueuePolicy::RoundRobinFamilies;
    family_policy.family_order.reverse();
    let family_plan = explorer
        .plan_validation_shards(&family_policy)
        .expect("family plan should build");
    assert_ne!(
        stable.shard_manifests, family_plan.shard_manifests,
        "family queue policy must affect assigned execution order"
    );
    assert_eq!(
        stable
            .case_plans
            .iter()
            .map(|case| case.id.clone())
            .collect::<BTreeSet<_>>(),
        family_plan
            .case_plans
            .iter()
            .map(|case| case.id.clone())
            .collect::<BTreeSet<_>>()
    );

    let mut mutation_policy = stable_policy;
    mutation_policy.queue_policy = QueuePolicy::RoundRobinMutations;
    mutation_policy.mutation_schedule.mutation_classes.reverse();
    let mutation_plan = explorer
        .plan_validation_shards(&mutation_policy)
        .expect("mutation plan should build");
    assert_eq!(
        mutation_plan.case_plans[0].mutation_classes,
        mutation_policy.mutation_schedule.mutation_classes
    );
}

#[test]
fn bounded_case_budget_changes_reached_cases_without_changing_allocation() {
    let config = test_config().with_case_budget(2);
    let explorer = DeterministicExplorer::new(config.clone()).expect("config should validate");
    let stable_policy = ExplorerPolicy::from_config(&config.base_soak_config);
    let stable = explorer
        .plan_validation_shards(&stable_policy)
        .expect("stable bounded plan should build");

    let mut family_policy = stable_policy.clone();
    family_policy.queue_policy = QueuePolicy::RoundRobinFamilies;
    family_policy.family_order.reverse();
    let family_plan = explorer
        .plan_validation_shards(&family_policy)
        .expect("family bounded plan should build");

    assert_eq!(stable.case_plans.len(), 2);
    assert_eq!(family_plan.case_plans.len(), 2);
    assert_eq!(
        stable.shard_manifests.len(),
        family_plan.shard_manifests.len()
    );
    assert_eq!(
        stable
            .case_plans
            .iter()
            .map(|case| case.mutation_classes.len())
            .sum::<usize>(),
        family_plan
            .case_plans
            .iter()
            .map(|case| case.mutation_classes.len())
            .sum::<usize>()
    );
    assert_ne!(
        stable
            .case_plans
            .iter()
            .map(|case| case.id.clone())
            .collect::<Vec<_>>(),
        family_plan
            .case_plans
            .iter()
            .map(|case| case.id.clone())
            .collect::<Vec<_>>(),
        "policy ordering must affect the bounded reached-case set"
    );
}

#[test]
fn case_budget_must_fit_both_sealed_phase_domains() {
    let config = test_config().with_case_budget(5);
    assert!(DeterministicExplorer::new(config).is_err());
}

#[test]
fn guidance_retains_exact_local_replay_oracle_observations() {
    let explorer = DeterministicExplorer::new(test_config()).expect("config should validate");
    let result = explorer
        .run_validation_with_iteration_limit(1)
        .expect("validation should complete");
    let observation = &result.validation_frontier.records[0].evaluation.observation;

    assert!(!observation.replay_trace_observations.is_empty());
    assert!(observation
        .replay_trace_observations
        .iter()
        .all(|trace| trace.claim_boundary == ClaimBoundary::Level1LocalReplay));
    assert!(observation
        .replay_trace_observations
        .iter()
        .all(|trace| !trace.replay_manifest_id.is_empty() && !trace.replay_result_id.is_empty()));
    assert!(observation
        .replay_signatures
        .iter()
        .any(|signature| signature.contains("oracle=")));
}

#[test]
fn exploration_sidecar_is_optional_in_existing_soak_bundle_serialization() {
    let config = test_config();
    let plan = plan_soak_shards(config.base_soak_config.clone()).expect("plan should build");
    let explorer = DeterministicExplorer::new(config).expect("config should validate");
    let artifact = ExplorationArtifact::from_result(
        explorer
            .run_validation()
            .expect("validation should complete"),
    );
    let bundle = build_soak_report_bundle_with_exploration(
        "bundle_with_exploration",
        plan,
        Vec::new(),
        Vec::new(),
        Vec::new(),
        Some(artifact),
    )
    .expect("bundle should build");
    assert!(bundle.exploration.is_some());
    let json = serialize_soak_report_bundle_json(&bundle).expect("bundle should serialize");
    let restored = deserialize_soak_report_bundle_json(&json).expect("bundle should restore");
    assert!(restored.exploration.is_some());
}

#[test]
fn exploration_sidecar_round_trips_on_disk_and_rejects_missing_or_tampered_records() {
    let explorer = DeterministicExplorer::new(test_config()).expect("config should validate");
    let artifact = ExplorationArtifact::from_result(
        explorer
            .run_validation()
            .expect("validation should complete"),
    );
    let bundle = valid_bundle(Some(artifact.clone()));
    let dir = tempdir().expect("tempdir should be available");
    let root = dir.path().join("bundle");

    write_soak_report_bundle(&root, &bundle).expect("bundle should write");
    let sidecar_path = root.join("aggregate/exploration.json");
    assert!(sidecar_path.is_file());
    assert_eq!(
        read_soak_report_bundle(&root).expect("bundle should read"),
        bundle
    );

    fs::remove_file(&sidecar_path).expect("sidecar should remove");
    let missing = read_soak_report_bundle(&root).expect_err("missing sidecar should reject");
    assert!(missing.to_string().contains("exploration.json"));

    fs::write(
        &sidecar_path,
        serde_json::to_vec_pretty(&artifact).expect("tampered sidecar should serialize"),
    )
    .expect("sidecar should restore");
    let mut tampered = artifact;
    tampered.notes.push("tampered".to_string());
    fs::write(
        &sidecar_path,
        serde_json::to_vec_pretty(&tampered).expect("tampered sidecar should serialize"),
    )
    .expect("tampered sidecar should write");
    let digest_error = read_soak_report_bundle(&root).expect_err("tampered sidecar should reject");
    assert!(digest_error.to_string().contains("sidecar"));
}

#[test]
fn legacy_bundle_without_exploration_writes_without_a_sidecar() {
    let explorer = DeterministicExplorer::new(test_config()).expect("config should validate");
    let artifact = ExplorationArtifact::from_result(
        explorer
            .run_validation()
            .expect("validation should complete"),
    );
    let mut bundle = valid_bundle(Some(artifact));
    bundle.exploration = None;
    bundle
        .artifact_digest_set
        .artifacts
        .retain(|artifact| artifact.role != SoakArtifactRole::Exploration);

    let dir = tempdir().expect("tempdir should be available");
    let root = dir.path().join("legacy-bundle");
    write_soak_report_bundle(&root, &bundle).expect("legacy bundle should write");
    assert!(!root.join("aggregate/exploration.json").exists());
    assert_eq!(
        read_soak_report_bundle(&root).expect("legacy bundle should read"),
        bundle
    );
}

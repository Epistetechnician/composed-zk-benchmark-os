use std::fmt::Debug;

use tempfile::tempdir;
use zkbench_core::{
    build_failure_corpus_entry, build_smoke_soak_config, deserialize_failure_corpus_index_json,
    deserialize_failure_reproduction_manifest_json, deserialize_soak_artifact_manifest_json,
    deserialize_soak_health_report_json, deserialize_soak_report_bundle_json,
    deserialize_soak_run_config_json, deserialize_soak_shard_checkpoint_json,
    deserialize_soak_shard_manifest_json, deserialize_soak_shard_plan_json,
    deserialize_soak_telemetry_report_json, plan_soak_shards, run_soak_campaign,
    serialize_failure_corpus_index_json, serialize_failure_reproduction_manifest_json,
    serialize_soak_artifact_manifest_json, serialize_soak_health_report_json,
    serialize_soak_report_bundle_json, serialize_soak_run_config_json,
    serialize_soak_shard_checkpoint_json, serialize_soak_shard_manifest_json,
    serialize_soak_shard_plan_json, serialize_soak_telemetry_report_json, ClaimBoundary,
    FailureCorpusEntryInput, FailureCorpusKind, FamilyKind, GeneratorTunables,
    LocalSoakRunnerConfig, MutationClass, Result, SoakCampaignApproval,
    SoakCampaignArtifactRootPolicy, SoakCampaignConfig, SoakOutputPolicy, SoakShardId,
};

fn approved_config(campaign_id: &str, artifact_root: std::path::PathBuf) -> SoakCampaignConfig {
    SoakCampaignConfig {
        campaign_id: campaign_id.to_string(),
        approval: SoakCampaignApproval {
            approved_by: "local_user".to_string(),
            approval_statement: "approved local serialization coverage campaign".to_string(),
            approved_at_ms: 0,
        },
        artifact_root_policy: SoakCampaignArtifactRootPolicy {
            artifact_root,
            declared_outside_repo_or_ignored: true,
        },
        runner_config: LocalSoakRunnerConfig::default(),
        notes: Vec::new(),
    }
}

fn assert_roundtrip<T>(
    value: &T,
    serialize: fn(&T) -> Result<String>,
    deserialize: fn(&str) -> Result<T>,
) where
    T: Debug + PartialEq,
{
    let json = serialize(value).expect("value should serialize");
    assert!(
        json.contains('\n'),
        "serializer should emit stable pretty JSON"
    );
    let roundtrip = deserialize(&json).expect("value should deserialize");
    assert_eq!(&roundtrip, value);
}

fn assert_deserialize_error<T>(expected_path: &str, deserialize: fn(&str) -> Result<T>)
where
    T: Debug,
{
    let error = deserialize("{ not valid json").expect_err("invalid JSON should fail");
    let message = error.to_string();
    assert!(
        message.contains("deserialization error"),
        "expected deserialization error, got {message}"
    );
    assert!(
        message.contains(expected_path),
        "expected path {expected_path:?}, got {message}"
    );
}

#[test]
fn soak_serialization_helpers_roundtrip_every_local_artifact_shape() {
    let artifact_root = tempdir().expect("tempdir should be available");
    let soak_config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1)
        .with_output_policy(SoakOutputPolicy::FailurePacksOnly {
            max_failure_packs: 1,
        });
    let plan = plan_soak_shards(soak_config).expect("plan should build");
    let result = run_soak_campaign(
        &approved_config(
            "phase_128_serialization",
            artifact_root.path().to_path_buf(),
        ),
        plan.clone(),
    )
    .expect("campaign should run");
    let outcome = &result.shard_outcomes[0];
    let failure_reproduction = build_failure_corpus_entry(FailureCorpusEntryInput {
        shard_id: SoakShardId::from_index(0),
        case_id: "phase_128_case".to_string(),
        family_kind: FamilyKind::BaselineFsm,
        generator_seed: 128,
        tunables: GeneratorTunables::default(),
        mutation_class: Some(MutationClass::MissingConstraints),
        trace_id: Some("accepted_baseline".to_string()),
        failure_kind: FailureCorpusKind::ReplayFailure,
        local_error_summary: "simulated local replay failure".to_string(),
    })
    .reproduction_manifest;

    assert_roundtrip(
        &plan.config,
        serialize_soak_run_config_json,
        deserialize_soak_run_config_json,
    );
    assert_roundtrip(
        &plan,
        serialize_soak_shard_plan_json,
        deserialize_soak_shard_plan_json,
    );
    assert_roundtrip(
        &plan.shard_manifests[0],
        serialize_soak_shard_manifest_json,
        deserialize_soak_shard_manifest_json,
    );
    assert_roundtrip(
        &outcome.run_result.checkpoint,
        serialize_soak_shard_checkpoint_json,
        deserialize_soak_shard_checkpoint_json,
    );
    assert_roundtrip(
        &outcome.run_result.telemetry_report,
        serialize_soak_telemetry_report_json,
        deserialize_soak_telemetry_report_json,
    );
    assert_roundtrip(
        &outcome.run_result.health_report,
        serialize_soak_health_report_json,
        deserialize_soak_health_report_json,
    );
    assert_roundtrip(
        &outcome.run_result.failure_corpus_index,
        serialize_failure_corpus_index_json,
        deserialize_failure_corpus_index_json,
    );
    assert_roundtrip(
        &failure_reproduction,
        serialize_failure_reproduction_manifest_json,
        deserialize_failure_reproduction_manifest_json,
    );
    assert_roundtrip(
        &result.report_bundle.artifact_digest_set.artifacts[0],
        serialize_soak_artifact_manifest_json,
        deserialize_soak_artifact_manifest_json,
    );
    assert_roundtrip(
        &result.report_bundle,
        serialize_soak_report_bundle_json,
        deserialize_soak_report_bundle_json,
    );

    assert_eq!(result.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert!(!result.contains_zk_backend_performance_claims());
}

#[test]
fn soak_deserializers_report_their_wrapper_path_on_malformed_json() {
    assert_deserialize_error(
        "deserialize_soak_run_config_json",
        deserialize_soak_run_config_json,
    );
    assert_deserialize_error(
        "deserialize_soak_shard_plan_json",
        deserialize_soak_shard_plan_json,
    );
    assert_deserialize_error(
        "deserialize_soak_shard_manifest_json",
        deserialize_soak_shard_manifest_json,
    );
    assert_deserialize_error(
        "deserialize_soak_shard_checkpoint_json",
        deserialize_soak_shard_checkpoint_json,
    );
    assert_deserialize_error(
        "deserialize_soak_telemetry_report_json",
        deserialize_soak_telemetry_report_json,
    );
    assert_deserialize_error(
        "deserialize_soak_health_report_json",
        deserialize_soak_health_report_json,
    );
    assert_deserialize_error(
        "deserialize_failure_corpus_index_json",
        deserialize_failure_corpus_index_json,
    );
    assert_deserialize_error(
        "deserialize_failure_reproduction_manifest_json",
        deserialize_failure_reproduction_manifest_json,
    );
    assert_deserialize_error(
        "deserialize_soak_artifact_manifest_json",
        deserialize_soak_artifact_manifest_json,
    );
    assert_deserialize_error(
        "deserialize_soak_report_bundle_json",
        deserialize_soak_report_bundle_json,
    );
}

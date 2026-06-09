use zkbench_core::{
    apply_mutation_pass, build_local_replay_manifest_for_instance,
    build_local_replay_manifest_for_mutation, deserialize_replay_manifest_json,
    deserialize_replay_result_json, generate_instance, run_local_replay,
    serialize_replay_manifest_json, serialize_replay_result_json, BadCountersPass, ClaimBoundary,
    GeneratorConfig, InstanceParams, ReplayCommand, ReplayMode,
};

#[test]
fn replay_manifest_round_trips_as_deterministic_json() {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(19),
        InstanceParams::default(),
    )
    .expect("generated instance should be available for local replay manifest");
    let manifest = build_local_replay_manifest_for_instance(&instance)
        .expect("local replay manifest should build");

    let json =
        serialize_replay_manifest_json(&manifest).expect("manifest should serialize to JSON");
    let parsed =
        deserialize_replay_manifest_json(&json).expect("manifest should deserialize from JSON");
    let json_again = serialize_replay_manifest_json(&parsed)
        .expect("manifest should serialize deterministically");

    assert_eq!(manifest, parsed);
    assert_eq!(json, json_again);
    assert!(json.contains("local_json_adapter_v0"));
    assert_eq!(manifest.replay_mode, ReplayMode::LocalOracle);
    assert_eq!(manifest.claim_boundary, ClaimBoundary::Level1LocalReplay);
    assert_eq!(
        manifest.commands,
        vec![ReplayCommand::LocalOracleEvaluation]
    );
    assert!(manifest
        .input_artifacts
        .iter()
        .all(|artifact| !artifact.uri.starts_with('/')));
}

#[test]
fn mutated_instance_can_produce_local_replay_manifest() {
    let instance = generate_instance(
        GeneratorConfig::bounded_counter_loop()
            .seed(21)
            .loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded instance should be generated");
    let mutation = apply_mutation_pass(&instance, &BadCountersPass)
        .expect("bad counter mutation should apply");
    let manifest = build_local_replay_manifest_for_mutation(&mutation)
        .expect("mutation replay manifest should build");

    let json =
        serialize_replay_manifest_json(&manifest).expect("mutated manifest should serialize");
    let parsed =
        deserialize_replay_manifest_json(&json).expect("mutated manifest should deserialize");

    assert_eq!(manifest, parsed);
    assert_eq!(parsed.claim_boundary, ClaimBoundary::Level1LocalReplay);
    assert!(parsed
        .input_artifacts
        .iter()
        .all(|artifact| !artifact.uri.starts_with('/')));
    assert_eq!(parsed.commands, vec![ReplayCommand::LocalOracleEvaluation]);
}

#[test]
fn replay_result_round_trips_as_deterministic_json() {
    let instance = generate_instance(
        GeneratorConfig::bounded_counter_loop().seed(23),
        InstanceParams::default(),
    )
    .expect("generated bounded instance should be available");
    let manifest = build_local_replay_manifest_for_instance(&instance)
        .expect("local replay manifest should build");
    let result = run_local_replay(&manifest).expect("local replay should run");

    let json = serialize_replay_result_json(&result).expect("result should serialize to JSON");
    let parsed = deserialize_replay_result_json(&json).expect("result should deserialize");
    let json_again = serialize_replay_result_json(&parsed).expect("result should reserialize");

    assert_eq!(result, parsed);
    assert_eq!(json, json_again);
    assert_eq!(parsed.claim_boundary, ClaimBoundary::Level1LocalReplay);
    assert_eq!(parsed.evidence_records.len(), parsed.trace_results.len());
}

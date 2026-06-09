use zkbench_core::{
    apply_mutation_pass, build_local_replay_manifest_for_instance,
    build_local_replay_manifest_for_mutation, generate_instance, local_json_capabilities,
    BackendOutcome, ClaimBoundary, ExpectedVerdict, GeneratorConfig, InstanceParams,
    LocalJsonAdapter, LocalJsonReplayInput, MissingConstraintsPass, ReplayCommand, ReplayMode,
    ResultClassification,
};

#[test]
fn local_json_adapter_evaluates_embedded_generated_instance() {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(31),
        InstanceParams::default(),
    )
    .expect("generated instance should be available");
    let manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    let adapter = LocalJsonAdapter::default();
    let output = adapter
        .replay_with_summary(LocalJsonReplayInput { manifest })
        .expect("local JSON adapter should replay embedded manifest");

    assert_eq!(
        output.replay_result.claim_boundary,
        ClaimBoundary::Level1LocalReplay
    );
    assert_eq!(
        output.replay_result.evidence_records.len(),
        output.replay_result.trace_results.len()
    );
    assert_eq!(
        output.summary.trace_count,
        output.replay_result.trace_results.len()
    );
    assert!(output.summary.local_accepted_count >= 1);
    assert!(output.summary.local_rejected_count >= 1);
}

#[test]
fn local_json_adapter_evaluates_bounded_counter_traces() {
    let instance = generate_instance(
        GeneratorConfig::bounded_counter_loop()
            .seed(33)
            .loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded generated instance should be available");
    let manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    let result = LocalJsonAdapter::default()
        .replay(&manifest)
        .expect("local JSON adapter should replay bounded counter manifest");

    assert!(result.trace_results.iter().any(|trace| {
        trace.result_classification == ResultClassification::ExpectedAcceptAccepted
    }));
    assert!(result.trace_results.iter().any(|trace| {
        trace.result_classification == ResultClassification::ExpectedRejectRejected
    }));
    assert_eq!(result.claim_boundary, ClaimBoundary::Level1LocalReplay);
}

#[test]
fn local_json_adapter_evaluates_mutated_instance() {
    let instance = generate_instance(
        GeneratorConfig::branching_fsm().seed(35),
        InstanceParams::default(),
    )
    .expect("branching generated instance should be available");
    let mutation = apply_mutation_pass(&instance, &MissingConstraintsPass)
        .expect("missing constraints mutation should apply");
    let manifest = build_local_replay_manifest_for_mutation(&mutation)
        .expect("mutation manifest should build");
    let result = LocalJsonAdapter::default()
        .replay(&manifest)
        .expect("local JSON adapter should replay mutation manifest");

    assert_eq!(result.trace_results.len(), 1);
    assert_eq!(result.evidence_records.len(), 1);
    assert_eq!(result.claim_boundary, ClaimBoundary::Level1LocalReplay);
}

#[test]
fn local_json_capabilities_do_not_claim_external_backend_features() {
    let capabilities = local_json_capabilities();

    assert!(capabilities.supports_execution);
    assert!(capabilities.supports_negative_tests);
    assert!(capabilities.supports_replay_manifest);
    assert!(capabilities.supports_artifact_hashing);
    assert!(!capabilities.supports_proving);
    assert!(!capabilities.supports_verification_timing);
    assert!(!capabilities.supports_formal_semantics);
    assert!(!capabilities.supports_machine_checked_proof);
}

#[test]
fn mock_backend_outcome_classifies_unsound_acceptance_candidate_without_proving_exploit() {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(37),
        InstanceParams::default(),
    )
    .expect("generated instance should be available");
    let mut manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    let rejected_trace = instance
        .rejected_traces
        .first()
        .expect("generated instance should include rejected trace");
    manifest.replay_mode = ReplayMode::MockOutcome;
    manifest.selected_traces = vec![zkbench_core::ReplayTraceSelection {
        trace_id: rejected_trace.id.clone(),
        expected_verdict: ExpectedVerdict::Reject,
    }];
    manifest.expected_outcomes = vec![zkbench_core::ReplayExpectedOutcome {
        trace_id: rejected_trace.id.clone(),
        expected_verdict: ExpectedVerdict::Reject,
    }];
    manifest.commands = vec![ReplayCommand::MockOutcomeEvaluation {
        outcome: BackendOutcome::Accepted,
    }];

    let result = LocalJsonAdapter::default()
        .replay(&manifest)
        .expect("mock replay should classify configured outcome");
    assert_eq!(
        result.trace_results[0].result_classification,
        ResultClassification::ExpectedRejectAcceptedUnsoundCandidate
    );
    assert!(result.trace_results[0]
        .notes
        .iter()
        .any(|note| note.contains("candidate")));
}

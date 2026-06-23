use zkbench_core::{
    apply_mutation_pass, build_local_replay_manifest_for_instance,
    build_local_replay_manifest_for_mutation, generate_instance, local_json_capabilities,
    BackendAdapter, BackendOutcome, BenchmarkInstance, ClaimBoundary, ExpectedVerdict,
    GeneratorConfig, InstanceParams, LocalJsonAdapter, LocalJsonReplayInput,
    MissingConstraintsPass, ReplayCommand, ReplayMode, ReplayStatus, ResultClassification,
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
    assert_eq!(result.status, ReplayStatus::Completed);
}

#[test]
fn local_json_adapter_rejects_claim_adapter_and_subject_drift() {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(41),
        InstanceParams::default(),
    )
    .expect("generated instance should be available");
    let manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    let adapter = LocalJsonAdapter::default();

    let mut elevated = manifest.clone();
    elevated.claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    assert!(adapter.replay(&elevated).is_err());

    let mut wrong_adapter = manifest.clone();
    wrong_adapter.adapter_id = "other_adapter".to_string();
    assert!(adapter.replay(&wrong_adapter).is_err());

    let mut missing_generated_payload = manifest.clone();
    missing_generated_payload.subject.generated_instance = None;
    assert!(adapter.replay(&missing_generated_payload).is_err());

    let mut unknown_trace = manifest.clone();
    unknown_trace.selected_traces[0].trace_id = "missing_trace".to_string();
    assert!(adapter.replay(&unknown_trace).is_err());
}

#[test]
fn local_json_adapter_rejects_mutated_payload_and_trace_drift() {
    let instance = generate_instance(
        GeneratorConfig::branching_fsm().seed(43),
        InstanceParams::default(),
    )
    .expect("branching generated instance should be available");
    let mutation = apply_mutation_pass(&instance, &MissingConstraintsPass)
        .expect("missing constraints mutation should apply");
    let manifest = build_local_replay_manifest_for_mutation(&mutation)
        .expect("mutation manifest should build");
    let adapter = LocalJsonAdapter::default();

    let mut missing_mutation_payload = manifest.clone();
    missing_mutation_payload.subject.mutated_instance = None;
    assert!(adapter.replay(&missing_mutation_payload).is_err());

    let mut wrong_mutation_trace = manifest.clone();
    wrong_mutation_trace.selected_traces[0].trace_id = "wrong_mutation_trace".to_string();
    assert!(adapter.replay(&wrong_mutation_trace).is_err());
}

#[test]
fn mock_mode_statuses_and_missing_command_fail_closed() {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(47),
        InstanceParams::default(),
    )
    .expect("generated instance should be available");
    let mut manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    manifest.replay_mode = ReplayMode::MockOutcome;
    manifest.selected_traces.truncate(1);
    manifest.expected_outcomes.truncate(1);

    let mut missing_mock_command = manifest.clone();
    missing_mock_command.commands = vec![ReplayCommand::LocalOracleEvaluation];
    assert!(LocalJsonAdapter::default()
        .replay(&missing_mock_command)
        .is_err());

    let mut capability_gap = manifest.clone();
    capability_gap.commands = vec![ReplayCommand::MockOutcomeEvaluation {
        outcome: BackendOutcome::CapabilityGap,
    }];
    let capability_gap_output = LocalJsonAdapter::default()
        .replay_with_summary(LocalJsonReplayInput {
            manifest: capability_gap,
        })
        .expect("mock capability gap should replay");
    assert_eq!(
        capability_gap_output.replay_result.status,
        ReplayStatus::CapabilityGap
    );
    assert_eq!(capability_gap_output.summary.inconclusive_count, 1);

    let mut inconclusive = manifest;
    inconclusive.commands = vec![ReplayCommand::MockOutcomeEvaluation {
        outcome: BackendOutcome::Inconclusive,
    }];
    let inconclusive_output = LocalJsonAdapter::default()
        .replay_with_summary(LocalJsonReplayInput {
            manifest: inconclusive,
        })
        .expect("mock inconclusive should replay");
    assert_eq!(
        inconclusive_output.replay_result.status,
        ReplayStatus::Inconclusive
    );
    assert_eq!(inconclusive_output.summary.inconclusive_count, 1);
}

#[test]
fn backend_adapter_trait_methods_stay_local_and_fail_closed() {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(53),
        InstanceParams::default(),
    )
    .expect("generated instance should be available");
    let legacy_instance = BenchmarkInstance {
        id: instance.id.clone(),
        family_id: instance.family_id.clone(),
        machine_id: "local-machine".to_string(),
        trace_ids: instance
            .accepted_traces
            .iter()
            .chain(instance.rejected_traces.iter())
            .map(|trace| trace.id.clone())
            .collect(),
        mutation_variant_id: None,
        expected_verdict: ExpectedVerdict::Accept,
        claim_boundary_max: ClaimBoundary::Level1LocalReplay,
    };
    let adapter = LocalJsonAdapter::default();
    let prepared = adapter
        .prepare_replay(&instance.semantic_ir, &legacy_instance)
        .expect("legacy manifest preparation should succeed");
    assert_eq!(prepared.adapter_id, "local_json_adapter_v0");
    assert!(prepared.subject.generated_instance.is_none());
    assert!(adapter.replay(&prepared).is_err());

    let valid_manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    let mut result = adapter
        .replay(&valid_manifest)
        .expect("local replay should produce evidence records");
    assert!(adapter.normalize_result(&result).is_ok());
    result.evidence_records.clear();
    assert!(adapter.normalize_result(&result).is_err());
}

use tempfile::tempdir;
use zkbench_core::{
    build_local_replay_manifest_for_instance, build_manual_handoff_bundle_from_zk_harness_plan,
    build_smoke_soak_config, build_soak_report_bundle, build_zk_harness_dry_run_plan_from_pack,
    create_evidence_append_proposal, deserialize_artifact_capture_contract_json,
    deserialize_evidence_append_proposal_json, deserialize_evidence_append_proposal_ledger_json,
    deserialize_external_result_candidate_json, deserialize_external_result_import_schema_json,
    deserialize_external_runner_policy_json, deserialize_manual_handoff_bundle_json,
    deserialize_normalized_external_result_draft_json, deserialize_provenance_contract_json,
    deserialize_quarantine_manifest_json, deserialize_replay_manifest_json,
    deserialize_replay_result_json, deserialize_synthetic_result_import_bundle_json,
    generate_instance, import_synthetic_result_candidate_json,
    normalize_synthetic_result_candidate, plan_soak_shards, run_local_replay,
    serialize_artifact_capture_contract_json, serialize_evidence_append_proposal_json,
    serialize_evidence_append_proposal_ledger_json, serialize_external_result_candidate_json,
    serialize_external_result_import_schema_json, serialize_external_runner_policy_json,
    serialize_manual_handoff_bundle_json, serialize_normalized_external_result_draft_json,
    serialize_provenance_contract_json, serialize_quarantine_manifest_json,
    serialize_synthetic_result_import_bundle_json, validate_synthetic_result_candidate,
    AdapterCapabilitySet, BackendAdapter, BackendTarget, BenchmarkInstance, BenchmarkPackReader,
    BenchmarkPackWriter, ClaimBoundary, EvidenceLedger, EvidenceRecord, FamilyKind,
    GeneratorConfig, InstanceParams, LocalSoakRunner, MockTelemetryClock, MutationClass,
    ReplayManifest, ReplayResult, ResultCandidateArtifactResolver, SemanticIr, SoakArtifactRole,
    SoakOutputPolicy, SoakShardId, ZkBenchError,
};

fn tiny_soak_run() -> (zkbench_core::SoakShardPlan, zkbench_core::SoakRunResult) {
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1)
        .with_output_policy(SoakOutputPolicy::NoPacks);
    let plan = plan_soak_shards(config).expect("plan should build");
    let mut runner = LocalSoakRunner::new(plan.clone()).with_clock(MockTelemetryClock::default());
    let result = runner
        .run_shard(SoakShardId::from_index(0))
        .expect("tiny soak shard should run");
    (plan, result)
}

fn resolver() -> ResultCandidateArtifactResolver {
    ResultCandidateArtifactResolver::from_in_memory_bytes(vec![(
        "artifacts/synthetic_metric_source.json".to_string(),
        b"synthetic metric source v1\n".to_vec(),
    )])
}

fn assert_deserialization_path<T>(result: zkbench_core::Result<T>, expected_path: &str) {
    match result {
        Err(ZkBenchError::Deserialization { path, message }) => {
            assert_eq!(path, expected_path);
            assert!(!message.is_empty());
        }
        Err(other) => panic!("expected deserialization error, got {other:?}"),
        Ok(_) => panic!("expected deserialization error, got success"),
    }
}

fn dry_run_plan() -> zkbench_core::ZkHarnessDryRunPlan {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(101),
        InstanceParams::default(),
    )
    .expect("baseline instance should generate");
    let manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    let result = run_local_replay(&manifest).expect("local replay should run");
    let mut ledger = EvidenceLedger::new();
    ledger
        .append_replay_result(&result)
        .expect("ledger append should work");

    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_v_serialization_pack")
        .with_generated_instance(instance)
        .with_replay_manifest(manifest)
        .with_replay_result(result)
        .with_evidence_ledger(ledger)
        .write_to(dir.path())
        .expect("pack should write");
    let reader = BenchmarkPackReader::read(dir.path()).expect("pack should read");
    build_zk_harness_dry_run_plan_from_pack(&reader).expect("dry-run plan should build")
}

#[test]
fn soak_report_bundle_builder_keeps_local_claim_boundary_and_artifact_roles() {
    let (plan, result) = tiny_soak_run();

    let bundle = build_soak_report_bundle(
        "phase_v_local_soak_bundle",
        plan,
        vec![result.telemetry_report],
        vec![result.health_report],
        vec![result.failure_corpus_index],
    )
    .expect("bundle should build from shard outputs");

    assert_eq!(bundle.bundle_id, "phase_v_local_soak_bundle");
    assert_eq!(bundle.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(bundle.telemetry_reports.len(), 1);
    assert_eq!(bundle.health_reports.len(), 1);
    assert_eq!(bundle.failure_corpus_indexes.len(), 1);
    assert!(bundle
        .notes
        .iter()
        .any(|note| note.contains("Local soak telemetry is not official benchmark evidence.")));

    let roles = bundle
        .artifact_digest_set
        .artifacts
        .iter()
        .map(|artifact| artifact.role)
        .collect::<Vec<_>>();
    assert_eq!(
        roles,
        vec![
            SoakArtifactRole::RunConfig,
            SoakArtifactRole::ShardPlan,
            SoakArtifactRole::Telemetry,
            SoakArtifactRole::HealthReport,
            SoakArtifactRole::FailureCorpusIndex,
        ]
    );

    let validation = zkbench_core::soak::validation::validate_report_bundle(&bundle);
    assert!(validation.valid, "{:?}", validation.issues);
}

#[test]
fn soak_validation_facade_exercises_local_artifact_validators() {
    let (plan, result) = tiny_soak_run();
    let manifest = &plan.shard_manifests[0];
    let expected_resume_token = manifest
        .resume_token
        .as_ref()
        .expect("planned manifest should carry a resume token");

    zkbench_core::soak::validation::validate_config(&plan.config).expect("config should validate");
    zkbench_core::soak::validation::validate_shard_plan(&plan).expect("shard plan should validate");
    assert!(zkbench_core::soak::validation::validate_shard_manifest(manifest).valid);
    assert!(zkbench_core::soak::validation::validate_shard_summary(&result.shard_summary).valid);
    zkbench_core::soak::validation::validate_checkpoint(
        &result.checkpoint,
        &plan.config_digest,
        expected_resume_token,
    )
    .expect("checkpoint should validate");
    zkbench_core::soak::validation::validate_telemetry(&result.telemetry_report)
        .expect("telemetry report should validate");
    zkbench_core::soak::validation::validate_health_report(&result.health_report)
        .expect("health report should validate");
    zkbench_core::soak::validation::validate_failure_corpus(&result.failure_corpus_index)
        .expect("failure corpus should validate");
}

#[test]
fn zero_coverage_facades_exercise_public_contract_methods() {
    struct DummyAdapter {
        target: BackendTarget,
    }

    impl BackendAdapter for DummyAdapter {
        fn target(&self) -> BackendTarget {
            self.target.clone()
        }

        fn prepare_replay(
            &self,
            _ir: &SemanticIr,
            _instance: &BenchmarkInstance,
        ) -> zkbench_core::Result<ReplayManifest> {
            unimplemented!("test only exercises the default capability method")
        }

        fn normalize_result(&self, _result: &ReplayResult) -> zkbench_core::Result<EvidenceRecord> {
            unimplemented!("test only exercises the default capability method")
        }
    }

    let adapter = DummyAdapter {
        target: BackendTarget {
            id: "phase_v_dummy".to_string(),
            kind: "local_contract_only".to_string(),
            version: Some("v0".to_string()),
            capabilities: AdapterCapabilitySet {
                supports_replay_manifest: true,
                supports_artifact_hashing: true,
                ..AdapterCapabilitySet::default()
            },
        },
    };
    let capabilities = adapter.capabilities();
    assert!(capabilities.supports_replay_manifest);
    assert!(capabilities.supports_artifact_hashing);

    let surface = zkbench_core::SurfaceSpec {
        machine: zkbench_core::MachineSpec {
            id: "phase_v_machine".to_string(),
            description: None,
            initial_state: "start".to_string(),
            semantic_equivalence_class: None,
            states: vec![zkbench_core::StateSpec {
                id: "start".to_string(),
                description: None,
            }],
            fields: Vec::new(),
            transitions: Vec::new(),
            loops: Vec::new(),
            invariants: Vec::new(),
            observations: Vec::new(),
            witness_policy: zkbench_core::WitnessPolicy::default(),
            public_inputs: Vec::new(),
            private_witnesses: Vec::new(),
        },
        oracle: zkbench_core::OracleSpec::default(),
        targets: vec![zkbench_core::TargetSpec {
            id: "local".to_string(),
            kind: "local_oracle".to_string(),
            required_capabilities: vec!["replay_manifest".to_string()],
        }],
        mutations: Vec::new(),
        evidence: zkbench_core::EvidenceSpec::default(),
    };
    let surface_json = serde_json::to_string(&surface).expect("surface should serialize");
    let parsed: zkbench_core::SurfaceSpec =
        serde_json::from_str(&surface_json).expect("surface should deserialize");
    assert_eq!(
        parsed.evidence.claim_boundary,
        ClaimBoundary::Level0DesignNote
    );

    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(7),
        InstanceParams::default(),
    )
    .expect("baseline instance should generate");
    let manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    let replay = run_local_replay(&manifest).expect("local replay should run");
    assert_eq!(replay.output_artifacts().len(), replay.artifact_refs.len());
}

#[test]
fn external_runner_serialization_helpers_roundtrip_valid_local_artifacts() {
    let plan = dry_run_plan();
    let handoff = build_manual_handoff_bundle_from_zk_harness_plan(&plan)
        .expect("manual handoff should build");
    let candidate = deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_valid.json"
    ))
    .expect("candidate fixture should parse");
    let resolver = resolver();
    let validation = validate_synthetic_result_candidate(&candidate, &resolver);
    let draft = normalize_synthetic_result_candidate(&candidate, &validation, &resolver)
        .expect("candidate should normalize");
    let proposal = create_evidence_append_proposal(&draft).expect("proposal should build");
    let mut ledger = zkbench_core::EvidenceAppendProposalLedger::new();
    ledger
        .append(proposal.clone())
        .expect("proposal append should work");
    let bundle = import_synthetic_result_candidate_json(
        include_str!("fixtures/synthetic_result_candidate_valid.json"),
        &resolver,
    )
    .expect("valid synthetic import should build a bundle");
    let quarantine_bundle = import_synthetic_result_candidate_json(
        include_str!("fixtures/synthetic_result_candidate_bad_digest.json"),
        &resolver,
    )
    .expect("bad synthetic import should build a quarantine bundle");
    let quarantine = quarantine_bundle
        .quarantine_manifest
        .as_ref()
        .expect("quarantine manifest should be present");

    let policy_json = serialize_external_runner_policy_json(&handoff.external_runner_policy)
        .expect("policy should serialize");
    assert_eq!(
        deserialize_external_runner_policy_json(&policy_json).expect("policy should deserialize"),
        handoff.external_runner_policy
    );

    let handoff_json =
        serialize_manual_handoff_bundle_json(&handoff).expect("handoff should serialize");
    assert_eq!(
        deserialize_manual_handoff_bundle_json(&handoff_json).expect("handoff should deserialize"),
        handoff
    );

    let capture_json = serialize_artifact_capture_contract_json(&handoff.artifact_capture_contract)
        .expect("capture contract should serialize");
    assert_eq!(
        deserialize_artifact_capture_contract_json(&capture_json)
            .expect("capture contract should deserialize"),
        handoff.artifact_capture_contract
    );

    let provenance_json = serialize_provenance_contract_json(&handoff.provenance_contract)
        .expect("provenance contract should serialize");
    assert_eq!(
        deserialize_provenance_contract_json(&provenance_json)
            .expect("provenance contract should deserialize"),
        handoff.provenance_contract
    );

    let schema_json = serialize_external_result_import_schema_json(&handoff.result_import_schema)
        .expect("schema should serialize");
    assert_eq!(
        deserialize_external_result_import_schema_json(&schema_json)
            .expect("schema should deserialize"),
        handoff.result_import_schema
    );

    let candidate_json =
        serialize_external_result_candidate_json(&candidate).expect("candidate should serialize");
    assert_eq!(
        deserialize_external_result_candidate_json(&candidate_json)
            .expect("candidate should deserialize"),
        candidate
    );

    let quarantine_json =
        serialize_quarantine_manifest_json(quarantine).expect("quarantine should serialize");
    assert_eq!(
        deserialize_quarantine_manifest_json(&quarantine_json)
            .expect("quarantine should deserialize"),
        *quarantine
    );

    let bundle_json =
        serialize_synthetic_result_import_bundle_json(&bundle).expect("bundle should serialize");
    assert_eq!(
        deserialize_synthetic_result_import_bundle_json(&bundle_json)
            .expect("bundle should deserialize"),
        bundle
    );

    let draft_json =
        serialize_normalized_external_result_draft_json(&draft).expect("draft should serialize");
    assert_eq!(
        deserialize_normalized_external_result_draft_json(&draft_json)
            .expect("draft should deserialize"),
        draft
    );

    let proposal_json =
        serialize_evidence_append_proposal_json(&proposal).expect("proposal should serialize");
    assert_eq!(
        deserialize_evidence_append_proposal_json(&proposal_json)
            .expect("proposal should deserialize"),
        proposal
    );

    let ledger_json =
        serialize_evidence_append_proposal_ledger_json(&ledger).expect("ledger should serialize");
    assert_eq!(
        deserialize_evidence_append_proposal_ledger_json(&ledger_json)
            .expect("ledger should deserialize"),
        ledger
    );
}

#[test]
fn external_runner_and_replay_deserializers_preserve_error_context() {
    let invalid_json = "{";

    assert_deserialization_path(
        deserialize_external_runner_policy_json(invalid_json),
        "deserialize_external_runner_policy_json",
    );
    assert_deserialization_path(
        deserialize_manual_handoff_bundle_json(invalid_json),
        "deserialize_manual_handoff_bundle_json",
    );
    assert_deserialization_path(
        deserialize_artifact_capture_contract_json(invalid_json),
        "deserialize_artifact_capture_contract_json",
    );
    assert_deserialization_path(
        deserialize_provenance_contract_json(invalid_json),
        "deserialize_provenance_contract_json",
    );
    assert_deserialization_path(
        deserialize_external_result_import_schema_json(invalid_json),
        "deserialize_external_result_import_schema_json",
    );
    assert_deserialization_path(
        deserialize_external_result_candidate_json(invalid_json),
        "deserialize_external_result_candidate_json",
    );
    assert_deserialization_path(
        deserialize_quarantine_manifest_json(invalid_json),
        "deserialize_quarantine_manifest_json",
    );
    assert_deserialization_path(
        deserialize_synthetic_result_import_bundle_json(invalid_json),
        "deserialize_synthetic_result_import_bundle_json",
    );
    assert_deserialization_path(
        deserialize_normalized_external_result_draft_json(invalid_json),
        "deserialize_normalized_external_result_draft_json",
    );
    assert_deserialization_path(
        deserialize_evidence_append_proposal_json(invalid_json),
        "deserialize_evidence_append_proposal_json",
    );
    assert_deserialization_path(
        deserialize_evidence_append_proposal_ledger_json(invalid_json),
        "deserialize_evidence_append_proposal_ledger_json",
    );
    assert_deserialization_path(
        deserialize_replay_manifest_json(invalid_json),
        "deserialize_replay_manifest_json",
    );
    assert_deserialization_path(
        deserialize_replay_result_json(invalid_json),
        "deserialize_replay_result_json",
    );
}

#[test]
fn zkbench_error_constructors_and_parse_conversions_keep_context() {
    let cases = [
        (
            ZkBenchError::validation("surface.states", "missing initial state"),
            "validation error at surface.states: missing initial state",
        ),
        (
            ZkBenchError::lowering("machine.transitions", "unknown target"),
            "lowering error at machine.transitions: unknown target",
        ),
        (
            ZkBenchError::oracle("trace[1]", "guard mismatch"),
            "oracle error at trace[1]: guard mismatch",
        ),
        (
            ZkBenchError::generation("seed", "out of range"),
            "generation error at seed: out of range",
        ),
        (
            ZkBenchError::mutation("pass", "no target"),
            "mutation error at pass: no target",
        ),
        (
            ZkBenchError::replay("manifest", "missing adapter"),
            "replay error at manifest: missing adapter",
        ),
        (
            ZkBenchError::evidence_ledger("ledger[0]", "stale digest"),
            "evidence ledger error at ledger[0]: stale digest",
        ),
        (
            ZkBenchError::artifact("artifacts/result.json", "digest mismatch"),
            "artifact error at artifacts/result.json: digest mismatch",
        ),
        (
            ZkBenchError::benchmark_pack("pack", "missing manifest"),
            "benchmark pack error at pack: missing manifest",
        ),
        (
            ZkBenchError::zk_harness("dry_run", "live mode forbidden"),
            "zk-Harness dry-run error at dry_run: live mode forbidden",
        ),
        (
            ZkBenchError::external_runner("policy", "manual handoff required"),
            "external-runner boundary error at policy: manual handoff required",
        ),
        (
            ZkBenchError::synthetic_import("candidate", "missing provenance"),
            "synthetic result import error at candidate: missing provenance",
        ),
        (
            ZkBenchError::evidence_append_proposal("proposal", "not reviewed"),
            "evidence append proposal error at proposal: not reviewed",
        ),
        (
            ZkBenchError::evidence_review("decision", "missing reviewer"),
            "evidence review error at decision: missing reviewer",
        ),
        (
            ZkBenchError::evidence_acceptance_policy("policy", "level2 blocked"),
            "evidence acceptance policy error at policy: level2 blocked",
        ),
        (
            ZkBenchError::evidence_record_candidate("candidate", "claim too high"),
            "evidence record candidate error at candidate: claim too high",
        ),
        (
            ZkBenchError::evidence_append_preview("preview", "accepted evidence forbidden"),
            "evidence append preview error at preview: accepted evidence forbidden",
        ),
        (
            ZkBenchError::level2_eligibility("report", "insufficient information"),
            "Level2 eligibility error at report: insufficient information",
        ),
        (
            ZkBenchError::evidence_review_ledger("ledger", "tampered"),
            "evidence review ledger error at ledger: tampered",
        ),
        (
            ZkBenchError::soak("shard", "checkpoint mismatch"),
            "local soak error at shard: checkpoint mismatch",
        ),
        (
            ZkBenchError::serialization("writer", "unsupported value"),
            "serialization error at writer: unsupported value",
        ),
        (
            ZkBenchError::deserialization("reader", "bad json"),
            "deserialization error at reader: bad json",
        ),
        (
            ZkBenchError::ClaimBoundary {
                message: "cannot exceed Level1LocalReplay".to_string(),
            },
            "claim boundary error: cannot exceed Level1LocalReplay",
        ),
    ];

    for (error, display) in cases {
        assert_eq!(error.to_string(), display);
    }

    let json_error: ZkBenchError = serde_json::from_str::<serde_json::Value>("{")
        .expect_err("invalid JSON should fail")
        .into();
    assert!(matches!(json_error, ZkBenchError::Parse { .. }));

    let yaml_error: ZkBenchError = serde_yaml::from_str::<serde_yaml::Value>(": bad")
        .expect_err("invalid YAML should fail")
        .into();
    assert!(matches!(yaml_error, ZkBenchError::Parse { .. }));
}

use zkbench_core::{
    build_recursion_adapter_manual_handoff_bundle, compute_recursion_envelope_digest_chain_root,
    deserialize_recursion_adapter_manual_handoff_bundle_json,
    deserialize_recursion_adapter_preparation_plan_json,
    deserialize_recursion_envelope_candidate_json,
    validate_recursion_adapter_manual_handoff_bundle, validate_recursion_adapter_preparation_plan,
    validate_recursion_envelope_candidate, ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind,
    ArtifactRole, ClaimBoundary, EvidenceClass, RecursionAdapterPreparationArtifact,
    RecursionAdapterPreparationArtifactRole, RecursionAdapterPreparationIssueKind,
    RecursionAdapterPreparationPlan, RecursionAdapterPreparationTarget, RecursionEnvelopeCandidate,
    RecursionEnvelopeInputKind, RecursionEnvelopeInputRef, RecursionEnvelopeMetric,
    RecursionEnvelopeMetricKind, RecursionEnvelopeValidationIssueKind, RecursionEnvelopeVersion,
};

fn digest(byte: u8) -> ArtifactDigest {
    ArtifactDigest {
        algorithm: ArtifactDigestAlgorithm::Sha256,
        hex_digest: format!("{byte:02x}").repeat(32),
        byte_len: 64,
        kind: Some(ArtifactKind::Other),
        role: Some(ArtifactRole::Digest),
    }
}

fn malformed_digest() -> ArtifactDigest {
    ArtifactDigest {
        algorithm: ArtifactDigestAlgorithm::Unsupported,
        hex_digest: "ABC".to_string(),
        byte_len: 0,
        kind: Some(ArtifactKind::Other),
        role: Some(ArtifactRole::Digest),
    }
}

fn input(
    input_id: &str,
    artifact_uri: &str,
    kind: RecursionEnvelopeInputKind,
    claim_boundary: ClaimBoundary,
    evidence_class: EvidenceClass,
    digest: ArtifactDigest,
) -> RecursionEnvelopeInputRef {
    RecursionEnvelopeInputRef {
        input_id: input_id.to_string(),
        artifact_uri: artifact_uri.to_string(),
        kind,
        digest,
        evidence_class,
        claim_boundary,
        notes: Vec::new(),
    }
}

fn valid_inputs() -> Vec<RecursionEnvelopeInputRef> {
    vec![
        input(
            "local_replay",
            "artifacts/local_replay.json",
            RecursionEnvelopeInputKind::LocalReplayResult,
            ClaimBoundary::Level1LocalReplay,
            EvidenceClass::LocalReplay,
            digest(1),
        ),
        input(
            "append_preview",
            "artifacts/append_preview.json",
            RecursionEnvelopeInputKind::EvidenceAppendPreview,
            ClaimBoundary::Level0DesignNote,
            EvidenceClass::DesignNote,
            digest(2),
        ),
    ]
}

fn valid_candidate() -> RecursionEnvelopeCandidate {
    let inputs = valid_inputs();
    let digest_chain_root =
        compute_recursion_envelope_digest_chain_root(&inputs).expect("root should compute");
    RecursionEnvelopeCandidate {
        envelope_id: "phase_191_recursion_candidate".to_string(),
        version: RecursionEnvelopeVersion::default(),
        inputs,
        recursion_depth: 2,
        aggregation_width: 2,
        digest_chain_root,
        verifier_acceptance_status: None,
        executable_adapter_authorized: false,
        metrics: vec![RecursionEnvelopeMetric {
            kind: RecursionEnvelopeMetricKind::RecursionDepth,
            value: Some(2),
            claim_boundary: ClaimBoundary::Level0DesignNote,
            notes: Vec::new(),
        }],
        output_claim_boundary: ClaimBoundary::Level0DesignNote,
        limitations: vec!["recursion proof is not semantic proof".to_string()],
        notes: Vec::new(),
    }
}

fn valid_preparation_plan() -> RecursionAdapterPreparationPlan {
    RecursionAdapterPreparationPlan {
        plan_id: "phase_191_recursion_preparation".to_string(),
        version: RecursionEnvelopeVersion::default(),
        target: RecursionAdapterPreparationTarget::GnarkPlonk,
        source_inputs: valid_inputs(),
        expected_artifacts: vec![RecursionAdapterPreparationArtifact {
            artifact_id: "input_manifest".to_string(),
            artifact_uri: "artifacts/input_manifest.json".to_string(),
            role: RecursionAdapterPreparationArtifactRole::InputManifest,
            required: true,
            notes: Vec::new(),
        }],
        executable_adapter_authorized: false,
        executable_steps: Vec::new(),
        claim_boundary: ClaimBoundary::Level0DesignNote,
        limitations: vec!["recursion proof is not semantic proof".to_string()],
        notes: Vec::new(),
    }
}

#[test]
fn recursion_candidate_validation_reports_empty_shape_digest_and_metric_boundary() {
    let mut candidate = valid_candidate();
    candidate.envelope_id = " ".to_string();
    candidate.version.value.clear();
    candidate.inputs[0].input_id.clear();
    candidate.inputs[0].artifact_uri = " ".to_string();
    candidate.inputs[0].digest = malformed_digest();
    candidate.digest_chain_root = malformed_digest();
    candidate.metrics.push(RecursionEnvelopeMetric {
        kind: RecursionEnvelopeMetricKind::AggregationWidth,
        value: Some(2),
        claim_boundary: ClaimBoundary::Level1LocalReplay,
        notes: Vec::new(),
    });

    let validation = validate_recursion_envelope_candidate(&candidate);
    let kinds: Vec<_> = validation.issues.iter().map(|issue| issue.kind).collect();
    let paths: Vec<_> = validation
        .issues
        .iter()
        .map(|issue| issue.path.as_str())
        .collect();

    assert!(!validation.valid);
    assert!(kinds.contains(&RecursionEnvelopeValidationIssueKind::EmptyIdentity));
    assert!(kinds.contains(&RecursionEnvelopeValidationIssueKind::InvalidDigest));
    assert!(kinds.contains(&RecursionEnvelopeValidationIssueKind::ClaimBoundaryEscalation));
    assert!(paths.contains(&"envelope_id"));
    assert!(paths.contains(&"version.value"));
    assert!(paths.contains(&"inputs[0].input_id"));
    assert!(paths.contains(&"inputs[0].artifact_uri"));
    assert!(paths.contains(&"inputs[0].digest"));
    assert!(paths.contains(&"digest_chain_root"));
    assert!(paths.contains(&"metrics[1].claim_boundary"));
}

#[test]
fn recursion_candidate_missing_inputs_reports_missing_inputs_without_boundary_floor() {
    let inputs = Vec::new();
    let digest_chain_root =
        compute_recursion_envelope_digest_chain_root(&inputs).expect("empty root should compute");
    let mut candidate = valid_candidate();
    candidate.inputs = inputs;
    candidate.digest_chain_root = digest_chain_root;

    let validation = validate_recursion_envelope_candidate(&candidate);

    assert!(!validation.valid);
    assert_eq!(
        validation
            .issues
            .iter()
            .filter(|issue| issue.kind == RecursionEnvelopeValidationIssueKind::MissingInputs)
            .count(),
        1
    );
}

#[test]
fn recursion_preparation_validation_reports_empty_plan_shape() {
    let mut plan = valid_preparation_plan();
    plan.plan_id.clear();
    plan.version.value.clear();
    plan.source_inputs.clear();
    plan.expected_artifacts.clear();

    let validation = validate_recursion_adapter_preparation_plan(&plan);
    let kinds: Vec<_> = validation.issues.iter().map(|issue| issue.kind).collect();
    let paths: Vec<_> = validation
        .issues
        .iter()
        .map(|issue| issue.path.as_str())
        .collect();

    assert!(!validation.valid);
    assert!(kinds.contains(&RecursionAdapterPreparationIssueKind::EmptyIdentity));
    assert!(kinds.contains(&RecursionAdapterPreparationIssueKind::MissingInputs));
    assert!(kinds.contains(&RecursionAdapterPreparationIssueKind::MissingExpectedArtifacts));
    assert!(paths.contains(&"plan_id"));
    assert!(paths.contains(&"version.value"));
    assert!(paths.contains(&"source_inputs"));
    assert!(paths.contains(&"expected_artifacts"));
}

#[test]
fn recursion_preparation_validation_reports_nested_input_and_artifact_failures() {
    let mut plan = valid_preparation_plan();
    plan.source_inputs = vec![
        input(
            "",
            "artifacts\\bad.json",
            RecursionEnvelopeInputKind::EvidenceAppendPreview,
            ClaimBoundary::Level1LocalReplay,
            EvidenceClass::DesignNote,
            malformed_digest(),
        ),
        input(
            "level2_eligibility",
            "https://example.invalid/eligibility.json",
            RecursionEnvelopeInputKind::Level2EligibilityReport,
            ClaimBoundary::Level2ReproducibleBenchmarkArtifact,
            EvidenceClass::DesignNote,
            digest(3),
        ),
    ];
    plan.expected_artifacts = vec![RecursionAdapterPreparationArtifact {
        artifact_id: " ".to_string(),
        artifact_uri: "~/recursion_output.json".to_string(),
        role: RecursionAdapterPreparationArtifactRole::OutputEnvelopeCandidate,
        required: true,
        notes: Vec::new(),
    }];

    let validation = validate_recursion_adapter_preparation_plan(&plan);
    let kinds: Vec<_> = validation.issues.iter().map(|issue| issue.kind).collect();
    let paths: Vec<_> = validation
        .issues
        .iter()
        .map(|issue| issue.path.as_str())
        .collect();

    assert!(!validation.valid);
    assert!(kinds.contains(&RecursionAdapterPreparationIssueKind::EmptyIdentity));
    assert!(kinds.contains(&RecursionAdapterPreparationIssueKind::InvalidArtifactRef));
    assert!(kinds.contains(&RecursionAdapterPreparationIssueKind::InvalidInput));
    assert!(paths.contains(&"source_inputs[0].input_id"));
    assert!(paths.contains(&"source_inputs[0].artifact_uri"));
    assert!(paths.contains(&"source_inputs[0].digest"));
    assert!(paths.contains(&"source_inputs[0].claim_boundary"));
    assert!(paths.contains(&"source_inputs[1].artifact_uri"));
    assert!(paths.contains(&"source_inputs[1].claim_boundary"));
    assert!(paths.contains(&"expected_artifacts[0].artifact_id"));
    assert!(paths.contains(&"expected_artifacts[0].artifact_uri"));
}

#[test]
fn recursion_manual_handoff_validation_rejects_wrapper_boundary_drift() {
    let plan = valid_preparation_plan();
    let mut bundle =
        build_recursion_adapter_manual_handoff_bundle(&plan).expect("handoff should build");
    bundle.claim_boundary = ClaimBoundary::Level1LocalReplay;
    bundle.mapping.claim_boundary = ClaimBoundary::Level1LocalReplay;

    let validation = validate_recursion_adapter_manual_handoff_bundle(&bundle);
    let paths: Vec<_> = validation
        .issues
        .iter()
        .map(|issue| issue.path.as_str())
        .collect();

    assert!(!validation.valid);
    assert!(paths.contains(&"recursion_adapter_manual_handoff.claim_boundary"));
    assert!(paths.contains(&"recursion_adapter_manual_handoff.mapping.claim_boundary"));
}

#[test]
fn recursion_json_deserializers_report_malformed_input_contexts() {
    let cases = [
        (
            "candidate",
            deserialize_recursion_envelope_candidate_json("{").expect_err("candidate should fail"),
            "deserialize_recursion_envelope_candidate_json",
        ),
        (
            "plan",
            deserialize_recursion_adapter_preparation_plan_json("{").expect_err("plan should fail"),
            "deserialize_recursion_adapter_preparation_plan_json",
        ),
        (
            "handoff",
            deserialize_recursion_adapter_manual_handoff_bundle_json("{")
                .expect_err("handoff should fail"),
            "deserialize_recursion_adapter_manual_handoff_bundle_json",
        ),
    ];

    for (label, err, context) in cases {
        let text = err.to_string();
        assert!(
            text.contains(context),
            "{label} error should expose context: {text}"
        );
    }
}

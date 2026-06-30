use zkbench_core::{
    build_default_artifact_capture_contract, deserialize_artifact_capture_contract_json,
    serialize_artifact_capture_contract_json, validate_artifact_capture_contract,
    ArtifactCaptureRequirement, CapturedArtifactMetadata, ClaimBoundary, ExpectedArtifactFormat,
    ExpectedArtifactRole,
};

#[test]
fn default_contract_includes_expected_future_artifact_roles() {
    let contract = build_default_artifact_capture_contract();
    let roles = contract
        .expected_artifacts
        .iter()
        .map(|artifact| artifact.role)
        .collect::<Vec<_>>();

    assert!(roles.contains(&ExpectedArtifactRole::InputManifest));
    assert!(roles.contains(&ExpectedArtifactRole::CandidateWorkloadManifest));
    assert!(roles.contains(&ExpectedArtifactRole::ExternalToolVersion));
    assert!(roles.contains(&ExpectedArtifactRole::RawExternalOutput));
    assert!(roles.contains(&ExpectedArtifactRole::NormalizedResultCandidate));
    assert!(roles.contains(&ExpectedArtifactRole::ProvenanceRecord));
    assert!(roles.contains(&ExpectedArtifactRole::ValidationReport));
    assert!(roles.contains(&ExpectedArtifactRole::EvidenceAppendProposal));
    assert!(contract.has_no_actual_external_artifacts());
    assert_eq!(contract.claim_boundary, ClaimBoundary::Level0DesignNote);
}

#[test]
fn default_contract_declares_required_formats_requirements_and_paths() {
    let contract = build_default_artifact_capture_contract();

    let input = contract
        .expected_artifacts
        .iter()
        .find(|artifact| artifact.role == ExpectedArtifactRole::InputManifest)
        .expect("input manifest artifact is declared");
    assert_eq!(input.format, ExpectedArtifactFormat::Json);
    assert_eq!(input.requirement, ArtifactCaptureRequirement::Required);
    assert_eq!(
        input.relative_path_hint.as_deref(),
        Some("handoff/input_manifest.json")
    );
    assert!(input
        .notes
        .iter()
        .any(|note| note.contains("Expected future")));

    let external_version = contract
        .expected_artifacts
        .iter()
        .find(|artifact| artifact.role == ExpectedArtifactRole::ExternalToolVersion)
        .expect("external tool version artifact is declared");
    assert_eq!(external_version.format, ExpectedArtifactFormat::Text);
    assert_eq!(
        external_version.relative_path_hint.as_deref(),
        Some("provenance/external_tool_version.txt")
    );

    let raw_output = contract
        .expected_artifacts
        .iter()
        .find(|artifact| artifact.role == ExpectedArtifactRole::RawExternalOutput)
        .expect("raw external output artifact is declared");
    assert_eq!(
        raw_output.format,
        ExpectedArtifactFormat::UnknownFutureFormat
    );
    assert_eq!(
        raw_output.requirement,
        ArtifactCaptureRequirement::ForbiddenInPhaseH
    );
    assert_eq!(
        raw_output.relative_path_hint.as_deref(),
        Some("artifacts/raw_external_output")
    );

    let proposal = contract
        .expected_artifacts
        .iter()
        .find(|artifact| artifact.role == ExpectedArtifactRole::EvidenceAppendProposal)
        .expect("evidence append proposal artifact is declared");
    assert_eq!(proposal.format, ExpectedArtifactFormat::Json);
    assert_eq!(
        proposal.requirement,
        ArtifactCaptureRequirement::ForbiddenInPhaseH
    );
    assert_eq!(
        proposal.relative_path_hint.as_deref(),
        Some("handoff/evidence_append_proposal.json")
    );
}

#[test]
fn contract_round_trips_through_json() {
    let contract = build_default_artifact_capture_contract();
    let json =
        serialize_artifact_capture_contract_json(&contract).expect("contract should serialize");
    let parsed =
        deserialize_artifact_capture_contract_json(&json).expect("contract should deserialize");
    let json_again =
        serialize_artifact_capture_contract_json(&parsed).expect("contract should serialize again");

    assert_eq!(contract, parsed);
    assert_eq!(json, json_again);
}

#[test]
fn contract_rejects_absolute_artifact_paths() {
    let mut contract = build_default_artifact_capture_contract();
    contract.expected_artifacts[0].relative_path_hint = Some("/tmp/raw-output.json".to_string());

    let validation = validate_artifact_capture_contract(&contract);
    assert!(!validation.valid);
    assert!(validation
        .errors
        .iter()
        .any(|issue| issue.message.contains("absolute")));
}

#[test]
fn contract_validation_reports_shape_and_expected_artifact_errors() {
    let mut contract = build_default_artifact_capture_contract();
    contract.id = " ".to_string();
    contract.claim_boundary = ClaimBoundary::Level1LocalReplay;
    contract.expected_artifacts[0].id = " ".to_string();
    contract.expected_artifacts[1].relative_path_hint = Some("../candidate.json".to_string());

    let validation = validate_artifact_capture_contract(&contract);

    assert!(!validation.valid);
    let paths = validation
        .errors
        .iter()
        .map(|issue| issue.path.as_str())
        .collect::<Vec<_>>();
    assert!(paths.contains(&"contract.id"));
    assert!(paths.contains(&"contract.claim_boundary"));
    assert!(paths.contains(&"contract.expected_artifacts[0].id"));
    assert!(paths.contains(&"contract.expected_artifacts[1].relative_path_hint"));
}

#[test]
fn contract_validation_warns_on_captured_artifacts_and_rejects_unsafe_uri() {
    let mut contract = build_default_artifact_capture_contract();
    contract.captured_artifacts.push(CapturedArtifactMetadata {
        id: "raw_output_capture".to_string(),
        role: ExpectedArtifactRole::RawExternalOutput,
        format: ExpectedArtifactFormat::UnknownFutureFormat,
        relative_uri: "../external/raw-output.json".to_string(),
        digest: None,
        reviewed: false,
        notes: vec!["fixture metadata only; not a live artifact".to_string()],
    });

    let validation = validate_artifact_capture_contract(&contract);

    assert!(!validation.valid);
    assert!(validation.errors.iter().any(|issue| {
        issue.path == "contract.captured_artifacts[0].relative_uri"
            && issue.message.contains("absolute or contains traversal")
    }));
    assert!(validation.warnings.iter().any(|issue| {
        issue.path == "contract.captured_artifacts"
            && issue
                .message
                .contains("captured external artifacts require future review")
    }));
    assert!(validation.warnings.iter().any(|issue| {
        issue.path == "contract.captured_artifacts[0].reviewed"
            && issue.message.contains("not reviewed")
    }));
}

#[test]
fn contract_distinguishes_expected_from_captured_artifacts() {
    let contract = build_default_artifact_capture_contract();
    assert!(!contract.expected_artifacts.is_empty());
    assert!(contract.captured_artifacts.is_empty());
    assert_eq!(contract.claim_boundary, ClaimBoundary::Level0DesignNote);
}

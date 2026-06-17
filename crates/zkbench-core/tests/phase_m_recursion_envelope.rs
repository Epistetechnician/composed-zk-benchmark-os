use std::fs;
use std::path::Path;

use zkbench_core::{
    compute_recursion_envelope_digest_chain_root, deserialize_recursion_envelope_candidate_json,
    serialize_recursion_envelope_candidate_json, validate_recursion_envelope_candidate,
    ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole, ClaimBoundary,
    EvidenceClass, RecursionEnvelopeCandidate, RecursionEnvelopeInputKind,
    RecursionEnvelopeInputRef, RecursionEnvelopeMetric, RecursionEnvelopeMetricKind,
    RecursionEnvelopeValidationIssueKind, RecursionEnvelopeVersion,
    RecursionVerifierAcceptanceStatus,
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

fn input(
    input_id: &str,
    kind: RecursionEnvelopeInputKind,
    claim_boundary: ClaimBoundary,
    evidence_class: EvidenceClass,
    digest_byte: u8,
) -> RecursionEnvelopeInputRef {
    RecursionEnvelopeInputRef {
        input_id: input_id.to_string(),
        artifact_uri: format!("artifacts/{input_id}.json"),
        kind,
        digest: digest(digest_byte),
        evidence_class,
        claim_boundary,
        notes: Vec::new(),
    }
}

fn candidate_with_inputs(inputs: Vec<RecursionEnvelopeInputRef>) -> RecursionEnvelopeCandidate {
    let digest_chain_root = compute_recursion_envelope_digest_chain_root(&inputs)
        .expect("digest chain root should compute");
    RecursionEnvelopeCandidate {
        envelope_id: "phase_m_envelope_candidate".to_string(),
        version: RecursionEnvelopeVersion::default(),
        inputs,
        recursion_depth: 2,
        aggregation_width: 2,
        digest_chain_root,
        verifier_acceptance_status: None,
        executable_adapter_authorized: false,
        metrics: vec![
            RecursionEnvelopeMetric {
                kind: RecursionEnvelopeMetricKind::RecursionDepth,
                value: Some(2),
                claim_boundary: ClaimBoundary::Level0DesignNote,
                notes: Vec::new(),
            },
            RecursionEnvelopeMetric {
                kind: RecursionEnvelopeMetricKind::EnvelopeInputCount,
                value: Some(2),
                claim_boundary: ClaimBoundary::Level0DesignNote,
                notes: Vec::new(),
            },
        ],
        output_claim_boundary: ClaimBoundary::Level0DesignNote,
        limitations: vec![
            "recursion proof is not semantic proof".to_string(),
            "local replay remains local replay".to_string(),
        ],
        notes: Vec::new(),
    }
}

fn valid_candidate() -> RecursionEnvelopeCandidate {
    candidate_with_inputs(vec![
        input(
            "replay_manifest",
            RecursionEnvelopeInputKind::LocalReplayManifest,
            ClaimBoundary::Level1LocalReplay,
            EvidenceClass::LocalReplay,
            1,
        ),
        input(
            "append_preview",
            RecursionEnvelopeInputKind::EvidenceAppendPreview,
            ClaimBoundary::Level0DesignNote,
            EvidenceClass::DesignNote,
            2,
        ),
    ])
}

fn issue_kinds(
    candidate: &RecursionEnvelopeCandidate,
) -> Vec<RecursionEnvelopeValidationIssueKind> {
    validate_recursion_envelope_candidate(candidate)
        .issues
        .into_iter()
        .map(|issue| issue.kind)
        .collect()
}

#[test]
fn valid_fixture_recursion_envelope_candidate_validates() {
    let candidate = deserialize_recursion_envelope_candidate_json(include_str!(
        "fixtures/phase_m_recursion_envelope_valid.json"
    ))
    .expect("valid Phase M fixture should deserialize");

    let validation = validate_recursion_envelope_candidate(&candidate);

    assert!(validation.valid, "issues: {:?}", validation.issues);
    assert_eq!(candidate, valid_candidate());
    assert_eq!(validation.claim_boundary, ClaimBoundary::Level0DesignNote);
}

#[test]
fn invalid_fixture_recursion_envelope_candidate_fails_closed() {
    let candidate = deserialize_recursion_envelope_candidate_json(include_str!(
        "fixtures/phase_m_recursion_envelope_invalid.json"
    ))
    .expect("invalid Phase M fixture should deserialize");

    let kinds = issue_kinds(&candidate);

    assert!(kinds.contains(&RecursionEnvelopeValidationIssueKind::AppendPreviewBoundary));
    assert!(kinds.contains(&RecursionEnvelopeValidationIssueKind::Level2EligibilityBoundary));
    assert!(kinds.contains(&RecursionEnvelopeValidationIssueKind::DigestChainRootMismatch));
    assert!(kinds.contains(&RecursionEnvelopeValidationIssueKind::ClaimBoundaryEscalation));
    assert!(kinds.contains(&RecursionEnvelopeValidationIssueKind::UnauthorizedVerifierStatus));
    assert!(kinds.contains(&RecursionEnvelopeValidationIssueKind::UnauthorizedExecutableMetric));
    assert!(kinds.contains(&RecursionEnvelopeValidationIssueKind::MissingLimitation));
}

#[test]
fn phase_m_files_do_not_gain_executable_adapter_hooks() {
    let crate_root = Path::new(env!("CARGO_MANIFEST_DIR"));
    let scanned_paths = [
        crate_root.join("src/recursion.rs"),
        crate_root.join("tests/phase_m_recursion_envelope.rs"),
        crate_root.join("tests/fixtures/phase_m_recursion_envelope_valid.json"),
        crate_root.join("tests/fixtures/phase_m_recursion_envelope_invalid.json"),
    ];
    let forbidden_markers = [
        concat!("std::process::", "Command"),
        concat!("Command", "::new"),
        concat!("std::net", "::"),
        concat!("Tcp", "Stream"),
        concat!("Udp", "Socket"),
        concat!("req", "west"),
        concat!("u", "req"),
        concat!("go", " run"),
        concat!("git", " clone"),
        concat!("gnark", ".Prove"),
        concat!("gnark", ".Verify"),
        concat!("prover", "_time"),
        concat!("verifier", "_time"),
        concat!("proof", "_size"),
        concat!("memory", "_usage"),
    ];

    let mut findings = Vec::new();
    for path in scanned_paths {
        let text = fs::read_to_string(&path).expect("Phase M file should be readable");
        for marker in forbidden_markers {
            if text.contains(marker) {
                findings.push(format!("{} contains {marker}", path.display()));
            }
        }
    }

    assert!(
        findings.is_empty(),
        "Phase M local contract files must remain inert: {findings:?}"
    );
}

#[test]
fn valid_inert_recursion_envelope_candidate_validates() {
    let candidate = valid_candidate();
    let validation = validate_recursion_envelope_candidate(&candidate);

    assert!(validation.valid, "issues: {:?}", validation.issues);
    assert_eq!(validation.claim_boundary, ClaimBoundary::Level0DesignNote);
}

#[test]
fn candidate_round_trips_as_json() {
    let candidate = valid_candidate();
    let json = serialize_recursion_envelope_candidate_json(&candidate)
        .expect("candidate should serialize");
    let round_trip =
        deserialize_recursion_envelope_candidate_json(&json).expect("candidate should deserialize");

    assert_eq!(round_trip, candidate);
}

#[test]
fn output_claim_boundary_cannot_exceed_weakest_input_or_phase_boundary() {
    let mut candidate = candidate_with_inputs(vec![
        input(
            "local_replay_a",
            RecursionEnvelopeInputKind::LocalReplayResult,
            ClaimBoundary::Level1LocalReplay,
            EvidenceClass::LocalReplay,
            3,
        ),
        input(
            "local_replay_b",
            RecursionEnvelopeInputKind::LocalReplayManifest,
            ClaimBoundary::Level1LocalReplay,
            EvidenceClass::LocalReplay,
            4,
        ),
    ]);
    candidate.output_claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;

    let kinds = issue_kinds(&candidate);
    assert!(kinds.contains(&RecursionEnvelopeValidationIssueKind::ClaimBoundaryEscalation));
}

#[test]
fn executable_verifier_status_and_metrics_require_future_authorization() {
    let mut candidate = valid_candidate();
    candidate.verifier_acceptance_status = Some(RecursionVerifierAcceptanceStatus::Accepted);
    candidate.metrics.push(RecursionEnvelopeMetric {
        kind: RecursionEnvelopeMetricKind::RecursionVerifierTimeMs,
        value: Some(10),
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: Vec::new(),
    });

    let kinds = issue_kinds(&candidate);
    assert!(kinds.contains(&RecursionEnvelopeValidationIssueKind::UnauthorizedVerifierStatus));
    assert!(kinds.contains(&RecursionEnvelopeValidationIssueKind::UnauthorizedExecutableMetric));
}

#[test]
fn append_preview_and_level2_eligibility_inputs_remain_level0_metadata() {
    let mut candidate = candidate_with_inputs(vec![
        input(
            "append_preview",
            RecursionEnvelopeInputKind::EvidenceAppendPreview,
            ClaimBoundary::Level1LocalReplay,
            EvidenceClass::DesignNote,
            5,
        ),
        input(
            "level2_eligibility",
            RecursionEnvelopeInputKind::Level2EligibilityReport,
            ClaimBoundary::Level2ReproducibleBenchmarkArtifact,
            EvidenceClass::DesignNote,
            6,
        ),
    ]);
    candidate.output_claim_boundary = ClaimBoundary::Level1LocalReplay;

    let kinds = issue_kinds(&candidate);
    assert!(kinds.contains(&RecursionEnvelopeValidationIssueKind::AppendPreviewBoundary));
    assert!(kinds.contains(&RecursionEnvelopeValidationIssueKind::Level2EligibilityBoundary));
}

#[test]
fn stale_digest_chain_root_is_rejected() {
    let mut candidate = valid_candidate();
    candidate.digest_chain_root = digest(9);

    let kinds = issue_kinds(&candidate);
    assert!(kinds.contains(&RecursionEnvelopeValidationIssueKind::DigestChainRootMismatch));
}

#[test]
fn limitation_must_preserve_recursion_not_semantic_proof_boundary() {
    let mut candidate = valid_candidate();
    candidate.limitations.clear();

    let kinds = issue_kinds(&candidate);
    assert!(kinds.contains(&RecursionEnvelopeValidationIssueKind::MissingLimitation));
}

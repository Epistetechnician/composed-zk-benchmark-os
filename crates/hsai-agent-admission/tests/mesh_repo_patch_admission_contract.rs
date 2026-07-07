use hsai_agent_admission::{
    evaluate_mesh_hsai_admission_request, mesh_repo_patch_admission_policy,
    mesh_repo_patch_required_nonclaims, mesh_repo_patch_supported_claims, GatewayFormalBackendKind,
    GatewayFormalBackendRunCheckerStatus, GatewayFormalEvidencePropertyKind, MeshAttestationRef,
    MeshBackendRunMetadata, MeshEvidenceGate, MeshFormalEvidenceMetadata, MeshHsaiAdmissionRequest,
    MeshHsaiAdmissionVerdict, MeshRequestedClaimWeakening, MESH_CLAIM_CANDIDATE_DIGEST_BOUND,
    MESH_CLAIM_FORMAL_EVIDENCE_METADATA_BOUND, MESH_CLAIM_PATCH_APPLIES_CLEANLY,
    MESH_COMBINED_PROOF_PACKET_SCHEMA_VERSION, MESH_HSAI_ADMISSION_REQUEST_SCHEMA_VERSION,
    MESH_REPO_PATCH_ADMISSION_CLAIM_BOUNDARY,
};
use hsai_claim_envelope::Hash;
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

const MESH_GOLDEN_ALLOW_REQUEST: &str =
    include_str!("fixtures/hsai_bridge/golden_allow_request.json");
const MESH_GOLDEN_ALLOW_DECISION: &str =
    include_str!("fixtures/hsai_bridge/golden_allow_decision.json");
const MESH_GOLDEN_DENY_REQUEST: &str =
    include_str!("fixtures/hsai_bridge/golden_deny_request.json");
const MESH_GOLDEN_DENY_DECISION: &str =
    include_str!("fixtures/hsai_bridge/golden_deny_decision.json");

fn hash(byte: u8) -> Hash {
    Hash([byte; 32])
}

fn gate(gate_id: &str, passed: bool, evidence_digest: Hash) -> MeshEvidenceGate {
    MeshEvidenceGate {
        gate_id: gate_id.to_owned(),
        passed,
        evidence_digest,
        reason_codes: Vec::new(),
    }
}

fn valid_request() -> MeshHsaiAdmissionRequest {
    MeshHsaiAdmissionRequest {
        schema_version: MESH_HSAI_ADMISSION_REQUEST_SCHEMA_VERSION.to_owned(),
        mesh_run_id: "mesh-run-1".to_owned(),
        mesh_action_id: "mesh-action-1".to_owned(),
        mesh_policy_id: "mesh-policy-current".to_owned(),
        candidate_digest: hash(1),
        evidence_packet_schema_version: MESH_COMBINED_PROOF_PACKET_SCHEMA_VERSION.to_owned(),
        evidence_packet_digest: hash(2),
        attestation_refs: BTreeSet::from([MeshAttestationRef {
            ref_id: "attestation-ref-1".to_owned(),
            digest: hash(3),
            claim_binding: "repo_patch.attestation.bound".to_owned(),
        }]),
        requested_claims: mesh_repo_patch_supported_claims(),
        explicit_nonclaims: mesh_repo_patch_required_nonclaims(),
        claim_weakenings: Vec::new(),
        candidate_evidence_gate: gate("candidate_evidence_gate", true, hash(4)),
        accepted_evidence_gate: gate("accepted_evidence_gate", true, hash(5)),
        formal_evidence_metadata: Some(MeshFormalEvidenceMetadata {
            evidence_id: "formal-evidence-1".to_owned(),
            evidence_digest: hash(6),
            backend_kind: GatewayFormalBackendKind::Smt,
            property_kind:
                GatewayFormalEvidencePropertyKind::AttestationChallengeBindingDeterministicInputSensitive,
            local_regression_only: true,
            claim_boundary: "local formal metadata only".to_owned(),
        }),
        backend_run_metadata: Some(MeshBackendRunMetadata {
            run_id: "backend-run-1".to_owned(),
            backend_kind: GatewayFormalBackendKind::Smt,
            run_digest: hash(7),
            transcript_digest: hash(8),
            checker_status: GatewayFormalBackendRunCheckerStatus::Checked,
            creates_accepted_evidence: false,
            creates_level2_evidence: false,
            grants_authority: false,
            claim_boundary: "backend run metadata only".to_owned(),
        }),
    }
}

fn assert_denies_with_reason(request: &MeshHsaiAdmissionRequest, expected_reason: &str) {
    let decision = evaluate_mesh_hsai_admission_request(
        request,
        &mesh_repo_patch_admission_policy("mesh-policy-current"),
    );

    assert_eq!(decision.verdict, MeshHsaiAdmissionVerdict::Deny);
    assert!(decision.accepted_claims.is_empty());
    assert!(
        decision.reason_codes.contains(&expected_reason.to_owned()),
        "missing expected reason code {expected_reason}; got {:?}",
        decision.reason_codes
    );
}

fn json_fixture(text: &str) -> Value {
    serde_json::from_str(text).expect("golden fixture parses")
}

fn fixture_string<'a>(value: &'a Value, key: &str) -> &'a str {
    value
        .get(key)
        .and_then(Value::as_str)
        .unwrap_or_else(|| panic!("fixture string key exists: {key}"))
}

fn fixture_string_set(value: &Value, key: &str) -> BTreeSet<String> {
    value
        .get(key)
        .and_then(Value::as_array)
        .unwrap_or_else(|| panic!("fixture string array key exists: {key}"))
        .iter()
        .map(|entry| {
            entry
                .as_str()
                .unwrap_or_else(|| panic!("fixture string array element exists: {key}"))
                .to_owned()
        })
        .collect()
}

fn fixture_nonclaims(value: &Value) -> BTreeSet<hsai_agent_admission::NonClaimLabel> {
    fixture_string_set(value, "explicit_nonclaims")
        .into_iter()
        .map(hsai_agent_admission::NonClaimLabel)
        .collect()
}

fn fixture_hash(value: &Value, key: &str) -> Hash {
    hash_from_sha256_uri(fixture_string(value, key))
}

fn hash_from_sha256_uri(value: &str) -> Hash {
    let hex = value
        .strip_prefix("sha256:")
        .expect("fixture digest has sha256 prefix");
    assert_eq!(hex.len(), 64, "fixture digest is 32 bytes hex");
    let mut out = [0u8; 32];
    for (idx, chunk) in hex.as_bytes().chunks_exact(2).enumerate() {
        out[idx] = (hex_nibble(chunk[0]) << 4) | hex_nibble(chunk[1]);
    }
    Hash(out)
}

fn hex_nibble(byte: u8) -> u8 {
    match byte {
        b'0'..=b'9' => byte - b'0',
        b'a'..=b'f' => 10 + byte - b'a',
        b'A'..=b'F' => 10 + byte - b'A',
        _ => panic!("invalid fixture hex nibble"),
    }
}

fn mesh_canonical_digest(value: &Value) -> String {
    let mut hasher = Sha256::new();
    hasher.update(mesh_canonical_json(value).as_bytes());
    let digest = hasher.finalize();
    let mut hex = String::with_capacity(64);
    for byte in digest {
        hex.push_str(&format!("{byte:02x}"));
    }
    format!("sha256:{hex}")
}

fn mesh_decision_digest(value: &Value) -> String {
    let mut without_digest = value.clone();
    without_digest
        .as_object_mut()
        .expect("decision fixture is object")
        .remove("decision_digest");
    mesh_canonical_digest(&without_digest)
}

fn mesh_canonical_json(value: &Value) -> String {
    match value {
        Value::Null => "null".to_owned(),
        Value::Bool(value) => value.to_string(),
        Value::Number(value) => value.to_string(),
        Value::String(value) => serde_json::to_string(value).expect("string serializes"),
        Value::Array(values) => {
            let body = values
                .iter()
                .map(mesh_canonical_json)
                .collect::<Vec<_>>()
                .join(",");
            format!("[{body}]")
        }
        Value::Object(map) => {
            let mut entries = map.iter().collect::<Vec<_>>();
            entries.sort_by(|(left, _), (right, _)| left.cmp(right));
            let body = entries
                .into_iter()
                .map(|(key, value)| {
                    format!(
                        "{}:{}",
                        serde_json::to_string(key).expect("key serializes"),
                        mesh_canonical_json(value)
                    )
                })
                .collect::<Vec<_>>()
                .join(",");
            format!("{{{body}}}")
        }
    }
}

fn hsai_request_from_mesh_fixture(request: &Value, decision: &Value) -> MeshHsaiAdmissionRequest {
    let formal = decision
        .get("formal_evidence_metadata")
        .expect("decision formal metadata exists");
    let metadata_digest = fixture_hash(formal, "metadata_digest");
    MeshHsaiAdmissionRequest {
        schema_version: fixture_string(request, "schema_version").to_owned(),
        mesh_run_id: fixture_string(request, "mesh_run_id").to_owned(),
        mesh_action_id: fixture_string(request, "mesh_action_id").to_owned(),
        mesh_policy_id: fixture_string(request, "mesh_policy_id").to_owned(),
        candidate_digest: fixture_hash(request, "candidate_payload_digest"),
        evidence_packet_schema_version: MESH_COMBINED_PROOF_PACKET_SCHEMA_VERSION.to_owned(),
        evidence_packet_digest: fixture_hash(request, "evidence_packet_digest"),
        attestation_refs: request
            .get("attestation_refs")
            .and_then(Value::as_array)
            .expect("attestation refs exist")
            .iter()
            .map(|entry| MeshAttestationRef {
                ref_id: fixture_string(entry, "kind").to_owned(),
                digest: fixture_hash(entry, "digest"),
                claim_binding: fixture_string(entry, "kind").to_owned(),
            })
            .collect(),
        requested_claims: fixture_string_set(request, "requested_claims"),
        explicit_nonclaims: fixture_nonclaims(request),
        claim_weakenings: Vec::new(),
        candidate_evidence_gate: gate(
            "candidate_evidence_gate",
            true,
            fixture_hash(request, "evidence_packet_digest"),
        ),
        accepted_evidence_gate: gate(
            "accepted_evidence_gate",
            true,
            fixture_hash(request, "evidence_packet_digest"),
        ),
        formal_evidence_metadata: Some(MeshFormalEvidenceMetadata {
            evidence_id: fixture_string(formal, "backend").to_owned(),
            evidence_digest: metadata_digest,
            backend_kind: GatewayFormalBackendKind::LocalRustMetadataOnly,
            property_kind:
                GatewayFormalEvidencePropertyKind::AttestationChallengeBindingDeterministicInputSensitive,
            local_regression_only: true,
            claim_boundary: fixture_string(formal, "nonclaim").to_owned(),
        }),
        backend_run_metadata: Some(MeshBackendRunMetadata {
            run_id: fixture_string(formal, "backend_run_id").to_owned(),
            backend_kind: GatewayFormalBackendKind::LocalRustMetadataOnly,
            run_digest: metadata_digest,
            transcript_digest: metadata_digest,
            checker_status: GatewayFormalBackendRunCheckerStatus::NotRun,
            creates_accepted_evidence: false,
            creates_level2_evidence: false,
            grants_authority: false,
            claim_boundary: fixture_string(formal, "nonclaim").to_owned(),
        }),
    }
}

fn fixture_decision_claims(decision: &Value, key: &str) -> BTreeSet<String> {
    fixture_string_set(decision, key)
}

#[test]
fn valid_repo_patch_admission_allows_supported_bounded_claims() {
    let request = valid_request();
    let policy = mesh_repo_patch_admission_policy("mesh-policy-current");
    let decision = evaluate_mesh_hsai_admission_request(&request, &policy);

    assert_eq!(decision.verdict, MeshHsaiAdmissionVerdict::Allow);
    assert_eq!(decision.reason_codes, Vec::<String>::new());
    assert_eq!(decision.accepted_claims, request.requested_claims);
    assert!(decision.rejected_claims.is_empty());
    assert!(decision.weakened_claims.is_empty());
    assert_eq!(decision.enforced_nonclaims, policy.required_nonclaims);
    assert_eq!(
        decision.formal_evidence_metadata,
        request.formal_evidence_metadata
    );
    assert_eq!(decision.backend_run_metadata, request.backend_run_metadata);
    assert_eq!(
        decision.claim_boundary,
        MESH_REPO_PATCH_ADMISSION_CLAIM_BOUNDARY
    );
    assert!(!decision.grants_authority);
    assert!(!decision.production_readiness_claimed);
}

#[test]
fn mesh_golden_allow_fixture_matches_hsai_decision_semantics() {
    let request_fixture = json_fixture(MESH_GOLDEN_ALLOW_REQUEST);
    let decision_fixture = json_fixture(MESH_GOLDEN_ALLOW_DECISION);
    let request = hsai_request_from_mesh_fixture(&request_fixture, &decision_fixture);
    let policy =
        mesh_repo_patch_admission_policy(fixture_string(&request_fixture, "mesh_policy_id"));
    let decision = evaluate_mesh_hsai_admission_request(&request, &policy);

    assert_eq!(
        mesh_canonical_digest(&request_fixture),
        fixture_string(&decision_fixture, "request_digest")
    );
    assert_eq!(
        mesh_decision_digest(&decision_fixture),
        fixture_string(&decision_fixture, "decision_digest")
    );
    assert_eq!(decision.verdict, MeshHsaiAdmissionVerdict::Allow);
    assert_eq!(decision.reason_codes, Vec::<String>::new());
    assert_eq!(
        decision.accepted_claims,
        fixture_decision_claims(&decision_fixture, "accepted_claims")
    );
    assert_eq!(
        decision.enforced_nonclaims,
        fixture_decision_claims(&decision_fixture, "enforced_nonclaims")
            .into_iter()
            .map(hsai_agent_admission::NonClaimLabel)
            .collect()
    );
    assert_eq!(
        decision.candidate_digest,
        fixture_hash(&decision_fixture, "candidate_digest")
    );
    assert_eq!(
        decision.request_digest,
        hsai_request_from_mesh_fixture(&request_fixture, &decision_fixture).digest()
    );

    let mut changed_request = request.clone();
    changed_request.candidate_digest = hash(9);
    let changed_decision = evaluate_mesh_hsai_admission_request(&changed_request, &policy);
    assert_ne!(decision.digest(), changed_decision.digest());
    assert_ne!(decision.request_digest, changed_decision.request_digest);
    assert_eq!(changed_decision.candidate_digest, hash(9));
}

#[test]
fn mesh_golden_deny_fixture_preserves_missing_explicit_nonclaims() {
    let request_fixture = json_fixture(MESH_GOLDEN_DENY_REQUEST);
    let decision_fixture = json_fixture(MESH_GOLDEN_DENY_DECISION);
    let request = hsai_request_from_mesh_fixture(&request_fixture, &decision_fixture);
    let policy =
        mesh_repo_patch_admission_policy(fixture_string(&request_fixture, "mesh_policy_id"));
    let decision = evaluate_mesh_hsai_admission_request(&request, &policy);

    assert_eq!(
        mesh_canonical_digest(&request_fixture),
        fixture_string(&decision_fixture, "request_digest")
    );
    assert_eq!(
        mesh_decision_digest(&decision_fixture),
        fixture_string(&decision_fixture, "decision_digest")
    );
    assert_eq!(decision.verdict, MeshHsaiAdmissionVerdict::Deny);
    assert_eq!(decision.reason_codes, vec!["missing_explicit_nonclaims"]);
    assert_eq!(
        decision.reason_codes,
        fixture_string_set(&decision_fixture, "reason_codes")
            .into_iter()
            .collect::<Vec<_>>()
    );
    assert!(decision.accepted_claims.is_empty());
    assert!(decision.enforced_nonclaims.is_empty());
    assert_eq!(
        decision.candidate_digest,
        fixture_hash(&decision_fixture, "candidate_digest")
    );
}

#[test]
fn missing_candidate_digest_denies() {
    let mut request = valid_request();
    request.candidate_digest = Hash([0; 32]);

    let decision = evaluate_mesh_hsai_admission_request(
        &request,
        &mesh_repo_patch_admission_policy("mesh-policy-current"),
    );

    assert_eq!(decision.verdict, MeshHsaiAdmissionVerdict::Deny);
    assert!(decision
        .reason_codes
        .contains(&"missing_candidate_digest".to_owned()));
}

#[test]
fn missing_evidence_packet_digest_denies() {
    let mut request = valid_request();
    request.evidence_packet_digest = Hash([0; 32]);

    let decision = evaluate_mesh_hsai_admission_request(
        &request,
        &mesh_repo_patch_admission_policy("mesh-policy-current"),
    );

    assert_eq!(decision.verdict, MeshHsaiAdmissionVerdict::Deny);
    assert!(decision
        .reason_codes
        .contains(&"missing_evidence_packet_digest".to_owned()));
}

#[test]
fn missing_nonclaims_denies() {
    let mut request = valid_request();
    request.explicit_nonclaims.clear();

    let decision = evaluate_mesh_hsai_admission_request(
        &request,
        &mesh_repo_patch_admission_policy("mesh-policy-current"),
    );

    assert_eq!(decision.verdict, MeshHsaiAdmissionVerdict::Deny);
    assert!(decision
        .reason_codes
        .contains(&"missing_explicit_nonclaims".to_owned()));
    assert!(!decision
        .reason_codes
        .contains(&"missing_required_nonclaim".to_owned()));
    assert!(decision.accepted_claims.is_empty());
    assert!(decision.enforced_nonclaims.is_empty());
}

#[test]
fn unsupported_schema_version_denies() {
    let mut request = valid_request();
    request.schema_version = "mesh.hsai_admission_request.v0".to_owned();

    let decision = evaluate_mesh_hsai_admission_request(
        &request,
        &mesh_repo_patch_admission_policy("mesh-policy-current"),
    );

    assert_eq!(decision.verdict, MeshHsaiAdmissionVerdict::Deny);
    assert!(decision
        .reason_codes
        .contains(&"unsupported_schema_version".to_owned()));
}

#[test]
fn unsupported_claim_is_rejected() {
    let mut request = valid_request();
    request
        .requested_claims
        .insert("repo_patch.unimplemented_runtime_action".to_owned());

    let decision = evaluate_mesh_hsai_admission_request(
        &request,
        &mesh_repo_patch_admission_policy("mesh-policy-current"),
    );

    assert_eq!(decision.verdict, MeshHsaiAdmissionVerdict::Deny);
    assert!(decision
        .reason_codes
        .contains(&"unsupported_claim".to_owned()));
    assert!(decision.rejected_claims.iter().any(|claim| {
        claim.claim == "repo_patch.unimplemented_runtime_action"
            && claim.reason_code == "unsupported_claim"
    }));
}

#[test]
fn overbroad_claim_is_rejected() {
    let mut request = valid_request();
    request
        .requested_claims
        .insert("production_readiness".to_owned());

    let decision = evaluate_mesh_hsai_admission_request(
        &request,
        &mesh_repo_patch_admission_policy("mesh-policy-current"),
    );

    assert_eq!(decision.verdict, MeshHsaiAdmissionVerdict::Deny);
    assert!(decision
        .reason_codes
        .contains(&"overbroad_claim_rejected".to_owned()));
    assert!(decision.rejected_claims.iter().any(|claim| {
        claim.claim == "production_readiness" && claim.reason_code == "overbroad_claim_rejected"
    }));
}

#[test]
fn weakened_claim_requires_explicit_reason_code() {
    let mut request = valid_request();
    request.requested_claims = BTreeSet::from(["production_readiness".to_owned()]);
    request.claim_weakenings = vec![MeshRequestedClaimWeakening {
        requested_claim: "production_readiness".to_owned(),
        weakened_claim: MESH_CLAIM_CANDIDATE_DIGEST_BOUND.to_owned(),
        reason_code: None,
    }];

    let decision = evaluate_mesh_hsai_admission_request(
        &request,
        &mesh_repo_patch_admission_policy("mesh-policy-current"),
    );

    assert_eq!(decision.verdict, MeshHsaiAdmissionVerdict::Deny);
    assert!(decision
        .reason_codes
        .contains(&"weakened_claim_reason_code_required".to_owned()));
}

#[test]
fn stale_policy_and_malformed_mesh_ids_deny() {
    let mut stale = valid_request();
    stale.mesh_policy_id = "mesh-policy-stale".to_owned();
    assert_denies_with_reason(&stale, "stale_policy_id");

    let mut malformed = valid_request();
    malformed.mesh_run_id = "mesh/run".to_owned();
    malformed.mesh_action_id = "mesh..action".to_owned();
    malformed.mesh_policy_id = " mesh-policy-current".to_owned();
    let decision = evaluate_mesh_hsai_admission_request(
        &malformed,
        &mesh_repo_patch_admission_policy("mesh-policy-current"),
    );

    assert_eq!(decision.verdict, MeshHsaiAdmissionVerdict::Deny);
    assert!(decision.accepted_claims.is_empty());
    for reason in [
        "malformed_mesh_run_id",
        "malformed_mesh_action_id",
        "malformed_mesh_policy_id",
        "stale_policy_id",
    ] {
        assert!(decision.reason_codes.contains(&reason.to_owned()));
    }
}

#[test]
fn attestation_and_gate_shape_fail_closed() {
    let mut missing_attestation = valid_request();
    missing_attestation.attestation_refs.clear();
    assert_denies_with_reason(&missing_attestation, "missing_attestation_refs");

    let mut malformed_attestation = valid_request();
    malformed_attestation.attestation_refs = BTreeSet::from([MeshAttestationRef {
        ref_id: "attestation/ref".to_owned(),
        digest: Hash([0; 32]),
        claim_binding: " repo_patch.attestation.bound".to_owned(),
    }]);
    let malformed_decision = evaluate_mesh_hsai_admission_request(
        &malformed_attestation,
        &mesh_repo_patch_admission_policy("mesh-policy-current"),
    );
    assert_eq!(malformed_decision.verdict, MeshHsaiAdmissionVerdict::Deny);
    for reason in [
        "malformed_attestation_ref",
        "missing_attestation_ref_digest",
        "malformed_attestation_claim_binding",
    ] {
        assert!(malformed_decision.reason_codes.contains(&reason.to_owned()));
    }

    let mut malformed_gate = valid_request();
    malformed_gate.accepted_evidence_gate = MeshEvidenceGate {
        gate_id: "wrong_gate".to_owned(),
        passed: false,
        evidence_digest: Hash([0; 32]),
        reason_codes: Vec::new(),
    };
    let gate_decision = evaluate_mesh_hsai_admission_request(
        &malformed_gate,
        &mesh_repo_patch_admission_policy("mesh-policy-current"),
    );
    assert_eq!(gate_decision.verdict, MeshHsaiAdmissionVerdict::Deny);
    for reason in [
        "malformed_evidence_gate",
        "missing_accepted_evidence_digest",
        "accepted_evidence_gate_failed",
        "evidence_gate_failure_reason_missing",
    ] {
        assert!(gate_decision.reason_codes.contains(&reason.to_owned()));
    }
}

#[test]
fn weakened_claim_shape_and_evidence_fail_closed() {
    let mut unrequested = valid_request();
    unrequested.claim_weakenings = vec![MeshRequestedClaimWeakening {
        requested_claim: "production_readiness".to_owned(),
        weakened_claim: "repo_patch.unsupported_weakened".to_owned(),
        reason_code: Some("bounded-substitute".to_owned()),
    }];
    let unrequested_decision = evaluate_mesh_hsai_admission_request(
        &unrequested,
        &mesh_repo_patch_admission_policy("mesh-policy-current"),
    );
    assert_eq!(unrequested_decision.verdict, MeshHsaiAdmissionVerdict::Deny);
    assert!(unrequested_decision
        .reason_codes
        .contains(&"weakened_claim_not_requested".to_owned()));
    assert!(unrequested_decision
        .reason_codes
        .contains(&"unsupported_weakened_claim".to_owned()));

    let mut not_weakened = valid_request();
    not_weakened.claim_weakenings = vec![MeshRequestedClaimWeakening {
        requested_claim: MESH_CLAIM_PATCH_APPLIES_CLEANLY.to_owned(),
        weakened_claim: MESH_CLAIM_PATCH_APPLIES_CLEANLY.to_owned(),
        reason_code: Some("same-claim".to_owned()),
    }];
    assert_denies_with_reason(&not_weakened, "weakened_claim_not_weakened");

    let mut inadequate = valid_request();
    inadequate.requested_claims = BTreeSet::from(["production_readiness".to_owned()]);
    inadequate.formal_evidence_metadata = None;
    inadequate.backend_run_metadata = None;
    inadequate.claim_weakenings = vec![MeshRequestedClaimWeakening {
        requested_claim: "production_readiness".to_owned(),
        weakened_claim: MESH_CLAIM_FORMAL_EVIDENCE_METADATA_BOUND.to_owned(),
        reason_code: Some("formal-metadata-substitute".to_owned()),
    }];
    assert_denies_with_reason(&inadequate, "inadequate_evidence_for_weakened_claim");
}

#[test]
fn backend_metadata_shape_and_forbidden_flags_deny() {
    let mut forbidden = valid_request();
    let backend = forbidden
        .backend_run_metadata
        .as_mut()
        .expect("valid request has backend metadata");
    backend.creates_accepted_evidence = true;
    backend.creates_level2_evidence = true;
    backend.grants_authority = true;
    let forbidden_decision = evaluate_mesh_hsai_admission_request(
        &forbidden,
        &mesh_repo_patch_admission_policy("mesh-policy-current"),
    );
    assert_eq!(forbidden_decision.verdict, MeshHsaiAdmissionVerdict::Deny);
    for reason in [
        "backend_run_creates_accepted_evidence",
        "backend_run_creates_level2_evidence",
        "backend_run_grants_authority",
        "formal_evidence_metadata_inadequate",
    ] {
        assert!(forbidden_decision.reason_codes.contains(&reason.to_owned()));
    }

    let mut malformed = valid_request();
    let backend = malformed
        .backend_run_metadata
        .as_mut()
        .expect("valid request has backend metadata");
    backend.run_id = "backend/run".to_owned();
    backend.backend_kind = GatewayFormalBackendKind::RustToLean;
    backend.run_digest = Hash([0; 32]);
    backend.transcript_digest = Hash([0; 32]);
    backend.claim_boundary.clear();
    let malformed_decision = evaluate_mesh_hsai_admission_request(
        &malformed,
        &mesh_repo_patch_admission_policy("mesh-policy-current"),
    );
    assert_eq!(malformed_decision.verdict, MeshHsaiAdmissionVerdict::Deny);
    for reason in [
        "malformed_backend_run_id",
        "backend_kind_mismatch",
        "missing_backend_run_digest",
        "missing_backend_transcript_digest",
        "missing_backend_run_claim_boundary",
        "formal_evidence_metadata_inadequate",
    ] {
        assert!(malformed_decision.reason_codes.contains(&reason.to_owned()));
    }

    let mut orphan_backend = valid_request();
    orphan_backend.formal_evidence_metadata = None;
    assert_denies_with_reason(
        &orphan_backend,
        "backend_run_metadata_without_formal_evidence",
    );
}

#[test]
fn decision_digest_binds_request_digest_and_candidate_digest() {
    let request = valid_request();
    let policy = mesh_repo_patch_admission_policy("mesh-policy-current");
    let decision = evaluate_mesh_hsai_admission_request(&request, &policy);
    let decision_digest = decision.digest();

    let mut changed_request = request.clone();
    changed_request.candidate_digest = hash(9);
    let changed_decision = evaluate_mesh_hsai_admission_request(&changed_request, &policy);

    assert_eq!(decision.request_digest, request.digest());
    assert_eq!(decision.candidate_digest, request.candidate_digest);
    assert_eq!(changed_decision.request_digest, changed_request.digest());
    assert_eq!(
        changed_decision.candidate_digest,
        changed_request.candidate_digest
    );
    assert_ne!(decision_digest, changed_decision.digest());
}

#[test]
fn backend_run_metadata_is_required_for_formal_evidence() {
    let mut request = valid_request();
    request.backend_run_metadata = None;

    let decision = evaluate_mesh_hsai_admission_request(
        &request,
        &mesh_repo_patch_admission_policy("mesh-policy-current"),
    );

    assert_eq!(decision.verdict, MeshHsaiAdmissionVerdict::Deny);
    assert!(decision
        .reason_codes
        .contains(&"backend_run_metadata_required_for_formal_evidence".to_owned()));
    assert!(decision
        .reason_codes
        .contains(&"formal_evidence_metadata_inadequate".to_owned()));
    assert!(!decision
        .accepted_claims
        .contains(MESH_CLAIM_FORMAL_EVIDENCE_METADATA_BOUND));
}

#[test]
fn denial_preserves_reason_codes() {
    let mut request = valid_request();
    request.candidate_evidence_gate = MeshEvidenceGate {
        gate_id: "candidate_evidence_gate".to_owned(),
        passed: false,
        evidence_digest: hash(4),
        reason_codes: vec!["candidate_gate.missing_review".to_owned()],
    };

    let decision = evaluate_mesh_hsai_admission_request(
        &request,
        &mesh_repo_patch_admission_policy("mesh-policy-current"),
    );

    assert_eq!(decision.verdict, MeshHsaiAdmissionVerdict::Deny);
    assert!(decision
        .reason_codes
        .contains(&"candidate_evidence_gate_failed".to_owned()));
    assert!(decision
        .reason_codes
        .contains(&"candidate_gate.missing_review".to_owned()));
}

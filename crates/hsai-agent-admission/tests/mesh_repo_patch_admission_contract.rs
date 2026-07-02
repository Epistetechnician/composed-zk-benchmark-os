use hsai_agent_admission::{
    evaluate_mesh_hsai_admission_request, mesh_repo_patch_admission_policy,
    mesh_repo_patch_required_nonclaims, mesh_repo_patch_supported_claims, GatewayFormalBackendKind,
    GatewayFormalBackendRunCheckerStatus, GatewayFormalEvidencePropertyKind, MeshAttestationRef,
    MeshBackendRunMetadata, MeshEvidenceGate, MeshFormalEvidenceMetadata, MeshHsaiAdmissionRequest,
    MeshHsaiAdmissionVerdict, MeshRequestedClaimWeakening, MESH_CLAIM_CANDIDATE_DIGEST_BOUND,
    MESH_CLAIM_FORMAL_EVIDENCE_METADATA_BOUND, MESH_COMBINED_PROOF_PACKET_SCHEMA_VERSION,
    MESH_HSAI_ADMISSION_REQUEST_SCHEMA_VERSION, MESH_REPO_PATCH_ADMISSION_CLAIM_BOUNDARY,
};
use hsai_claim_envelope::Hash;
use std::collections::BTreeSet;

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
        .contains(&"missing_nonclaims".to_owned()));
    assert!(decision
        .reason_codes
        .contains(&"missing_required_nonclaim".to_owned()));
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

use serde_json::json;
use zkbench_core::{
    external_runner::{
        compute_fresh_actor_custody_packet_digest,
        compute_fresh_actor_custody_replay_manifest_digest, evaluate_astral_execution_eligibility,
        AstralActorReadinessDeclaration, AstralExecutionEligibilityDecision,
        AstralExecutionEligibilityRequest, AstralInstrumentReadinessDeclaration,
        AstralReviewDisposition, FreshActorCustodyHandoff, FreshActorCustodyPacket,
        FreshActorCustodyReplayManifest, ASTRAL_EXECUTION_ELIGIBILITY_GATE_STATE_SLICE,
        ASTRAL_FRESH_ACTOR_CUSTODY_HANDOFF_STATE_SLICE,
        ASTRAL_FRESH_ACTOR_CUSTODY_PACKET_SCHEMA_VERSION,
    },
    ArtifactDigest, ArtifactDigestAlgorithm, ClaimBoundary,
};

fn digest(hex_digit: char) -> ArtifactDigest {
    ArtifactDigest {
        algorithm: ArtifactDigestAlgorithm::Sha256,
        hex_digest: hex_digit.to_string().repeat(64),
        byte_len: 1,
        kind: None,
        role: None,
    }
}

fn packet() -> FreshActorCustodyPacket {
    let mut packet = FreshActorCustodyPacket {
        schema_version: ASTRAL_FRESH_ACTOR_CUSTODY_PACKET_SCHEMA_VERSION.to_string(),
        packet_id: "v37-synthetic-packet-1".to_string(),
        nonce: "1".repeat(64),
        predecessor_packet_digest: None,
        handoff: FreshActorCustodyHandoff {
            id: "v34-synthetic-handoff-001".to_string(),
            state_slice: ASTRAL_FRESH_ACTOR_CUSTODY_HANDOFF_STATE_SLICE.to_string(),
            actor_id: "fresh-actor-synthetic-001".to_string(),
            actor_digest: digest('a'),
            source_archive_digest: digest('b'),
            runtime_digest: digest('c'),
            launcher_digest: digest('d'),
            launcher_argv_digest: digest('e'),
            split_manifest_digest: digest('f'),
            validator_id: "v34-validator-synthetic-001".to_string(),
            artifact_root: digest('0'),
            claim_boundary: ClaimBoundary::Level0DesignNote,
            custody_complete: true,
            assessment_opened: false,
            forbidden_materials: Vec::new(),
        },
        packet_digest: None,
    };
    packet.packet_digest =
        Some(compute_fresh_actor_custody_packet_digest(&packet).expect("packet hashes"));
    packet
}

fn manifest() -> FreshActorCustodyReplayManifest {
    let mut manifest = FreshActorCustodyReplayManifest::new().expect("manifest builds");
    manifest.ingest(packet()).expect("packet ingests");
    manifest
}

fn eligible_request(
    manifest: &FreshActorCustodyReplayManifest,
) -> AstralExecutionEligibilityRequest {
    AstralExecutionEligibilityRequest {
        request_id: "v37-synthetic-request-1".to_string(),
        state_slice: ASTRAL_EXECUTION_ELIGIBILITY_GATE_STATE_SLICE.to_string(),
        replay_manifest_digest: compute_fresh_actor_custody_replay_manifest_digest(manifest)
            .expect("manifest hashes")
            .hex_digest,
        actor_readiness: AstralActorReadinessDeclaration::DeclaredFreshInstrumentedActor,
        instrument_readiness:
            AstralInstrumentReadinessDeclaration::DeclaredPerLayerInterventionSurface,
        review_disposition: AstralReviewDisposition::IndependentReviewRecorded,
        reviewer_id: "synthetic-independent-reviewer".to_string(),
        requested_claim_boundary: ClaimBoundary::Level0DesignNote,
        nonclaims_acknowledged: true,
        assessment_opened: false,
        external_execution_disabled: true,
    }
}

#[test]
fn complete_synthetic_request_is_only_eligible_for_separate_human_authorization() {
    let manifest = manifest();
    let evaluation = evaluate_astral_execution_eligibility(&eligible_request(&manifest), &manifest);

    assert_eq!(
        evaluation.decision,
        AstralExecutionEligibilityDecision::EligibleForSeparateHumanAuthorization
    );
    assert!(evaluation.issues.is_empty());
    assert_eq!(evaluation.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert!(!evaluation.assessment_opened);
}

#[test]
fn gate_denies_missing_custody_instrument_review_and_nonclaim_controls() {
    let manifest = manifest();
    let mut request = eligible_request(&manifest);
    request.state_slice = "wrong-state-slice".to_string();
    request.replay_manifest_digest = "wrong-digest".to_string();
    request.actor_readiness = AstralActorReadinessDeclaration::NoFreshActor;
    request.instrument_readiness = AstralInstrumentReadinessDeclaration::FinalEmbeddingOnly;
    request.review_disposition = AstralReviewDisposition::Pending;
    request.reviewer_id.clear();
    request.requested_claim_boundary = ClaimBoundary::Level1LocalReplay;
    request.nonclaims_acknowledged = false;
    request.assessment_opened = true;
    request.external_execution_disabled = false;

    let evaluation = evaluate_astral_execution_eligibility(&request, &manifest);
    let paths: Vec<&str> = evaluation
        .issues
        .iter()
        .map(|issue| issue.path.as_str())
        .collect();

    assert_eq!(
        evaluation.decision,
        AstralExecutionEligibilityDecision::Denied
    );
    for expected in [
        "state_slice",
        "replay_manifest_digest",
        "actor_readiness",
        "instrument_readiness",
        "review_disposition",
        "reviewer_id",
        "requested_claim_boundary",
        "nonclaims_acknowledged",
        "assessment_opened",
        "external_execution_disabled",
    ] {
        assert!(paths.contains(&expected), "missing issue for {expected}");
    }
}

#[test]
fn gate_denies_empty_manifest_and_unknown_request_fields() {
    let manifest = FreshActorCustodyReplayManifest::new().expect("manifest builds");
    let evaluation = evaluate_astral_execution_eligibility(&eligible_request(&manifest), &manifest);
    assert_eq!(
        evaluation.decision,
        AstralExecutionEligibilityDecision::Denied
    );
    assert!(evaluation
        .issues
        .iter()
        .any(|issue| issue.path == "replay_manifest.entries"));

    let mut request =
        serde_json::to_value(eligible_request(&manifest)).expect("request serializes");
    request["raw_trace"] = json!("synthetic sentinel");
    let parsed: Result<AstralExecutionEligibilityRequest, _> = serde_json::from_value(request);
    assert!(parsed.is_err());
}

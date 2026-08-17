use serde_json::json;
use zkbench_core::{
    external_runner::{
        validate_fresh_actor_custody_handoff, ForbiddenCustodyMaterial, FreshActorCustodyHandoff,
        ASTRAL_FRESH_ACTOR_CUSTODY_HANDOFF_STATE_SLICE,
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

fn valid_handoff() -> FreshActorCustodyHandoff {
    FreshActorCustodyHandoff {
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
    }
}

#[test]
fn valid_handoff_is_accepted_as_design_only() {
    let validation = validate_fresh_actor_custody_handoff(&valid_handoff());

    assert!(validation.valid);
    assert!(validation.issues.is_empty());
}

#[test]
fn custody_gate_rejects_reserved_incomplete_or_opened_handoffs() {
    let mut handoff = valid_handoff();
    handoff.actor_id = "V25".to_string();
    handoff.custody_complete = false;
    handoff.assessment_opened = true;
    handoff.claim_boundary = ClaimBoundary::Level1LocalReplay;
    handoff.forbidden_materials = vec![ForbiddenCustodyMaterial::RawTrace];

    let validation = validate_fresh_actor_custody_handoff(&handoff);
    let paths: Vec<&str> = validation
        .issues
        .iter()
        .map(|issue| issue.path.as_str())
        .collect();

    assert!(!validation.valid);
    assert!(paths.contains(&"actor_id"));
    assert!(paths.contains(&"custody_complete"));
    assert!(paths.contains(&"assessment_opened"));
    assert!(paths.contains(&"claim_boundary"));
    assert!(paths.contains(&"forbidden_materials"));
}

#[test]
fn custody_gate_rejects_missing_or_malformed_required_digests() {
    let mut handoff = valid_handoff();
    handoff.source_archive_digest.hex_digest = "not-a-sha256".to_string();
    handoff.runtime_digest.algorithm = ArtifactDigestAlgorithm::Unsupported;
    handoff.launcher_digest.byte_len = 0;
    handoff.split_manifest_digest.hex_digest = "A".repeat(64);

    let validation = validate_fresh_actor_custody_handoff(&handoff);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path == "source_archive_digest"));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path == "runtime_digest"));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path == "launcher_digest"));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path == "split_manifest_digest"));
}

#[test]
fn custody_schema_rejects_untyped_trace_or_secret_fields() {
    let mut value = serde_json::to_value(valid_handoff()).expect("handoff serializes");
    value["raw_trace"] = json!("synthetic sentinel must not enter the schema");
    value["credential"] = json!("synthetic sentinel must not enter the schema");

    let result: Result<FreshActorCustodyHandoff, _> = serde_json::from_value(value);
    assert!(result.is_err());
}

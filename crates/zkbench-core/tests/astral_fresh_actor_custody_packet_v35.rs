use serde_json::json;
use zkbench_core::{
    external_runner::{
        compute_fresh_actor_custody_packet_digest, deserialize_fresh_actor_custody_packet_json,
        serialize_fresh_actor_custody_packet_json, validate_fresh_actor_custody_packet,
        FreshActorCustodyHandoff, FreshActorCustodyPacket, FreshActorCustodyReplayGuard,
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

fn handoff() -> FreshActorCustodyHandoff {
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

fn packet(
    nonce_digit: char,
    predecessor_packet_digest: Option<ArtifactDigest>,
) -> FreshActorCustodyPacket {
    let mut packet = FreshActorCustodyPacket {
        schema_version: ASTRAL_FRESH_ACTOR_CUSTODY_PACKET_SCHEMA_VERSION.to_string(),
        packet_id: format!("v35-synthetic-packet-{nonce_digit}"),
        nonce: nonce_digit.to_string().repeat(64),
        predecessor_packet_digest,
        handoff: handoff(),
        packet_digest: None,
    };
    packet.packet_digest =
        Some(compute_fresh_actor_custody_packet_digest(&packet).expect("synthetic packet hashes"));
    packet
}

#[test]
fn packet_round_trip_is_canonical_and_valid() {
    let packet = packet('1', None);
    let json = serialize_fresh_actor_custody_packet_json(&packet).expect("packet serializes");
    let parsed = deserialize_fresh_actor_custody_packet_json(&json).expect("packet parses");

    assert_eq!(parsed, packet);
    assert!(validate_fresh_actor_custody_packet(&parsed).valid);
    assert_eq!(
        serialize_fresh_actor_custody_packet_json(&parsed).unwrap(),
        json
    );
}

#[test]
fn packet_rejects_tampering_schema_drift_and_unknown_fields() {
    let first_packet = packet('1', None);
    let mut tampered = first_packet.clone();
    tampered.handoff.actor_id = "different-synthetic-actor".to_string();
    let validation = validate_fresh_actor_custody_packet(&tampered);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path == "packet_digest"));

    let mut value = serde_json::to_value(first_packet).expect("packet serializes");
    value["raw_trace"] = json!("synthetic sentinel");
    assert!(deserialize_fresh_actor_custody_packet_json(&value.to_string()).is_err());

    let mut wrong_schema = serde_json::to_value(packet('2', None)).expect("packet serializes");
    wrong_schema["schema_version"] = json!("future-unreviewed-schema");
    assert!(deserialize_fresh_actor_custody_packet_json(&wrong_schema.to_string()).is_err());
}

#[test]
fn replay_guard_enforces_nonce_uniqueness_and_predecessor_order() {
    let first = packet('1', None);
    let second = packet('2', first.packet_digest.clone());
    let mut guard = FreshActorCustodyReplayGuard::default();

    assert!(guard.accept(&first).valid);
    assert!(guard.accept(&second).valid);

    let replay = guard.accept(&second);
    assert!(!replay.valid);
    assert!(replay.issues.iter().any(|issue| issue.path == "nonce"));

    let out_of_order = packet('3', None);
    let rejected = guard.accept(&out_of_order);
    assert!(!rejected.valid);
    assert!(rejected
        .issues
        .iter()
        .any(|issue| issue.path == "predecessor_packet_digest"));
}

#[test]
fn packet_requires_valid_nonce_and_digest() {
    let mut invalid_nonce_packet = packet('1', None);
    invalid_nonce_packet.nonce = "not-a-nonce".to_string();

    let validation = validate_fresh_actor_custody_packet(&invalid_nonce_packet);
    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| issue.path == "nonce"));

    let mut digest_tampered = packet('1', None);
    let mut digest_hex = digest_tampered
        .packet_digest
        .as_ref()
        .expect("packet has a digest")
        .hex_digest
        .clone();
    let replacement = if digest_hex.starts_with('a') {
        "b"
    } else {
        "a"
    };
    digest_hex.replace_range(0..1, replacement);
    digest_tampered
        .packet_digest
        .as_mut()
        .expect("packet has a digest")
        .hex_digest = digest_hex;
    let digest_validation = validate_fresh_actor_custody_packet(&digest_tampered);
    assert!(!digest_validation.valid);
    assert!(digest_validation
        .issues
        .iter()
        .any(|issue| issue.path == "packet_digest"));
}

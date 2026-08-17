use serde_json::json;
use zkbench_core::{
    external_runner::{
        compute_fresh_actor_custody_packet_digest,
        deserialize_fresh_actor_custody_replay_manifest_json,
        serialize_fresh_actor_custody_replay_manifest_json, FreshActorCustodyHandoff,
        FreshActorCustodyIngestDisposition, FreshActorCustodyPacket,
        FreshActorCustodyQuarantineReason, FreshActorCustodyReplayManifest,
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
        packet_id: format!("v36-synthetic-packet-{nonce_digit}"),
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
fn manifest_accepts_chain_and_round_trips_canonically() {
    let mut manifest = FreshActorCustodyReplayManifest::new().expect("manifest builds");
    let first = packet('1', None);
    assert_eq!(
        manifest.ingest(first.clone()).expect("first ingests"),
        FreshActorCustodyIngestDisposition::Accepted
    );
    let second = packet('2', first.packet_digest.clone());
    assert_eq!(
        manifest.ingest(second).expect("second ingests"),
        FreshActorCustodyIngestDisposition::Accepted
    );
    assert!(manifest.validate().valid);

    let json =
        serialize_fresh_actor_custody_replay_manifest_json(&manifest).expect("manifest serializes");
    let parsed =
        deserialize_fresh_actor_custody_replay_manifest_json(&json).expect("manifest deserializes");
    assert_eq!(parsed, manifest);
    assert_eq!(
        serialize_fresh_actor_custody_replay_manifest_json(&parsed).unwrap(),
        json
    );
}

#[test]
fn manifest_quarantines_duplicate_and_out_of_order_packets_without_payloads() {
    let mut manifest = FreshActorCustodyReplayManifest::new().expect("manifest builds");
    let first = packet('1', None);
    assert_eq!(
        manifest.ingest(first.clone()).expect("first ingests"),
        FreshActorCustodyIngestDisposition::Accepted
    );
    assert_eq!(
        manifest.ingest(first).expect("duplicate quarantines"),
        FreshActorCustodyIngestDisposition::Quarantined
    );
    assert_eq!(
        manifest
            .ingest(packet('3', None))
            .expect("out-of-order quarantines"),
        FreshActorCustodyIngestDisposition::Quarantined
    );

    assert_eq!(manifest.entries.len(), 1);
    assert_eq!(manifest.quarantined.len(), 2);
    assert_eq!(
        manifest.quarantined[0].reason,
        FreshActorCustodyQuarantineReason::DuplicateNonce
    );
    assert_eq!(
        manifest.quarantined[1].reason,
        FreshActorCustodyQuarantineReason::PredecessorMismatch
    );
    assert!(manifest.validate().valid);
}

#[test]
fn manifest_rejects_chain_tampering_and_unknown_fields() {
    let mut manifest = FreshActorCustodyReplayManifest::new().expect("manifest builds");
    manifest.ingest(packet('1', None)).expect("packet ingests");
    manifest.entries[0].packet.handoff.actor_id = "tampered-actor".to_string();
    assert!(!manifest.validate().valid);
    assert!(serialize_fresh_actor_custody_replay_manifest_json(&manifest).is_err());

    let mut clean = FreshActorCustodyReplayManifest::new().expect("manifest builds");
    clean.ingest(packet('1', None)).expect("packet ingests");
    let mut value = serde_json::to_value(clean).expect("manifest serializes");
    value["raw_trace"] = json!("synthetic sentinel");
    assert!(deserialize_fresh_actor_custody_replay_manifest_json(&value.to_string()).is_err());
}

#[test]
fn invalid_packet_is_quarantined_and_manifest_stays_valid() {
    let mut manifest = FreshActorCustodyReplayManifest::new().expect("manifest builds");
    let mut invalid = packet('1', None);
    invalid.handoff.assessment_opened = true;
    assert_eq!(
        manifest
            .ingest(invalid)
            .expect("invalid packet quarantines"),
        FreshActorCustodyIngestDisposition::Quarantined
    );
    assert_eq!(manifest.entries.len(), 0);
    assert_eq!(manifest.quarantined.len(), 1);
    assert_eq!(
        manifest.quarantined[0].reason,
        FreshActorCustodyQuarantineReason::InvalidPacket
    );
    assert!(manifest.validate().valid);
}

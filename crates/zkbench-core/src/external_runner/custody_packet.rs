//! Deterministic integrity and replay preflight for a V34 custody handoff.
//!
//! This packet is metadata-only. It does not prove artifact authenticity,
//! verify a signature, load a model, or authorize an assessment.

use std::collections::BTreeSet;

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{ArtifactDigest, ArtifactDigestAlgorithm};

use super::actor_custody::{
    validate_fresh_actor_custody_handoff, FreshActorCustodyHandoff,
    FreshActorCustodyValidationIssue,
};

/// State slice governed by this packet.
pub const ASTRAL_FRESH_ACTOR_CUSTODY_PACKET_STATE_SLICE: &str =
    "astral-fresh-actor-custody-packet-v35";

/// Schema version for deterministic V35 custody packets.
pub const ASTRAL_FRESH_ACTOR_CUSTODY_PACKET_SCHEMA_VERSION: &str =
    "astral-fresh-actor-custody-packet-v35";

/// A deterministic, typed custody packet.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FreshActorCustodyPacket {
    /// Fixed packet schema version.
    pub schema_version: String,
    /// Packet identifier.
    pub packet_id: String,
    /// Unique packet nonce represented as lowercase hexadecimal.
    pub nonce: String,
    /// Digest of the immediately preceding accepted packet, if any.
    #[serde(default)]
    pub predecessor_packet_digest: Option<ArtifactDigest>,
    /// V34 typed custody handoff.
    pub handoff: FreshActorCustodyHandoff,
    /// SHA-256 digest over the packet with this field set to null.
    pub packet_digest: Option<ArtifactDigest>,
}

/// Packet validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FreshActorCustodyPacketValidation {
    /// True only when the packet is internally consistent.
    pub valid: bool,
    /// Deterministic validation issues.
    pub issues: Vec<FreshActorCustodyValidationIssue>,
}

/// Stateful local replay guard for a sequence of custody packets.
#[derive(Debug, Clone, Default, PartialEq, Eq)]
pub struct FreshActorCustodyReplayGuard {
    seen_nonces: BTreeSet<String>,
    expected_predecessor: Option<ArtifactDigest>,
}

impl FreshActorCustodyReplayGuard {
    /// Validate and record one packet only when it is fresh and in order.
    pub fn accept(
        &mut self,
        packet: &FreshActorCustodyPacket,
    ) -> FreshActorCustodyPacketValidation {
        let mut validation = validate_fresh_actor_custody_packet(packet);
        if !validation.valid {
            return validation;
        }
        if self.seen_nonces.contains(&packet.nonce) {
            validation
                .issues
                .push(issue("nonce", "packet nonce has already been accepted"));
        }
        if packet.predecessor_packet_digest != self.expected_predecessor {
            validation.issues.push(issue(
                "predecessor_packet_digest",
                "packet predecessor does not match the local accepted sequence",
            ));
        }
        if validation.issues.is_empty() {
            self.seen_nonces.insert(packet.nonce.clone());
            self.expected_predecessor = packet.packet_digest.clone();
        }
        validation.valid = validation.issues.is_empty();
        validation
    }
}

/// Validate a custody packet without changing replay state.
pub fn validate_fresh_actor_custody_packet(
    packet: &FreshActorCustodyPacket,
) -> FreshActorCustodyPacketValidation {
    let mut issues = Vec::new();
    require_nonempty(&packet.schema_version, "schema_version", &mut issues);
    require_nonempty(&packet.packet_id, "packet_id", &mut issues);
    require_nonempty(&packet.nonce, "nonce", &mut issues);
    if packet.schema_version != ASTRAL_FRESH_ACTOR_CUSTODY_PACKET_SCHEMA_VERSION {
        issues.push(issue(
            "schema_version",
            "packet schema version does not match the V35 contract",
        ));
    }
    if !is_lower_hex_64(&packet.nonce) {
        issues.push(issue(
            "nonce",
            "packet nonce must be exactly 64 lowercase hexadecimal characters",
        ));
    }
    let handoff_validation = validate_fresh_actor_custody_handoff(&packet.handoff);
    issues.extend(handoff_validation.issues);
    if let Some(predecessor) = &packet.predecessor_packet_digest {
        validate_digest("predecessor_packet_digest", predecessor, &mut issues);
    }
    match &packet.packet_digest {
        Some(packet_digest) => {
            validate_digest("packet_digest", packet_digest, &mut issues);
            if issues.is_empty() {
                match compute_fresh_actor_custody_packet_digest(packet) {
                    Ok(expected) if expected != *packet_digest => issues.push(issue(
                        "packet_digest",
                        "packet digest does not match canonical packet bytes",
                    )),
                    Err(error) => issues.push(issue("packet_digest", &error.to_string())),
                    Ok(_) => {}
                }
            }
        }
        None => issues.push(issue("packet_digest", "packet digest is required")),
    }
    FreshActorCustodyPacketValidation {
        valid: issues.is_empty(),
        issues,
    }
}

/// Serialize a validated custody packet using deterministic compact JSON.
pub fn serialize_fresh_actor_custody_packet_json(
    packet: &FreshActorCustodyPacket,
) -> Result<String> {
    let validation = validate_fresh_actor_custody_packet(packet);
    if !validation.valid {
        return Err(ZkBenchError::validation(
            "fresh_actor_custody_packet",
            "cannot serialize an invalid custody packet",
        ));
    }
    serde_json::to_string(packet).map_err(|error| {
        ZkBenchError::serialization("fresh_actor_custody_packet", error.to_string())
    })
}

/// Deserialize and validate one custody packet.
pub fn deserialize_fresh_actor_custody_packet_json(json: &str) -> Result<FreshActorCustodyPacket> {
    let packet: FreshActorCustodyPacket = serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("fresh_actor_custody_packet", error.to_string())
    })?;
    let validation = validate_fresh_actor_custody_packet(&packet);
    if !validation.valid {
        return Err(ZkBenchError::validation(
            "fresh_actor_custody_packet",
            "deserialized custody packet failed integrity validation",
        ));
    }
    Ok(packet)
}

/// Compute the SHA-256 digest over canonical packet bytes with no self-digest.
pub fn compute_fresh_actor_custody_packet_digest(
    packet: &FreshActorCustodyPacket,
) -> Result<ArtifactDigest> {
    let mut unsigned = packet.clone();
    unsigned.packet_digest = None;
    let bytes = serde_json::to_vec(&unsigned).map_err(|error| {
        ZkBenchError::serialization("fresh_actor_custody_packet.digest", error.to_string())
    })?;
    let digest = Sha256::digest(&bytes);
    Ok(ArtifactDigest {
        algorithm: ArtifactDigestAlgorithm::Sha256,
        hex_digest: hex::encode(digest),
        byte_len: bytes.len(),
        kind: None,
        role: None,
    })
}

fn require_nonempty(value: &str, path: &str, issues: &mut Vec<FreshActorCustodyValidationIssue>) {
    if value.trim().is_empty() {
        issues.push(issue(path, "required value is empty"));
    }
}

fn validate_digest(
    path: &str,
    digest: &ArtifactDigest,
    issues: &mut Vec<FreshActorCustodyValidationIssue>,
) {
    if digest.algorithm != ArtifactDigestAlgorithm::Sha256 {
        issues.push(issue(path, "packet digest must use SHA-256"));
    }
    if digest.byte_len == 0 {
        issues.push(issue(path, "packet digest byte length must be positive"));
    }
    if !is_lower_hex_64(&digest.hex_digest) {
        issues.push(issue(
            path,
            "packet digest must be exactly 64 lowercase hexadecimal characters",
        ));
    }
}

fn is_lower_hex_64(value: &str) -> bool {
    value.len() == 64
        && value
            .chars()
            .all(|character| character.is_ascii_digit() || ('a'..='f').contains(&character))
}

fn issue(path: &str, message: &str) -> FreshActorCustodyValidationIssue {
    FreshActorCustodyValidationIssue {
        path: path.to_string(),
        message: message.to_string(),
    }
}

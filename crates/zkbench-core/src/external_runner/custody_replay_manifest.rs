//! Append-only local replay manifest for V35 custody packets.
//!
//! The manifest is a serialized local control artifact. It is not a durable
//! distributed replay service, an attestation, accepted evidence, or an
//! execution authorization.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{ArtifactDigest, ArtifactDigestAlgorithm, ClaimBoundary};

use super::custody_packet::{
    validate_fresh_actor_custody_packet, FreshActorCustodyPacket, FreshActorCustodyPacketValidation,
};

/// State slice governed by this manifest.
pub const ASTRAL_FRESH_ACTOR_CUSTODY_REPLAY_MANIFEST_STATE_SLICE: &str =
    "astral-fresh-actor-custody-replay-manifest-v36";

/// Fixed schema version for the manifest.
pub const ASTRAL_FRESH_ACTOR_CUSTODY_REPLAY_MANIFEST_SCHEMA_VERSION: &str =
    "astral-fresh-actor-custody-replay-manifest-v36";

/// Result of ingesting one packet.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum FreshActorCustodyIngestDisposition {
    /// Packet was added to the accepted local chain.
    Accepted,
    /// Packet was represented by a typed quarantine record.
    Quarantined,
}

/// Quarantine reason without retaining the rejected packet payload.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum FreshActorCustodyQuarantineReason {
    /// Packet failed its own typed validation.
    InvalidPacket,
    /// Packet nonce was already accepted.
    DuplicateNonce,
    /// Packet id was already accepted.
    DuplicatePacketId,
    /// Packet predecessor did not match the accepted chain tip.
    PredecessorMismatch,
}

/// Typed quarantine record for one rejected packet.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FreshActorCustodyQuarantineEntry {
    /// Packet identifier, if present in the rejected envelope.
    pub packet_id: String,
    /// Packet nonce, if present in the rejected envelope.
    pub nonce: String,
    /// Packet digest, if present in the rejected envelope.
    #[serde(default)]
    pub packet_digest: Option<ArtifactDigest>,
    /// Typed rejection reason.
    pub reason: FreshActorCustodyQuarantineReason,
}

/// Accepted custody packet entry in the append-only chain.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FreshActorCustodyReplayEntry {
    /// Zero-based sequence number.
    pub sequence_number: u64,
    /// Accepted packet.
    pub packet: FreshActorCustodyPacket,
    /// Previous entry digest.
    #[serde(default)]
    pub previous_entry_digest: Option<ArtifactDigest>,
    /// Digest over this entry with this field set to null.
    pub entry_digest: Option<ArtifactDigest>,
}

/// Append-only local replay manifest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FreshActorCustodyReplayManifest {
    /// Fixed schema version.
    pub schema_version: String,
    /// Required state slice.
    pub state_slice: String,
    /// Claim ceiling for this local control artifact.
    pub claim_boundary: ClaimBoundary,
    /// Accepted packet chain.
    pub entries: Vec<FreshActorCustodyReplayEntry>,
    /// Typed quarantine records without rejected packet payloads.
    #[serde(default)]
    pub quarantined: Vec<FreshActorCustodyQuarantineEntry>,
    /// Digest over the manifest with this field set to null.
    pub manifest_digest: Option<ArtifactDigest>,
}

/// Manifest validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FreshActorCustodyReplayManifestValidationIssue {
    /// Field or entry path.
    pub path: String,
    /// Human-readable issue.
    pub message: String,
}

/// Manifest validation result.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FreshActorCustodyReplayManifestValidation {
    /// True only when the chain and manifest digest are valid.
    pub valid: bool,
    /// Deterministic issues.
    pub issues: Vec<FreshActorCustodyReplayManifestValidationIssue>,
}

impl FreshActorCustodyReplayManifest {
    /// Create an empty manifest and compute its initial digest.
    pub fn new() -> Result<Self> {
        let mut manifest = Self {
            schema_version: ASTRAL_FRESH_ACTOR_CUSTODY_REPLAY_MANIFEST_SCHEMA_VERSION.to_string(),
            state_slice: ASTRAL_FRESH_ACTOR_CUSTODY_REPLAY_MANIFEST_STATE_SLICE.to_string(),
            claim_boundary: ClaimBoundary::Level0DesignNote,
            entries: Vec::new(),
            quarantined: Vec::new(),
            manifest_digest: None,
        };
        manifest.refresh_digest()?;
        Ok(manifest)
    }

    /// Ingest one packet, accepting it only when it extends the local chain.
    pub fn ingest(
        &mut self,
        packet: FreshActorCustodyPacket,
    ) -> Result<FreshActorCustodyIngestDisposition> {
        let packet_validation = validate_fresh_actor_custody_packet(&packet);
        let reason = if !packet_validation.valid {
            Some(FreshActorCustodyQuarantineReason::InvalidPacket)
        } else if self
            .entries
            .iter()
            .any(|entry| entry.packet.nonce == packet.nonce)
        {
            Some(FreshActorCustodyQuarantineReason::DuplicateNonce)
        } else if self
            .entries
            .iter()
            .any(|entry| entry.packet.packet_id == packet.packet_id)
        {
            Some(FreshActorCustodyQuarantineReason::DuplicatePacketId)
        } else {
            let expected_predecessor = self
                .entries
                .last()
                .and_then(|entry| entry.packet.packet_digest.clone());
            (packet.predecessor_packet_digest != expected_predecessor)
                .then_some(FreshActorCustodyQuarantineReason::PredecessorMismatch)
        };

        if let Some(reason) = reason {
            self.quarantined.push(FreshActorCustodyQuarantineEntry {
                packet_id: packet.packet_id,
                nonce: packet.nonce,
                packet_digest: packet.packet_digest,
                reason,
            });
            self.refresh_digest()?;
            return Ok(FreshActorCustodyIngestDisposition::Quarantined);
        }

        let entry = FreshActorCustodyReplayEntry {
            sequence_number: self.entries.len() as u64,
            previous_entry_digest: self
                .entries
                .last()
                .and_then(|entry| entry.entry_digest.clone()),
            packet,
            entry_digest: None,
        };
        let mut entry = entry;
        entry.entry_digest = Some(compute_fresh_actor_custody_replay_entry_digest(&entry)?);
        self.entries.push(entry);
        self.refresh_digest()?;
        Ok(FreshActorCustodyIngestDisposition::Accepted)
    }

    /// Validate the complete local chain and manifest digest.
    pub fn validate(&self) -> FreshActorCustodyReplayManifestValidation {
        let mut issues = Vec::new();
        if self.schema_version != ASTRAL_FRESH_ACTOR_CUSTODY_REPLAY_MANIFEST_SCHEMA_VERSION {
            issues.push(issue(
                "schema_version",
                "manifest schema version does not match V36",
            ));
        }
        if self.state_slice != ASTRAL_FRESH_ACTOR_CUSTODY_REPLAY_MANIFEST_STATE_SLICE {
            issues.push(issue(
                "state_slice",
                "manifest state slice does not match V36",
            ));
        }
        if self.claim_boundary != ClaimBoundary::Level0DesignNote {
            issues.push(issue(
                "claim_boundary",
                "custody replay manifests remain Level0DesignNote",
            ));
        }

        let mut previous_entry_digest = None;
        let mut previous_packet_digest = None;
        for (index, entry) in self.entries.iter().enumerate() {
            if entry.sequence_number != index as u64 {
                issues.push(issue(
                    &format!("entries[{index}].sequence_number"),
                    "sequence number does not match entry position",
                ));
            }
            if entry.previous_entry_digest != previous_entry_digest {
                issues.push(issue(
                    &format!("entries[{index}].previous_entry_digest"),
                    "previous entry digest does not match chain tip",
                ));
            }
            let packet_validation = validate_fresh_actor_custody_packet(&entry.packet);
            append_packet_issues(index, packet_validation, &mut issues);
            if entry.packet.predecessor_packet_digest != previous_packet_digest {
                issues.push(issue(
                    &format!("entries[{index}].packet.predecessor_packet_digest"),
                    "packet predecessor does not match prior accepted packet",
                ));
            }
            match (
                &entry.entry_digest,
                compute_fresh_actor_custody_replay_entry_digest(entry),
            ) {
                (Some(actual), Ok(expected)) if *actual == expected => {}
                (Some(_), Ok(_)) => issues.push(issue(
                    &format!("entries[{index}].entry_digest"),
                    "entry digest mismatch",
                )),
                (None, _) => issues.push(issue(
                    &format!("entries[{index}].entry_digest"),
                    "entry digest is required",
                )),
                (_, Err(error)) => issues.push(issue(
                    &format!("entries[{index}].entry_digest"),
                    &error.to_string(),
                )),
            }
            previous_entry_digest = entry.entry_digest.clone();
            previous_packet_digest = entry.packet.packet_digest.clone();
        }

        if self.entries.iter().enumerate().any(|(index, entry)| {
            self.entries[..index]
                .iter()
                .any(|prior| prior.packet.nonce == entry.packet.nonce)
        }) {
            issues.push(issue("entries", "accepted packet nonce is duplicated"));
        }

        match (
            &self.manifest_digest,
            compute_fresh_actor_custody_replay_manifest_digest(self),
        ) {
            (Some(actual), Ok(expected)) if *actual == expected => {}
            (Some(_), Ok(_)) => issues.push(issue("manifest_digest", "manifest digest mismatch")),
            (None, _) => issues.push(issue("manifest_digest", "manifest digest is required")),
            (_, Err(error)) => issues.push(issue("manifest_digest", &error.to_string())),
        }

        FreshActorCustodyReplayManifestValidation {
            valid: issues.is_empty(),
            issues,
        }
    }

    fn refresh_digest(&mut self) -> Result<()> {
        self.manifest_digest = None;
        self.manifest_digest = Some(compute_fresh_actor_custody_replay_manifest_digest(self)?);
        Ok(())
    }
}

/// Serialize a validated replay manifest to deterministic compact JSON.
pub fn serialize_fresh_actor_custody_replay_manifest_json(
    manifest: &FreshActorCustodyReplayManifest,
) -> Result<String> {
    if !manifest.validate().valid {
        return Err(ZkBenchError::validation(
            "fresh_actor_custody_replay_manifest",
            "cannot serialize an invalid replay manifest",
        ));
    }
    serde_json::to_string(manifest).map_err(|error| {
        ZkBenchError::serialization("fresh_actor_custody_replay_manifest", error.to_string())
    })
}

/// Deserialize and validate a replay manifest.
pub fn deserialize_fresh_actor_custody_replay_manifest_json(
    json: &str,
) -> Result<FreshActorCustodyReplayManifest> {
    let manifest: FreshActorCustodyReplayManifest =
        serde_json::from_str(json).map_err(|error| {
            ZkBenchError::deserialization("fresh_actor_custody_replay_manifest", error.to_string())
        })?;
    if !manifest.validate().valid {
        return Err(ZkBenchError::validation(
            "fresh_actor_custody_replay_manifest",
            "deserialized replay manifest failed validation",
        ));
    }
    Ok(manifest)
}

/// Compute an accepted-entry digest with its self-digest removed.
pub fn compute_fresh_actor_custody_replay_entry_digest(
    entry: &FreshActorCustodyReplayEntry,
) -> Result<ArtifactDigest> {
    let mut unsigned = entry.clone();
    unsigned.entry_digest = None;
    digest_json(&unsigned, "fresh_actor_custody_replay_entry")
}

/// Compute a manifest digest with its self-digest removed.
pub fn compute_fresh_actor_custody_replay_manifest_digest(
    manifest: &FreshActorCustodyReplayManifest,
) -> Result<ArtifactDigest> {
    let mut unsigned = manifest.clone();
    unsigned.manifest_digest = None;
    digest_json(&unsigned, "fresh_actor_custody_replay_manifest")
}

fn append_packet_issues(
    index: usize,
    validation: FreshActorCustodyPacketValidation,
    issues: &mut Vec<FreshActorCustodyReplayManifestValidationIssue>,
) {
    for packet_issue in validation.issues {
        issues.push(issue(
            &format!("entries[{index}].packet.{}", packet_issue.path),
            &packet_issue.message,
        ));
    }
}

fn digest_json<T: Serialize>(value: &T, path: &str) -> Result<ArtifactDigest> {
    let bytes = serde_json::to_vec(value)
        .map_err(|error| ZkBenchError::serialization(path, error.to_string()))?;
    let digest = Sha256::digest(&bytes);
    Ok(ArtifactDigest {
        algorithm: ArtifactDigestAlgorithm::Sha256,
        hex_digest: hex::encode(digest),
        byte_len: bytes.len(),
        kind: None,
        role: None,
    })
}

fn issue(path: &str, message: &str) -> FreshActorCustodyReplayManifestValidationIssue {
    FreshActorCustodyReplayManifestValidationIssue {
        path: path.to_string(),
        message: message.to_string(),
    }
}

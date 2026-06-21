//! HSAI-owned challenge packet helpers for future Phala/dstack artifact capture.
//!
//! This module emits deterministic, non-secret capture inputs only. It performs
//! no network access and does not create attestation evidence.

use hsai_agent_case::AgentCase;
use hsai_attestation::report_data_binding;
use hsai_distinct_agent::Anchor;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

pub const HSAI_CHALLENGE_SCHEMA_VERSION: &str = "hsai-phala-challenge:v1";
pub const HSAI_CAPTURE_MANIFEST_SCHEMA_VERSION: &str = "hsai-phala-capture-manifest:v1";
pub const PHASE_57_CLAIM_BOUNDARY: &str = "Phase 57 challenge packets are local capture instructions only; they are not attestation evidence, proof, benchmark output, or independent Phase 4 authorization.";

const CASE_HASH_HEX_LEN: usize = 64;
const REPORT_DATA_HEX_LEN: usize = 64;

/// Provider mode expected for the future capture flow.
#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RealArtifactProviderMode {
    /// Future local quote/collateral verification path.
    LocalQuote,
    /// Future managed verifier response path with explicit managed trust root.
    ManagedVerifier,
}

/// Input material for an HSAI-owned Phala/dstack challenge packet.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct HsaiChallengeInput {
    pub subject: String,
    pub anchor_id: String,
    pub agent_pubkey_spki_hex: String,
    pub nonce: u64,
    pub case_hash_hex: String,
    pub challenge_created_at: u64,
    pub challenge_expires_at: u64,
    pub policy_id: String,
}

/// Deterministic challenge packet to hand to the attested workload.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct HsaiChallengePacket {
    pub schema_version: String,
    pub challenge_id: String,
    pub subject: String,
    pub anchor_id: String,
    pub agent_pubkey_spki_hex: String,
    pub nonce: u64,
    pub case_hash_hex: String,
    pub challenge_created_at: u64,
    pub challenge_expires_at: u64,
    pub policy_id: String,
    pub expected_report_data_hex: String,
}

/// Non-secret capture workflow manifest for an operator or external capture job.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct CaptureWorkflowManifest {
    pub schema_version: String,
    pub challenge: HsaiChallengePacket,
    pub provider: String,
    pub provider_mode: RealArtifactProviderMode,
    pub report_data_field: String,
    pub required_artifact_fields: Vec<String>,
    pub forbidden_artifact_fields: Vec<String>,
    pub claim_boundary: String,
}

/// Local replay guard for single-use challenge packets.
#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct ChallengeReplayGuard {
    consumed_challenge_ids: BTreeSet<String>,
}

/// Errors for local challenge-packet construction and validation.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum ChallengeError {
    EmptyField {
        field: String,
    },
    InvalidHex {
        field: String,
        value: String,
    },
    InvalidHexLength {
        field: String,
        actual: usize,
        expected: usize,
    },
    InvalidWindow {
        created_at: u64,
        expires_at: u64,
    },
    NotYetValid {
        now: u64,
        created_at: u64,
    },
    ExpiredChallenge {
        now: u64,
        expires_at: u64,
    },
    ReportDataMismatch {
        actual: String,
        expected: String,
    },
    ChallengeIdMismatch {
        actual: String,
        expected: String,
    },
    ReplayedChallenge {
        challenge_id: String,
    },
    SchemaMismatch {
        actual: String,
    },
    Serialization(String),
}

impl std::fmt::Display for ChallengeError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{self:?}")
    }
}

impl std::error::Error for ChallengeError {}

impl ChallengeReplayGuard {
    pub fn new() -> Self {
        Self::default()
    }

    /// Consume a challenge exactly once inside a local capture session.
    pub fn consume(
        &mut self,
        packet: &HsaiChallengePacket,
        now: u64,
    ) -> Result<(), ChallengeError> {
        validate_hsai_challenge_packet(packet, now)?;
        if !self
            .consumed_challenge_ids
            .insert(packet.challenge_id.clone())
        {
            return Err(ChallengeError::ReplayedChallenge {
                challenge_id: packet.challenge_id.clone(),
            });
        }
        Ok(())
    }
}

/// Build a challenge packet directly from normalized input fields.
pub fn build_hsai_challenge_packet(
    input: HsaiChallengeInput,
) -> Result<HsaiChallengePacket, ChallengeError> {
    validate_nonempty("subject", &input.subject)?;
    validate_nonempty("anchor_id", &input.anchor_id)?;
    validate_nonempty("policy_id", &input.policy_id)?;
    validate_window(input.challenge_created_at, input.challenge_expires_at)?;

    let agent_pubkey_hex =
        normalize_hex("agent_pubkey_spki_hex", &input.agent_pubkey_spki_hex, None)?;
    let case_hash_hex = normalize_hex(
        "case_hash_hex",
        &input.case_hash_hex,
        Some(CASE_HASH_HEX_LEN),
    )?;
    let agent_pubkey = decode_hex("agent_pubkey_spki_hex", &agent_pubkey_hex, None)?;
    let case_hash = decode_hex("case_hash_hex", &case_hash_hex, Some(CASE_HASH_HEX_LEN))?;
    let expected_report_data_hex =
        encode_hex(&report_data_binding(&agent_pubkey, input.nonce, &case_hash));

    let mut packet = HsaiChallengePacket {
        schema_version: HSAI_CHALLENGE_SCHEMA_VERSION.to_owned(),
        challenge_id: String::new(),
        subject: input.subject,
        anchor_id: input.anchor_id,
        agent_pubkey_spki_hex: agent_pubkey_hex,
        nonce: input.nonce,
        case_hash_hex,
        challenge_created_at: input.challenge_created_at,
        challenge_expires_at: input.challenge_expires_at,
        policy_id: input.policy_id,
        expected_report_data_hex,
    };
    packet.challenge_id = challenge_id(&packet);
    Ok(packet)
}

/// Build a challenge packet from an `AgentCase` and runtime anchor.
pub fn build_agent_case_challenge_packet(
    case: &AgentCase,
    anchor: &Anchor,
    agent_pubkey_spki_hex: &str,
    nonce: u64,
    challenge_created_at: u64,
    challenge_expires_at: u64,
    policy_id: &str,
) -> Result<HsaiChallengePacket, ChallengeError> {
    build_hsai_challenge_packet(HsaiChallengeInput {
        subject: case.subject.0.clone(),
        anchor_id: anchor.anchor_id(),
        agent_pubkey_spki_hex: agent_pubkey_spki_hex.to_owned(),
        nonce,
        case_hash_hex: encode_hex(&agent_case_hash(case)?),
        challenge_created_at,
        challenge_expires_at,
        policy_id: policy_id.to_owned(),
    })
}

/// Validate that a packet still matches the HSAI report-data binding.
pub fn validate_hsai_challenge_packet(
    packet: &HsaiChallengePacket,
    now: u64,
) -> Result<(), ChallengeError> {
    if packet.schema_version != HSAI_CHALLENGE_SCHEMA_VERSION {
        return Err(ChallengeError::SchemaMismatch {
            actual: packet.schema_version.clone(),
        });
    }
    validate_nonempty("subject", &packet.subject)?;
    validate_nonempty("anchor_id", &packet.anchor_id)?;
    validate_nonempty("policy_id", &packet.policy_id)?;
    validate_window(packet.challenge_created_at, packet.challenge_expires_at)?;
    if now < packet.challenge_created_at {
        return Err(ChallengeError::NotYetValid {
            now,
            created_at: packet.challenge_created_at,
        });
    }
    if now > packet.challenge_expires_at {
        return Err(ChallengeError::ExpiredChallenge {
            now,
            expires_at: packet.challenge_expires_at,
        });
    }

    let agent_pubkey_hex =
        normalize_hex("agent_pubkey_spki_hex", &packet.agent_pubkey_spki_hex, None)?;
    let case_hash_hex = normalize_hex(
        "case_hash_hex",
        &packet.case_hash_hex,
        Some(CASE_HASH_HEX_LEN),
    )?;
    let expected_report_data_hex = normalize_hex(
        "expected_report_data_hex",
        &packet.expected_report_data_hex,
        Some(REPORT_DATA_HEX_LEN),
    )?;
    let agent_pubkey = decode_hex("agent_pubkey_spki_hex", &agent_pubkey_hex, None)?;
    let case_hash = decode_hex("case_hash_hex", &case_hash_hex, Some(CASE_HASH_HEX_LEN))?;
    let recomputed = encode_hex(&report_data_binding(
        &agent_pubkey,
        packet.nonce,
        &case_hash,
    ));
    if expected_report_data_hex != recomputed {
        return Err(ChallengeError::ReportDataMismatch {
            actual: expected_report_data_hex,
            expected: recomputed,
        });
    }

    let expected_challenge_id = challenge_id(packet);
    if packet.challenge_id != expected_challenge_id {
        return Err(ChallengeError::ChallengeIdMismatch {
            actual: packet.challenge_id.clone(),
            expected: expected_challenge_id,
        });
    }

    Ok(())
}

/// Build the non-secret capture manifest an operator should hand to the CVM flow.
pub fn capture_workflow_manifest(
    challenge: HsaiChallengePacket,
    provider_mode: RealArtifactProviderMode,
) -> CaptureWorkflowManifest {
    CaptureWorkflowManifest {
        schema_version: HSAI_CAPTURE_MANIFEST_SCHEMA_VERSION.to_owned(),
        challenge,
        provider: "phala-dstack".to_owned(),
        provider_mode,
        report_data_field: "Set the provider custom-data/reportData field to challenge.expected_report_data_hex exactly.".to_owned(),
        required_artifact_fields: [
            "schema_version",
            "source",
            "captured_at",
            "challenge_created_at",
            "challenge_expires_at",
            "policy_id",
            "subject",
            "anchor_id",
            "agent_pubkey_spki_hex",
            "nonce",
            "case_hash_hex",
            "expected_report_data_hex",
            "provider",
            "provider_mode",
            "quote_hex or managed_verifier_response",
            "report_data_hex",
            "compose_hash",
            "app_id",
            "instance_id",
            "os_image_hash",
            "rtmrs",
            "rtmr_event_log",
            "docker_image_digests",
            "trust_root_labels",
        ]
        .into_iter()
        .map(str::to_owned)
        .collect(),
        forbidden_artifact_fields: [
            "private_keys",
            "api_tokens",
            "session_cookies",
            "bearer_tokens",
            "live_service_credentials",
        ]
        .into_iter()
        .map(str::to_owned)
        .collect(),
        claim_boundary: PHASE_57_CLAIM_BOUNDARY.to_owned(),
    }
}

/// Deterministically hash the local `AgentCase` into the Phase 57 case hash.
pub fn agent_case_hash(case: &AgentCase) -> Result<Vec<u8>, ChallengeError> {
    let case_json =
        serde_json::to_vec(case).map_err(|err| ChallengeError::Serialization(err.to_string()))?;
    let mut hasher = Sha256::new();
    hasher.update(b"hsai-agent-case-hash:v1");
    hasher.update((case_json.len() as u64).to_be_bytes());
    hasher.update(case_json);
    Ok(hasher.finalize().to_vec())
}

fn validate_nonempty(field: &str, value: &str) -> Result<(), ChallengeError> {
    if value.is_empty() {
        Err(ChallengeError::EmptyField {
            field: field.to_owned(),
        })
    } else {
        Ok(())
    }
}

fn validate_window(created_at: u64, expires_at: u64) -> Result<(), ChallengeError> {
    if created_at >= expires_at {
        Err(ChallengeError::InvalidWindow {
            created_at,
            expires_at,
        })
    } else {
        Ok(())
    }
}

fn challenge_id(packet: &HsaiChallengePacket) -> String {
    let mut hasher = Sha256::new();
    update_str(&mut hasher, HSAI_CHALLENGE_SCHEMA_VERSION);
    update_str(&mut hasher, &packet.subject);
    update_str(&mut hasher, &packet.anchor_id);
    update_str(&mut hasher, &packet.agent_pubkey_spki_hex);
    hasher.update(packet.nonce.to_be_bytes());
    update_str(&mut hasher, &packet.case_hash_hex);
    hasher.update(packet.challenge_created_at.to_be_bytes());
    hasher.update(packet.challenge_expires_at.to_be_bytes());
    update_str(&mut hasher, &packet.policy_id);
    update_str(&mut hasher, &packet.expected_report_data_hex);
    encode_hex(&hasher.finalize())
}

fn update_str(hasher: &mut Sha256, value: &str) {
    hasher.update((value.len() as u64).to_be_bytes());
    hasher.update(value.as_bytes());
}

fn normalize_hex(
    field: &str,
    value: &str,
    expected_len: Option<usize>,
) -> Result<String, ChallengeError> {
    let value = value
        .strip_prefix("0x")
        .unwrap_or(value)
        .to_ascii_lowercase();
    if let Some(expected) = expected_len {
        if value.len() != expected {
            return Err(ChallengeError::InvalidHexLength {
                field: field.to_owned(),
                actual: value.len(),
                expected,
            });
        }
    }
    if value.is_empty()
        || value.len() % 2 != 0
        || !value.as_bytes().iter().all(u8::is_ascii_hexdigit)
    {
        return Err(ChallengeError::InvalidHex {
            field: field.to_owned(),
            value,
        });
    }
    Ok(value)
}

fn decode_hex(
    field: &str,
    value: &str,
    expected_len: Option<usize>,
) -> Result<Vec<u8>, ChallengeError> {
    let value = normalize_hex(field, value, expected_len)?;
    (0..value.len())
        .step_by(2)
        .map(|index| {
            u8::from_str_radix(&value[index..index + 2], 16).map_err(|_| {
                ChallengeError::InvalidHex {
                    field: field.to_owned(),
                    value: value.clone(),
                }
            })
        })
        .collect()
}

fn encode_hex(bytes: &[u8]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut out = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        out.push(HEX[(byte >> 4) as usize] as char);
        out.push(HEX[(byte & 0x0f) as usize] as char);
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use hsai_agent_case::{ActionId, MemoryRoot, ModelId, OracleContract, Verdict};
    use hsai_claim_envelope::{Predicate, PropertyKind, SubjectId};
    use hsai_distinct_agent::distinctness;

    const AGENT_PUBKEY_HEX: &str = "aabbccddeeff00112233445566778899";
    const NONCE: u64 = 77;
    const CREATED_AT: u64 = 1_000;
    const EXPIRES_AT: u64 = 1_600;
    const NOW: u64 = 1_200;

    fn subject(id: &str) -> SubjectId {
        SubjectId(id.to_owned())
    }

    fn anchor() -> Anchor {
        Anchor::HardwareAttested {
            vendor: "phala-dstack".to_owned(),
            device: "phase57-agent-case-emitter".to_owned(),
        }
    }

    fn semantic_correctness_action() -> Predicate {
        Predicate {
            subject: subject("phase57-action"),
            property: PropertyKind::SemanticCorrectness,
        }
    }

    fn case() -> AgentCase {
        let subject = subject("phase57-agent");
        AgentCase {
            action: ActionId("phase57-admit-work".to_owned()),
            subject: subject.clone(),
            claimed_model: ModelId("phase57-agent-case-emitter".to_owned()),
            memory_root: MemoryRoot([9; 32]),
            observed_at: NOW,
            oracle: OracleContract {
                expected: Verdict::Accept,
                target_guarantees: BTreeSet::from([distinctness(&subject)]),
                excluded: BTreeSet::from([semantic_correctness_action()]),
            },
        }
    }

    fn packet() -> HsaiChallengePacket {
        build_agent_case_challenge_packet(
            &case(),
            &anchor(),
            AGENT_PUBKEY_HEX,
            NONCE,
            CREATED_AT,
            EXPIRES_AT,
            "phase57:test-policy",
        )
        .expect("challenge packet should build")
    }

    #[test]
    fn ra_1_fresh_challenge_binding_is_accepted() {
        let packet = packet();
        let agent_pubkey =
            decode_hex("agent_pubkey_spki_hex", AGENT_PUBKEY_HEX, None).expect("test key decodes");
        let expected = encode_hex(&report_data_binding(
            &agent_pubkey,
            NONCE,
            &agent_case_hash(&case()).expect("case hash builds"),
        ));

        assert_eq!(packet.expected_report_data_hex, expected);
        assert_eq!(validate_hsai_challenge_packet(&packet, NOW), Ok(()));
    }

    #[test]
    fn challenge_packet_is_deterministic() {
        assert_eq!(packet(), packet());
    }

    #[test]
    fn ra_2_replayed_challenge_is_rejected() {
        let packet = packet();
        let mut guard = ChallengeReplayGuard::new();

        assert_eq!(guard.consume(&packet, NOW), Ok(()));
        assert_eq!(
            guard.consume(&packet, NOW),
            Err(ChallengeError::ReplayedChallenge {
                challenge_id: packet.challenge_id,
            })
        );
    }

    #[test]
    fn ra_3_expired_challenge_is_rejected() {
        assert_eq!(
            validate_hsai_challenge_packet(&packet(), EXPIRES_AT + 1),
            Err(ChallengeError::ExpiredChallenge {
                now: EXPIRES_AT + 1,
                expires_at: EXPIRES_AT,
            })
        );
    }

    #[test]
    fn ra_4_wrong_case_hash_is_rejected() {
        let mut packet = packet();
        packet.case_hash_hex.replace_range(0..2, "00");

        assert!(matches!(
            validate_hsai_challenge_packet(&packet, NOW),
            Err(ChallengeError::ReportDataMismatch { .. })
        ));
    }

    #[test]
    fn tampered_challenge_id_is_rejected() {
        let mut packet = packet();
        packet.challenge_id.replace_range(0..2, "00");

        assert!(matches!(
            validate_hsai_challenge_packet(&packet, NOW),
            Err(ChallengeError::ChallengeIdMismatch { .. })
        ));
    }

    #[test]
    fn ra_5_capture_manifest_discloses_managed_verifier_and_forbidden_secrets() {
        let manifest =
            capture_workflow_manifest(packet(), RealArtifactProviderMode::ManagedVerifier);

        assert_eq!(manifest.provider, "phala-dstack");
        assert_eq!(
            manifest.provider_mode,
            RealArtifactProviderMode::ManagedVerifier
        );
        assert!(manifest
            .required_artifact_fields
            .contains(&"trust_root_labels".to_owned()));
        assert!(manifest
            .forbidden_artifact_fields
            .contains(&"private_keys".to_owned()));
        assert!(manifest.claim_boundary.contains("not attestation evidence"));
    }

    #[test]
    fn ra_6_phase4_precondition_fails_without_real_artifact_acceptance() {
        let manifest = capture_workflow_manifest(packet(), RealArtifactProviderMode::LocalQuote);

        assert!(manifest.claim_boundary.contains("Phase 4 authorization"));
        assert!(!manifest
            .required_artifact_fields
            .contains(&"agent_anchor_registry".to_owned()));
    }
}

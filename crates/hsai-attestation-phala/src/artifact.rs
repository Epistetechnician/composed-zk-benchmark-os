//! Captured Phala/dstack Trust Center artifact validation.
//!
//! State slice: `agent-identity-end-to-end-verification-hardening-v1`.
//!
//! This module validates a public captured artifact only after an explicit
//! quote verifier authenticates the complete quote. The default entry point is
//! fail-closed and does not perform network calls or invent provider trust.

use crate::challenge::agent_case_hash;
use hsai_agent_case::{AgentCase, EvidenceLane};
use hsai_attestation::report_data_binding;
use hsai_claim_envelope::{ClaimEnvelope, LaneId, Maturity, TimeWindow, TrustRoot, VendorId};
use hsai_distinct_agent::Anchor;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256, Sha384};
use std::collections::BTreeSet;

const REPORT_DATA_HEX_LEN: usize = 128;
const HSAI_OWNED_REPORT_DATA_HEX_LEN: usize = 64;
const HASH256_HEX_LEN: usize = 64;
const RTMR_HEX_LEN: usize = 96;

/// Captured Phala/dstack Trust Center artifact bundle.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PhalaArtifactBundle {
    pub source_url: String,
    pub observed_timestamp: u64,
    pub completed_at: String,
    pub anchor_id: String,
    pub agent_public_key_spki_hex: String,
    pub nonce_hex: String,
    pub case_hash_hex: String,
    pub quote_hex: String,
    pub report_data_hex: String,
    pub app_compose_json: String,
    pub compose_hash: String,
    pub app_id: String,
    pub instance_id: String,
    pub device_id: String,
    pub os_image_hash: String,
    pub mr_aggregated: String,
    pub rtmrs: RtmrSet,
    pub rtmr3_event_log: Vec<DstackEvent>,
    pub docker_image_digests: Vec<String>,
    pub verifier_mode: ManagedVerifierMode,
}

/// Captured RTMR values from the Phala/dstack artifact.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct RtmrSet {
    pub rtmr0: String,
    pub rtmr1: String,
    pub rtmr2: String,
    pub rtmr3: String,
}

/// Captured dstack event-log entry.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct DstackEvent {
    pub imr: u8,
    pub event_type: u64,
    pub digest: String,
    pub event: String,
    pub event_payload: String,
}

/// Managed verifier metadata captured with the artifact.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ManagedVerifierMode {
    pub kind: String,
    pub service_url: String,
    pub artifact_url: String,
    pub intel_trust_authority_issuer: String,
    pub verification_status: String,
    pub tcb_status: Option<String>,
}

/// The authenticated quote backend used by the artifact lane.
///
/// Implementations must parse and authenticate the complete quote against the
/// configured TDX/DCAP trust roots and verify that its report-data field equals
/// `expected_report_data`. A substring check is intentionally not a valid
/// implementation of this trait.
pub trait PhalaQuoteVerifier {
    fn verify_quote(
        &self,
        quote: &[u8],
        expected_report_data: &[u8],
    ) -> Result<VerifiedPhalaQuote, PhalaQuoteVerificationError>;
}

/// Authenticated output from a [`PhalaQuoteVerifier`].
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct VerifiedPhalaQuote {
    /// Report-data bytes extracted from the authenticated quote body.
    pub report_data: Vec<u8>,
    /// Provider and/or hardware roots used to authenticate the quote.
    pub trust_roots: BTreeSet<TrustRoot>,
}

/// Why a quote backend refused to authenticate a quote.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum PhalaQuoteVerificationError {
    Unavailable,
    Invalid,
}

struct RejectingPhalaQuoteVerifier;

impl PhalaQuoteVerifier for RejectingPhalaQuoteVerifier {
    fn verify_quote(
        &self,
        _quote: &[u8],
        _expected_report_data: &[u8],
    ) -> Result<VerifiedPhalaQuote, PhalaQuoteVerificationError> {
        Err(PhalaQuoteVerificationError::Unavailable)
    }
}

/// Local validation policy for a captured Phala artifact.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PhalaValidationPolicy {
    pub expected_anchor_id: String,
    pub expected_report_data_hex: String,
    pub expected_compose_hash: String,
    pub expected_app_id: String,
    pub expected_instance_id: String,
    pub max_age_seconds: u64,
    pub required_docker_image_digests: BTreeSet<String>,
}

impl PhalaValidationPolicy {
    pub fn for_bundle(bundle: &PhalaArtifactBundle, max_age_seconds: u64) -> Self {
        Self {
            expected_anchor_id: bundle.anchor_id.clone(),
            expected_report_data_hex: bundle.report_data_hex.clone(),
            expected_compose_hash: bundle.compose_hash.clone(),
            expected_app_id: bundle.app_id.clone(),
            expected_instance_id: bundle.instance_id.clone(),
            max_age_seconds,
            required_docker_image_digests: bundle
                .docker_image_digests
                .iter()
                .cloned()
                .collect::<BTreeSet<_>>(),
        }
    }
}

/// Result of local validation over a captured Phala artifact.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ValidatedPhalaAttestation {
    pub anchor_id: String,
    pub report_data_hex: String,
    pub compose_hash: String,
    pub valid: TimeWindow,
    pub trust_roots: BTreeSet<TrustRoot>,
}

/// Validation errors for captured artifact mode.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum PhalaValidationError {
    InvalidJson(String),
    InvalidHex {
        field: String,
        value: String,
    },
    InvalidHexLength {
        field: String,
        actual: usize,
        expected: usize,
    },
    AnchorMismatch {
        actual: String,
        expected: String,
    },
    ReportDataMismatch {
        actual: String,
        expected: String,
    },
    ReportDataBindingMismatch,
    CaseHashMismatch {
        actual: String,
        expected: String,
    },
    /// The quote was not parsed and authenticated by an explicit verifier.
    QuoteUnverified,
    QuoteReportDataMissing,
    ComposeHashMismatch {
        actual: String,
        expected: String,
    },
    RtmrReplayMismatch {
        actual: String,
        expected: String,
    },
    MissingEvent(String),
    EventPayloadMismatch {
        event: String,
        actual: String,
        expected: String,
    },
    Stale {
        observed: u64,
        now: u64,
        max_age_seconds: u64,
    },
    ObservationInFuture {
        observed: u64,
        now: u64,
    },
    MissingDockerDigest(String),
    ManagedVerifierUntrusted(String),
}

impl std::fmt::Display for PhalaValidationError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{self:?}")
    }
}

impl std::error::Error for PhalaValidationError {}

/// Parse a captured Phala/dstack artifact bundle from JSON.
pub fn parse_phala_artifact(json: &str) -> Result<PhalaArtifactBundle, PhalaValidationError> {
    serde_json::from_str(json).map_err(|err| PhalaValidationError::InvalidJson(err.to_string()))
}

/// Validate a captured Phala/dstack artifact without a quote backend.
///
/// This entry point intentionally fails closed with [`PhalaValidationError::QuoteUnverified`].
/// Call [`validate_phala_artifact_with_quote_verifier`] only after wiring an
/// implementation that authenticates the provider quote and trust chain.
pub fn validate_phala_artifact(
    bundle: &PhalaArtifactBundle,
    policy: &PhalaValidationPolicy,
    now: u64,
) -> Result<ValidatedPhalaAttestation, PhalaValidationError> {
    validate_phala_artifact_with_quote_verifier(bundle, policy, now, &RejectingPhalaQuoteVerifier)
}

/// Validate an artifact with an explicit authenticated quote backend.
///
/// Structural checks run before the quote backend so malformed artifacts keep
/// precise failure causes. A successful result is possible only after the
/// backend has authenticated the complete quote and its report-data field.
pub fn validate_phala_artifact_with_quote_verifier<V: PhalaQuoteVerifier>(
    bundle: &PhalaArtifactBundle,
    policy: &PhalaValidationPolicy,
    now: u64,
    quote_verifier: &V,
) -> Result<ValidatedPhalaAttestation, PhalaValidationError> {
    let expected_anchor_id = policy.expected_anchor_id.clone();
    if bundle.anchor_id != expected_anchor_id {
        return Err(PhalaValidationError::AnchorMismatch {
            actual: bundle.anchor_id.clone(),
            expected: expected_anchor_id,
        });
    }

    validate_managed_verifier(&bundle.verifier_mode)?;
    validate_freshness(bundle.observed_timestamp, now, policy.max_age_seconds)?;

    let quote_hex = normalize_hex("quote_hex", &bundle.quote_hex, None)?;
    let report_data = normalize_hex("report_data_hex", &bundle.report_data_hex, None)?;
    let expected_report_data = normalize_hex(
        "expected_report_data_hex",
        &policy.expected_report_data_hex,
        None,
    )?;
    let nonce_hex = normalize_hex("nonce_hex", &bundle.nonce_hex, None)?;
    let case_hash = normalize_hex(
        "case_hash_hex",
        &bundle.case_hash_hex,
        Some(HASH256_HEX_LEN),
    )?;
    let agent_pubkey_hex = normalize_hex(
        "agent_public_key_spki_hex",
        &bundle.agent_public_key_spki_hex,
        None,
    )?;

    if report_data != expected_report_data {
        return Err(PhalaValidationError::ReportDataMismatch {
            actual: report_data,
            expected: expected_report_data,
        });
    }
    validate_report_data_binding(
        &expected_report_data,
        &nonce_hex,
        &case_hash,
        &agent_pubkey_hex,
    )?;
    let compose_hash = normalize_hex("compose_hash", &bundle.compose_hash, Some(HASH256_HEX_LEN))?;
    let expected_compose_hash = normalize_hex(
        "expected_compose_hash",
        &policy.expected_compose_hash,
        Some(HASH256_HEX_LEN),
    )?;
    let calculated_compose_hash = sha256_hex(bundle.app_compose_json.as_bytes());
    if compose_hash != expected_compose_hash {
        return Err(PhalaValidationError::ComposeHashMismatch {
            actual: compose_hash,
            expected: expected_compose_hash,
        });
    }
    if calculated_compose_hash != expected_compose_hash {
        return Err(PhalaValidationError::ComposeHashMismatch {
            actual: calculated_compose_hash,
            expected: expected_compose_hash,
        });
    }

    validate_static_fields(bundle, policy, &compose_hash)?;
    validate_rtmrs(bundle)?;
    validate_required_docker_digests(bundle, policy)?;

    let quote = decode_hex("quote_hex", &quote_hex, None)?;
    let expected_report_data_bytes = decode_hex("report_data_hex", &expected_report_data, None)?;
    let verified_quote = quote_verifier
        .verify_quote(&quote, &expected_report_data_bytes)
        .map_err(|_| PhalaValidationError::QuoteUnverified)?;
    if verified_quote.report_data != expected_report_data_bytes
        || verified_quote.trust_roots.is_empty()
    {
        return Err(PhalaValidationError::QuoteUnverified);
    }
    let mut trust_roots = managed_trust_roots(bundle, &compose_hash);
    trust_roots.extend(verified_quote.trust_roots);

    Ok(ValidatedPhalaAttestation {
        anchor_id: bundle.anchor_id.clone(),
        report_data_hex: expected_report_data,
        compose_hash: compose_hash.clone(),
        valid: TimeWindow {
            start: bundle.observed_timestamp,
            end: bundle
                .observed_timestamp
                .saturating_add(policy.max_age_seconds),
        },
        trust_roots,
    })
}

/// Validate an authenticated artifact against the exact current agent case.
///
/// The case hash is recomputed from `case`; it is never taken from the
/// artifact or copied into policy by the caller.
pub fn validate_phala_artifact_for_case_with_quote_verifier<V: PhalaQuoteVerifier>(
    bundle: &PhalaArtifactBundle,
    policy: &PhalaValidationPolicy,
    case: &AgentCase,
    quote_verifier: &V,
) -> Result<ValidatedPhalaAttestation, PhalaValidationError> {
    let validated = validate_phala_artifact_with_quote_verifier(
        bundle,
        policy,
        case.observed_at,
        quote_verifier,
    )?;
    let actual = normalize_hex(
        "case_hash_hex",
        &bundle.case_hash_hex,
        Some(HASH256_HEX_LEN),
    )?;
    let expected =
        encode_hex(
            &agent_case_hash(case).map_err(|_| PhalaValidationError::CaseHashMismatch {
                actual: actual.clone(),
                expected: "serializable-agent-case".to_owned(),
            })?,
        );
    if actual != expected {
        return Err(PhalaValidationError::CaseHashMismatch { actual, expected });
    }
    Ok(validated)
}

/// Artifact-specific lane for captured Phala/dstack evidence.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PhalaArtifactAttestationLane {
    pub anchor: Anchor,
    pub artifact: PhalaArtifactBundle,
    pub policy: PhalaValidationPolicy,
}

impl PhalaArtifactAttestationLane {
    pub fn new(
        anchor: Anchor,
        artifact: PhalaArtifactBundle,
        policy: PhalaValidationPolicy,
    ) -> Self {
        Self {
            anchor,
            artifact,
            policy,
        }
    }

    /// Evaluate using an explicit quote parser/authenticator.
    pub fn evaluate_with_quote_verifier<V: PhalaQuoteVerifier>(
        &self,
        case: &AgentCase,
        quote_verifier: &V,
    ) -> ClaimEnvelope {
        match validate_phala_artifact_for_case_with_quote_verifier(
            &self.artifact,
            &self.policy,
            case,
            quote_verifier,
        ) {
            Ok(validated) if validated.anchor_id == self.anchor.anchor_id() => {
                let mut trust_roots = validated.trust_roots;
                trust_roots.insert(self.anchor.trust_root());

                ClaimEnvelope::new(
                    BTreeSet::from([self.anchor.validity_assumption(&case.subject)]),
                    BTreeSet::new(),
                    case.oracle.excluded.clone(),
                    Maturity::Attested,
                    trust_roots,
                    validated.valid,
                    self.id(),
                )
            }
            _ => stub_envelope(case, self.id()),
        }
    }
}

impl EvidenceLane for PhalaArtifactAttestationLane {
    fn id(&self) -> LaneId {
        LaneId::Named("attestation-phala-artifact".to_owned())
    }

    fn ceiling(&self) -> Maturity {
        Maturity::Attested
    }

    fn evaluate(&self, case: &AgentCase) -> ClaimEnvelope {
        self.evaluate_with_quote_verifier(case, &RejectingPhalaQuoteVerifier)
    }
}

fn stub_envelope(case: &AgentCase, lane: LaneId) -> ClaimEnvelope {
    ClaimEnvelope::new(
        BTreeSet::new(),
        BTreeSet::new(),
        case.oracle.excluded.clone(),
        Maturity::Stub,
        BTreeSet::new(),
        TimeWindow::all(),
        lane,
    )
}

fn validate_managed_verifier(mode: &ManagedVerifierMode) -> Result<(), PhalaValidationError> {
    if mode.kind != "managed_phala_trust_center" {
        return Err(PhalaValidationError::ManagedVerifierUntrusted(
            mode.kind.clone(),
        ));
    }
    if mode.service_url != "https://trust.phala.com" {
        return Err(PhalaValidationError::ManagedVerifierUntrusted(
            mode.service_url.clone(),
        ));
    }
    if mode.intel_trust_authority_issuer != "https://portal.trustauthority.intel.com" {
        return Err(PhalaValidationError::ManagedVerifierUntrusted(
            mode.intel_trust_authority_issuer.clone(),
        ));
    }
    if mode.verification_status != "UpToDate" {
        return Err(PhalaValidationError::ManagedVerifierUntrusted(
            mode.verification_status.clone(),
        ));
    }
    Ok(())
}

/// Validate the report-data binding against either the Phase 3 captured-artifact
/// format (128 hex chars: `nonce_hex || case_hash_hex || ...`) or the Phase 57
/// HSAI-owned format (64 hex chars: SHA-256 over the agent pubkey, nonce, and
/// case hash via `report_data_binding`).
fn validate_report_data_binding(
    expected_report_data_hex: &str,
    nonce_hex: &str,
    case_hash_hex: &str,
    agent_pubkey_spki_hex: &str,
) -> Result<(), PhalaValidationError> {
    match expected_report_data_hex.len() {
        HSAI_OWNED_REPORT_DATA_HEX_LEN => {
            // Phase 57 HSAI-owned binding: recompute the shipped digest.
            let agent_pubkey =
                decode_hex("agent_public_key_spki_hex", agent_pubkey_spki_hex, None)?;
            let case_hash = decode_hex("case_hash_hex", case_hash_hex, Some(HASH256_HEX_LEN))?;
            let nonce_bytes = decode_hex("nonce_hex", nonce_hex, None)?;
            if nonce_bytes.len() > 8 {
                return Err(PhalaValidationError::ReportDataBindingMismatch);
            }
            let mut nonce_padded = [0u8; 8];
            nonce_padded[8 - nonce_bytes.len()..].copy_from_slice(&nonce_bytes);
            let nonce = u64::from_be_bytes(nonce_padded);
            let recomputed = encode_hex(&report_data_binding(&agent_pubkey, nonce, &case_hash));
            if recomputed == expected_report_data_hex {
                Ok(())
            } else {
                Err(PhalaValidationError::ReportDataBindingMismatch)
            }
        }
        REPORT_DATA_HEX_LEN => {
            // Phase 3 captured-artifact binding: literal prefix.
            if expected_report_data_hex.starts_with(&format!("{nonce_hex}{case_hash_hex}")) {
                Ok(())
            } else {
                Err(PhalaValidationError::ReportDataBindingMismatch)
            }
        }
        _ => Err(PhalaValidationError::InvalidHexLength {
            field: "expected_report_data_hex".to_owned(),
            actual: expected_report_data_hex.len(),
            expected: HSAI_OWNED_REPORT_DATA_HEX_LEN,
        }),
    }
}

fn validate_freshness(
    observed: u64,
    now: u64,
    max_age_seconds: u64,
) -> Result<(), PhalaValidationError> {
    if now < observed {
        return Err(PhalaValidationError::ObservationInFuture { observed, now });
    }
    if now.saturating_sub(observed) > max_age_seconds {
        return Err(PhalaValidationError::Stale {
            observed,
            now,
            max_age_seconds,
        });
    }
    Ok(())
}

fn validate_static_fields(
    bundle: &PhalaArtifactBundle,
    policy: &PhalaValidationPolicy,
    compose_hash: &str,
) -> Result<(), PhalaValidationError> {
    let app_id = normalize_hex("app_id", &bundle.app_id, Some(40))?;
    let instance_id = normalize_hex("instance_id", &bundle.instance_id, Some(40))?;
    // device_id is informational on real TDX hardware (processor/moniker) and
    // is not part of any binding check; accept any hex length or empty.
    if !bundle.device_id.is_empty() {
        normalize_hex("device_id", &bundle.device_id, None)?;
    }
    let os_image_hash = normalize_hex(
        "os_image_hash",
        &bundle.os_image_hash,
        Some(HASH256_HEX_LEN),
    )?;
    normalize_hex("mr_aggregated", &bundle.mr_aggregated, None)?;
    // mr_aggregated is a SHA-384 digest on real TDX hardware (96 hex chars).
    // Synthetic Phase 3 fixtures may use a 32-byte (64 hex char) placeholder;
    // accept either length.

    let expected_app_id = normalize_hex("expected_app_id", &policy.expected_app_id, Some(40))?;
    if app_id != expected_app_id {
        return Err(PhalaValidationError::EventPayloadMismatch {
            event: "app-id".to_owned(),
            actual: app_id,
            expected: expected_app_id,
        });
    }

    let expected_instance_id = normalize_hex(
        "expected_instance_id",
        &policy.expected_instance_id,
        Some(40),
    )?;
    if instance_id != expected_instance_id {
        return Err(PhalaValidationError::EventPayloadMismatch {
            event: "instance-id".to_owned(),
            actual: instance_id,
            expected: expected_instance_id,
        });
    }

    assert_event_payload(bundle, "app-id", &app_id)?;
    assert_event_payload(bundle, "compose-hash", compose_hash)?;
    assert_event_payload(bundle, "instance-id", &instance_id)?;
    assert_event_payload(bundle, "os-image-hash", &os_image_hash)?;

    Ok(())
}

fn validate_rtmrs(bundle: &PhalaArtifactBundle) -> Result<(), PhalaValidationError> {
    normalize_hex("rtmr0", &bundle.rtmrs.rtmr0, Some(RTMR_HEX_LEN))?;
    normalize_hex("rtmr1", &bundle.rtmrs.rtmr1, Some(RTMR_HEX_LEN))?;
    normalize_hex("rtmr2", &bundle.rtmrs.rtmr2, Some(RTMR_HEX_LEN))?;
    let expected_rtmr3 = normalize_hex("rtmr3", &bundle.rtmrs.rtmr3, Some(RTMR_HEX_LEN))?;

    let mut current = vec![0_u8; 48];
    for event in &bundle.rtmr3_event_log {
        if event.imr != 3 {
            return Err(PhalaValidationError::RtmrReplayMismatch {
                actual: event.imr.to_string(),
                expected: "3".to_owned(),
            });
        }
        let digest = decode_hex("rtmr3_event.digest", &event.digest, Some(RTMR_HEX_LEN))?;
        let mut hasher = Sha384::new();
        hasher.update(&current);
        hasher.update(&digest);
        current = hasher.finalize().to_vec();
    }

    let replayed = encode_hex(&current);
    if replayed != expected_rtmr3 {
        return Err(PhalaValidationError::RtmrReplayMismatch {
            actual: replayed,
            expected: expected_rtmr3,
        });
    }
    Ok(())
}

fn validate_required_docker_digests(
    bundle: &PhalaArtifactBundle,
    policy: &PhalaValidationPolicy,
) -> Result<(), PhalaValidationError> {
    let captured = bundle
        .docker_image_digests
        .iter()
        .map(|digest| normalize_digest(digest))
        .collect::<Result<BTreeSet<_>, _>>()?;

    for digest in &captured {
        if !bundle.app_compose_json.contains(digest) {
            return Err(PhalaValidationError::MissingDockerDigest(digest.clone()));
        }
    }

    for required in &policy.required_docker_image_digests {
        let required = normalize_digest(required)?;
        if !captured.contains(&required) {
            return Err(PhalaValidationError::MissingDockerDigest(required));
        }
    }

    Ok(())
}

fn assert_event_payload(
    bundle: &PhalaArtifactBundle,
    event_name: &str,
    expected: &str,
) -> Result<(), PhalaValidationError> {
    let event = bundle
        .rtmr3_event_log
        .iter()
        .find(|event| event.event == event_name)
        .ok_or_else(|| PhalaValidationError::MissingEvent(event_name.to_owned()))?;
    let actual = normalize_hex(
        &format!("rtmr3_event.{event_name}.event_payload"),
        &event.event_payload,
        Some(expected.len()),
    )?;
    if actual != expected {
        return Err(PhalaValidationError::EventPayloadMismatch {
            event: event_name.to_owned(),
            actual,
            expected: expected.to_owned(),
        });
    }
    Ok(())
}

fn managed_trust_roots(bundle: &PhalaArtifactBundle, compose_hash: &str) -> BTreeSet<TrustRoot> {
    BTreeSet::from([
        vendor_root("managed:phala-trust-center"),
        vendor_root("managed:intel-trust-authority"),
        vendor_root(format!("dstack-os:{}", bundle.os_image_hash)),
        vendor_root(format!("compose:{compose_hash}")),
    ])
}

fn vendor_root(id: impl Into<String>) -> TrustRoot {
    TrustRoot::HardwareVendor(VendorId(id.into()))
}

fn normalize_digest(digest: &str) -> Result<String, PhalaValidationError> {
    let digest = digest.to_ascii_lowercase();
    let Some(rest) = digest.strip_prefix("sha256:") else {
        return Err(PhalaValidationError::InvalidHex {
            field: "docker_image_digest".to_owned(),
            value: digest,
        });
    };
    normalize_hex("docker_image_digest", rest, Some(HASH256_HEX_LEN))?;
    Ok(format!("sha256:{rest}"))
}

fn normalize_hex(
    field: &str,
    value: &str,
    expected_len: Option<usize>,
) -> Result<String, PhalaValidationError> {
    let value = value
        .strip_prefix("0x")
        .unwrap_or(value)
        .to_ascii_lowercase();
    if let Some(expected) = expected_len {
        if value.len() != expected {
            return Err(PhalaValidationError::InvalidHexLength {
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
        return Err(PhalaValidationError::InvalidHex {
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
) -> Result<Vec<u8>, PhalaValidationError> {
    let value = normalize_hex(field, value, expected_len)?;
    (0..value.len())
        .step_by(2)
        .map(|index| {
            u8::from_str_radix(&value[index..index + 2], 16).map_err(|_| {
                PhalaValidationError::InvalidHex {
                    field: field.to_owned(),
                    value: value.clone(),
                }
            })
        })
        .collect()
}

fn sha256_hex(bytes: &[u8]) -> String {
    encode_hex(&Sha256::digest(bytes))
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

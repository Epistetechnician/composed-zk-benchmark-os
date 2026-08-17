//! Pure-data contract for the synthetic `OpaqueTraceReplay` mutation family.
//!
//! State slice: `research-synthesis-trace-replay-v1-benchmark-adapter-contract`.
//!
//! This module owns semantic mutation metadata, the expected-verdict oracle,
//! provenance, quarantine status, and claim ceilings. It does not retain an
//! opaque payload, call a provider, execute a model, or grant authority.

use serde::{Deserialize, Serialize};

use crate::error::Result;
use crate::evidence::{
    compute_artifact_digest, compute_artifact_digest_bytes, ArtifactDigest,
    ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole, BackendOutcome, ClaimBoundary,
    ExpectedVerdict,
};
use crate::external_runner::QuarantineStatus;
use crate::ids::is_non_empty_id;

/// Stable family identifier for synthetic opaque-trace replay cases.
pub const OPAQUE_TRACE_REPLAY_FAMILY_ID: &str = "OpaqueTraceReplay";

/// Versioned schema identifier for the pure-data contract.
pub const OPAQUE_TRACE_REPLAY_SCHEMA_VERSION: &str = "opaque-trace-replay-v1";

/// Maximum claim boundary emitted by this contract.
pub const OPAQUE_TRACE_REPLAY_CLAIM_BOUNDARY: ClaimBoundary = ClaimBoundary::Level0DesignNote;

/// Synthetic mutation variants covered by the contract.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum OpaqueTraceReplayVariant {
    /// Correct context, predecessor, nonce, and order.
    #[serde(rename = "valid_same_session")]
    ValidSameSession,
    /// User binding differs from the expected user.
    #[serde(rename = "wrong_user_replay")]
    WrongUserReplay,
    /// Session binding differs from the expected session.
    #[serde(rename = "wrong_session_replay")]
    WrongSessionReplay,
    /// Model/version binding differs from the expected model.
    #[serde(rename = "wrong_model_replay")]
    WrongModelReplay,
    /// Predecessor or sequence order is not the expected order.
    #[serde(rename = "out_of_order_block")]
    OutOfOrderBlock,
    /// The nonce has already been consumed.
    #[serde(rename = "duplicate_block")]
    DuplicateBlock,
    /// The candidate is stale or explicitly revoked.
    #[serde(rename = "stale_or_revoked_block")]
    StaleOrRevokedBlock,
    /// The synthetic opaque payload carries an injection marker.
    #[serde(rename = "hidden_injection")]
    HiddenInjection,
    /// The candidate declares a private synthetic sentinel without retaining it.
    #[serde(rename = "secret_bearing_transcript")]
    SecretBearingTranscript,
    /// The envelope is intentionally malformed.
    #[serde(rename = "malformed_envelope")]
    MalformedEnvelope,
}

impl OpaqueTraceReplayVariant {
    /// All variants in stable contract order.
    pub const ALL: [Self; 10] = [
        Self::ValidSameSession,
        Self::WrongUserReplay,
        Self::WrongSessionReplay,
        Self::WrongModelReplay,
        Self::OutOfOrderBlock,
        Self::DuplicateBlock,
        Self::StaleOrRevokedBlock,
        Self::HiddenInjection,
        Self::SecretBearingTranscript,
        Self::MalformedEnvelope,
    ];
}

/// Synthetic public/private boundary label.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum OpaqueTraceReplayBoundary {
    /// Only public synthetic metadata is represented.
    #[serde(rename = "public_synthetic")]
    PublicSynthetic,
    /// A private-looking value is represented only by a synthetic sentinel flag.
    #[serde(rename = "private_synthetic_sentinel")]
    PrivateSyntheticSentinel,
}

/// Context and ordering values used by the semantic oracle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OpaqueTraceReplayContextBinding {
    /// Expected user binding.
    pub expected_user_id: String,
    /// Candidate-provided user binding.
    pub observed_user_id: String,
    /// Expected session binding.
    pub expected_session_id: String,
    /// Candidate-provided session binding.
    pub observed_session_id: String,
    /// Expected model/version binding.
    pub expected_model_version: String,
    /// Candidate-provided model/version binding.
    pub observed_model_version: String,
    /// Expected predecessor digest.
    #[serde(default)]
    pub expected_predecessor_digest: Option<ArtifactDigest>,
    /// Candidate-provided predecessor digest.
    #[serde(default)]
    pub observed_predecessor_digest: Option<ArtifactDigest>,
    /// Expected block sequence number.
    pub expected_sequence_number: u64,
    /// Candidate-provided block sequence number.
    pub observed_sequence_number: u64,
}

/// Mutation provenance without retaining any opaque payload.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OpaqueTraceReplayMutationProvenance {
    /// Source semantic case digest.
    pub source_case_digest: ArtifactDigest,
    /// Stable mutation identifier.
    pub mutation_id: String,
    /// Declared variant copied from the semantic mutation.
    pub variant: OpaqueTraceReplayVariant,
}

/// Typed synthetic candidate. No raw trace or payload field exists by design.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OpaqueTraceReplayCandidate {
    /// Family identifier.
    pub family_id: String,
    /// Contract schema version.
    pub schema_version: String,
    /// Stable case identifier.
    pub case_id: String,
    /// Mutation provenance.
    pub mutation_provenance: OpaqueTraceReplayMutationProvenance,
    /// Mutation variant.
    pub variant: OpaqueTraceReplayVariant,
    /// Public/private boundary label.
    pub public_private_boundary: OpaqueTraceReplayBoundary,
    /// Digest of the opaque artifact representation.
    pub artifact_digest: ArtifactDigest,
    /// Bound context and ordering values.
    pub context: OpaqueTraceReplayContextBinding,
    /// Nonce presented by the candidate.
    pub observed_nonce: String,
    /// Whether the nonce has already been consumed.
    pub nonce_consumed: bool,
    /// Issuance time supplied by the caller, in epoch seconds.
    pub issued_at_epoch_seconds: u64,
    /// Expiry time supplied by the caller, in epoch seconds.
    pub expires_at_epoch_seconds: u64,
    /// Provider-side revocation marker represented as local metadata.
    pub revoked: bool,
    /// Synthetic injection marker; no instruction text is retained.
    pub injection_marker_present: bool,
    /// Synthetic secret marker; no secret value is retained.
    pub synthetic_secret_sentinel_present: bool,
    /// Hard-coded false retention guard.
    pub raw_payload_retained: bool,
    /// Maximum claim boundary for this candidate.
    pub claim_boundary: ClaimBoundary,
}

impl OpaqueTraceReplayCandidate {
    /// Compute a deterministic digest over the typed candidate metadata.
    pub fn digest(&self) -> Result<ArtifactDigest> {
        compute_artifact_digest(self, Some(ArtifactKind::Other), Some(ArtifactRole::Input))
    }
}

/// Case envelope pairing a candidate with oracle-owned expectations.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OpaqueTraceReplayCase {
    /// Typed candidate metadata.
    pub candidate: OpaqueTraceReplayCandidate,
    /// Expected semantic verdict produced by the oracle.
    pub expected_verdict: ExpectedVerdict,
    /// Expected quarantine result produced by the oracle.
    pub expected_quarantine_status: QuarantineStatus,
}

/// Adapter observations are not authority transitions.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum OpaqueTraceReplayAdapterObservation {
    /// The backend accepted the typed candidate.
    Accepted,
    /// The backend rejected the typed candidate.
    Rejected,
    /// The candidate was quarantined.
    Quarantined,
    /// The candidate was malformed.
    Malformed,
    /// No backend observation was produced.
    NotRun,
}

/// Adapter result metadata with an explicit no-authority field.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OpaqueTraceReplayAdapterResult {
    /// Digest of the typed candidate observed by the adapter.
    pub candidate_digest: ArtifactDigest,
    /// Adapter observation only.
    pub observation: OpaqueTraceReplayAdapterObservation,
    /// Normalized backend outcome, when one exists.
    pub backend_outcome: BackendOutcome,
    /// Quarantine status associated with the observation.
    pub quarantine_status: QuarantineStatus,
    /// Claim boundary carried by the result.
    pub claim_boundary: ClaimBoundary,
    /// Must remain false; this contract cannot authorize state.
    pub authority_granted: bool,
}

/// Validation issue kind for candidates and adapter results.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum OpaqueTraceReplayValidationIssueKind {
    /// Required identifier is empty.
    EmptyIdentifier,
    /// Family or schema does not match the contract.
    ContractMismatch,
    /// Digest is absent or malformed.
    InvalidDigest,
    /// Claim boundary is too high.
    ClaimBoundaryTooHigh,
    /// Raw payload retention was declared.
    RawPayloadRetained,
    /// Variant provenance does not match the candidate.
    ProvenanceMismatch,
    /// Candidate does not match its declared mutation.
    MutationMismatch,
    /// Adapter attempted to grant authority.
    AuthorityGranted,
    /// Adapter observed an outcome inconsistent with the oracle.
    UnexpectedObservation,
    /// Adapter result does not bind the candidate digest.
    CandidateDigestMismatch,
}

/// One deterministic validation issue.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OpaqueTraceReplayValidationIssue {
    /// Issue kind.
    pub kind: OpaqueTraceReplayValidationIssueKind,
    /// Field path.
    pub path: String,
    /// Human-readable reason.
    pub message: String,
}

/// Validation result for the pure-data contract.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OpaqueTraceReplayValidation {
    /// True when no issues were found.
    pub valid: bool,
    /// Deterministic issue list.
    pub issues: Vec<OpaqueTraceReplayValidationIssue>,
}

/// Return the oracle-owned expected verdict for a mutation variant.
pub fn expected_opaque_trace_replay_verdict(variant: OpaqueTraceReplayVariant) -> ExpectedVerdict {
    match variant {
        OpaqueTraceReplayVariant::ValidSameSession => ExpectedVerdict::Accept,
        OpaqueTraceReplayVariant::WrongUserReplay
        | OpaqueTraceReplayVariant::WrongSessionReplay
        | OpaqueTraceReplayVariant::WrongModelReplay
        | OpaqueTraceReplayVariant::OutOfOrderBlock
        | OpaqueTraceReplayVariant::DuplicateBlock
        | OpaqueTraceReplayVariant::StaleOrRevokedBlock
        | OpaqueTraceReplayVariant::HiddenInjection
        | OpaqueTraceReplayVariant::SecretBearingTranscript => ExpectedVerdict::Reject,
        OpaqueTraceReplayVariant::MalformedEnvelope => ExpectedVerdict::BackendError,
    }
}

/// Return the oracle-owned quarantine status for a mutation variant.
pub fn expected_opaque_trace_replay_quarantine_status(
    variant: OpaqueTraceReplayVariant,
) -> QuarantineStatus {
    match variant {
        OpaqueTraceReplayVariant::ValidSameSession => QuarantineStatus::PendingReview,
        OpaqueTraceReplayVariant::OutOfOrderBlock
        | OpaqueTraceReplayVariant::DuplicateBlock
        | OpaqueTraceReplayVariant::MalformedEnvelope => QuarantineStatus::Rejected,
        OpaqueTraceReplayVariant::WrongUserReplay
        | OpaqueTraceReplayVariant::WrongSessionReplay
        | OpaqueTraceReplayVariant::WrongModelReplay
        | OpaqueTraceReplayVariant::StaleOrRevokedBlock
        | OpaqueTraceReplayVariant::HiddenInjection
        | OpaqueTraceReplayVariant::SecretBearingTranscript => QuarantineStatus::Quarantined,
    }
}

/// Build a deterministic synthetic case for each declared variant.
pub fn build_opaque_trace_replay_case(variant: OpaqueTraceReplayVariant) -> OpaqueTraceReplayCase {
    let predecessor = synthetic_digest("predecessor", ArtifactRole::Manifest);
    let mut context = OpaqueTraceReplayContextBinding {
        expected_user_id: "synthetic-user-1".to_string(),
        observed_user_id: "synthetic-user-1".to_string(),
        expected_session_id: "synthetic-session-1".to_string(),
        observed_session_id: "synthetic-session-1".to_string(),
        expected_model_version: "synthetic-model-1".to_string(),
        observed_model_version: "synthetic-model-1".to_string(),
        expected_predecessor_digest: Some(predecessor.clone()),
        observed_predecessor_digest: Some(predecessor),
        expected_sequence_number: 1,
        observed_sequence_number: 1,
    };
    let mut observed_nonce = "synthetic-nonce-1".to_string();
    let mut nonce_consumed = false;
    let mut issued_at_epoch_seconds = 90;
    let mut expires_at_epoch_seconds = 110;
    let mut revoked = false;
    let mut injection_marker_present = false;
    let mut synthetic_secret_sentinel_present = false;
    let mut boundary = OpaqueTraceReplayBoundary::PublicSynthetic;
    let mut schema_version = OPAQUE_TRACE_REPLAY_SCHEMA_VERSION.to_string();
    let mut artifact_digest = synthetic_digest("opaque-artifact", ArtifactRole::Input);

    match variant {
        OpaqueTraceReplayVariant::ValidSameSession => {}
        OpaqueTraceReplayVariant::WrongUserReplay => {
            context.observed_user_id = "synthetic-user-2".to_string();
        }
        OpaqueTraceReplayVariant::WrongSessionReplay => {
            context.observed_session_id = "synthetic-session-2".to_string();
        }
        OpaqueTraceReplayVariant::WrongModelReplay => {
            context.observed_model_version = "synthetic-model-2".to_string();
        }
        OpaqueTraceReplayVariant::OutOfOrderBlock => {
            context.observed_predecessor_digest = Some(synthetic_digest(
                "wrong-predecessor",
                ArtifactRole::Manifest,
            ));
            context.observed_sequence_number = 2;
        }
        OpaqueTraceReplayVariant::DuplicateBlock => nonce_consumed = true,
        OpaqueTraceReplayVariant::StaleOrRevokedBlock => {
            expires_at_epoch_seconds = 99;
            revoked = true;
        }
        OpaqueTraceReplayVariant::HiddenInjection => injection_marker_present = true,
        OpaqueTraceReplayVariant::SecretBearingTranscript => {
            boundary = OpaqueTraceReplayBoundary::PrivateSyntheticSentinel;
            synthetic_secret_sentinel_present = true;
        }
        OpaqueTraceReplayVariant::MalformedEnvelope => {
            schema_version = "opaque-trace-replay-malformed".to_string();
            artifact_digest.hex_digest = "not-a-sha256".to_string();
        }
    }

    if matches!(variant, OpaqueTraceReplayVariant::DuplicateBlock) {
        observed_nonce = "synthetic-nonce-replayed".to_string();
    }
    if matches!(variant, OpaqueTraceReplayVariant::StaleOrRevokedBlock) {
        issued_at_epoch_seconds = 80;
    }

    let candidate = OpaqueTraceReplayCandidate {
        family_id: OPAQUE_TRACE_REPLAY_FAMILY_ID.to_string(),
        schema_version,
        case_id: format!("opaque-trace-replay-{}", variant_name(variant)),
        mutation_provenance: OpaqueTraceReplayMutationProvenance {
            source_case_digest: synthetic_digest("source-case", ArtifactRole::Manifest),
            mutation_id: format!("mutation-{}", variant_name(variant)),
            variant,
        },
        variant,
        public_private_boundary: boundary,
        artifact_digest,
        context,
        observed_nonce,
        nonce_consumed,
        issued_at_epoch_seconds,
        expires_at_epoch_seconds,
        revoked,
        injection_marker_present,
        synthetic_secret_sentinel_present,
        raw_payload_retained: false,
        claim_boundary: OPAQUE_TRACE_REPLAY_CLAIM_BOUNDARY,
    };

    OpaqueTraceReplayCase {
        expected_verdict: expected_opaque_trace_replay_verdict(variant),
        expected_quarantine_status: expected_opaque_trace_replay_quarantine_status(variant),
        candidate,
    }
}

/// Validate a typed candidate at a caller-supplied time.
pub fn validate_opaque_trace_replay_candidate(
    candidate: &OpaqueTraceReplayCandidate,
    now_epoch_seconds: u64,
) -> OpaqueTraceReplayValidation {
    let mut issues = Vec::new();
    let mut require_id = |path: &str, value: &str| {
        if !is_non_empty_id(value) {
            issues.push(issue(
                OpaqueTraceReplayValidationIssueKind::EmptyIdentifier,
                path,
                "required identifier is empty",
            ));
        }
    };

    require_id("family_id", &candidate.family_id);
    require_id("schema_version", &candidate.schema_version);
    require_id("case_id", &candidate.case_id);
    require_id(
        "mutation_provenance.mutation_id",
        &candidate.mutation_provenance.mutation_id,
    );
    require_id(
        "context.expected_user_id",
        &candidate.context.expected_user_id,
    );
    require_id(
        "context.observed_user_id",
        &candidate.context.observed_user_id,
    );
    require_id(
        "context.expected_session_id",
        &candidate.context.expected_session_id,
    );
    require_id(
        "context.observed_session_id",
        &candidate.context.observed_session_id,
    );
    require_id(
        "context.expected_model_version",
        &candidate.context.expected_model_version,
    );
    require_id(
        "context.observed_model_version",
        &candidate.context.observed_model_version,
    );
    require_id("observed_nonce", &candidate.observed_nonce);

    if candidate.family_id != OPAQUE_TRACE_REPLAY_FAMILY_ID
        || candidate.schema_version != OPAQUE_TRACE_REPLAY_SCHEMA_VERSION
    {
        issues.push(issue(
            OpaqueTraceReplayValidationIssueKind::ContractMismatch,
            "candidate",
            "family_id and schema_version must match the frozen contract",
        ));
    }
    if candidate.claim_boundary != OPAQUE_TRACE_REPLAY_CLAIM_BOUNDARY {
        issues.push(issue(
            OpaqueTraceReplayValidationIssueKind::ClaimBoundaryTooHigh,
            "claim_boundary",
            "OpaqueTraceReplay remains a Level0DesignNote contract",
        ));
    }
    if candidate.raw_payload_retained {
        issues.push(issue(
            OpaqueTraceReplayValidationIssueKind::RawPayloadRetained,
            "raw_payload_retained",
            "raw opaque payload retention is forbidden",
        ));
    }
    if candidate.mutation_provenance.variant != candidate.variant {
        issues.push(issue(
            OpaqueTraceReplayValidationIssueKind::ProvenanceMismatch,
            "mutation_provenance.variant",
            "mutation provenance variant must match candidate variant",
        ));
    }
    validate_digest(&mut issues, "artifact_digest", &candidate.artifact_digest);
    validate_digest(
        &mut issues,
        "mutation_provenance.source_case_digest",
        &candidate.mutation_provenance.source_case_digest,
    );
    if let Some(digest) = &candidate.context.expected_predecessor_digest {
        validate_digest(&mut issues, "context.expected_predecessor_digest", digest);
    }
    if let Some(digest) = &candidate.context.observed_predecessor_digest {
        validate_digest(&mut issues, "context.observed_predecessor_digest", digest);
    }
    if candidate.context.expected_sequence_number == 0
        || candidate.context.observed_sequence_number == 0
    {
        issues.push(issue(
            OpaqueTraceReplayValidationIssueKind::MutationMismatch,
            "context.sequence_number",
            "sequence numbers must be positive",
        ));
    }
    if candidate.expires_at_epoch_seconds <= candidate.issued_at_epoch_seconds {
        issues.push(issue(
            OpaqueTraceReplayValidationIssueKind::MutationMismatch,
            "expires_at_epoch_seconds",
            "expiry must be later than issuance",
        ));
    }

    match candidate.variant {
        OpaqueTraceReplayVariant::ValidSameSession => {
            if !context_matches(candidate)
                || candidate.nonce_consumed
                || candidate.revoked
                || candidate.issued_at_epoch_seconds > now_epoch_seconds
                || candidate.expires_at_epoch_seconds <= now_epoch_seconds
                || candidate.injection_marker_present
                || candidate.synthetic_secret_sentinel_present
            {
                mutation_mismatch(&mut issues, "valid_same_session");
            }
        }
        OpaqueTraceReplayVariant::WrongUserReplay => {
            if candidate.context.observed_user_id == candidate.context.expected_user_id {
                mutation_mismatch(&mut issues, "wrong_user_replay");
            }
        }
        OpaqueTraceReplayVariant::WrongSessionReplay => {
            if candidate.context.observed_session_id == candidate.context.expected_session_id {
                mutation_mismatch(&mut issues, "wrong_session_replay");
            }
        }
        OpaqueTraceReplayVariant::WrongModelReplay => {
            if candidate.context.observed_model_version == candidate.context.expected_model_version
            {
                mutation_mismatch(&mut issues, "wrong_model_replay");
            }
        }
        OpaqueTraceReplayVariant::OutOfOrderBlock => {
            if candidate.context.observed_sequence_number
                == candidate.context.expected_sequence_number
                && candidate.context.observed_predecessor_digest
                    == candidate.context.expected_predecessor_digest
            {
                mutation_mismatch(&mut issues, "out_of_order_block");
            }
        }
        OpaqueTraceReplayVariant::DuplicateBlock => {
            if !candidate.nonce_consumed {
                mutation_mismatch(&mut issues, "duplicate_block");
            }
        }
        OpaqueTraceReplayVariant::StaleOrRevokedBlock => {
            if !candidate.revoked && candidate.expires_at_epoch_seconds > now_epoch_seconds {
                mutation_mismatch(&mut issues, "stale_or_revoked_block");
            }
        }
        OpaqueTraceReplayVariant::HiddenInjection => {
            if !candidate.injection_marker_present {
                mutation_mismatch(&mut issues, "hidden_injection");
            }
        }
        OpaqueTraceReplayVariant::SecretBearingTranscript => {
            if candidate.public_private_boundary
                != OpaqueTraceReplayBoundary::PrivateSyntheticSentinel
                || !candidate.synthetic_secret_sentinel_present
            {
                mutation_mismatch(&mut issues, "secret_bearing_transcript");
            }
        }
        OpaqueTraceReplayVariant::MalformedEnvelope => {
            if candidate.schema_version == OPAQUE_TRACE_REPLAY_SCHEMA_VERSION
                && valid_digest(&candidate.artifact_digest)
            {
                mutation_mismatch(&mut issues, "malformed_envelope");
            }
        }
    }

    OpaqueTraceReplayValidation {
        valid: issues.is_empty(),
        issues,
    }
}

/// Validate an adapter observation without granting authority.
pub fn validate_opaque_trace_replay_adapter_result(
    case: &OpaqueTraceReplayCase,
    result: &OpaqueTraceReplayAdapterResult,
) -> OpaqueTraceReplayValidation {
    let mut issues = Vec::new();
    let oracle_verdict = expected_opaque_trace_replay_verdict(case.candidate.variant);
    let oracle_quarantine = expected_opaque_trace_replay_quarantine_status(case.candidate.variant);
    if case.expected_verdict != oracle_verdict {
        issues.push(issue(
            OpaqueTraceReplayValidationIssueKind::UnexpectedObservation,
            "expected_verdict",
            "case expected_verdict differs from the variant-owned semantic oracle",
        ));
    }
    if case.expected_quarantine_status != oracle_quarantine {
        issues.push(issue(
            OpaqueTraceReplayValidationIssueKind::UnexpectedObservation,
            "expected_quarantine_status",
            "case quarantine status differs from the variant-owned semantic oracle",
        ));
    }
    match case.candidate.digest() {
        Ok(expected_digest) if !same_digest(&expected_digest, &result.candidate_digest) => {
            issues.push(issue(
                OpaqueTraceReplayValidationIssueKind::CandidateDigestMismatch,
                "candidate_digest",
                "adapter result is not bound to the candidate metadata",
            ));
        }
        Err(_) => issues.push(issue(
            OpaqueTraceReplayValidationIssueKind::CandidateDigestMismatch,
            "candidate_digest",
            "candidate digest could not be computed",
        )),
        Ok(_) => {}
    }
    if result.authority_granted {
        issues.push(issue(
            OpaqueTraceReplayValidationIssueKind::AuthorityGranted,
            "authority_granted",
            "adapter observations cannot authorize state transitions",
        ));
    }
    if result.claim_boundary != OPAQUE_TRACE_REPLAY_CLAIM_BOUNDARY {
        issues.push(issue(
            OpaqueTraceReplayValidationIssueKind::ClaimBoundaryTooHigh,
            "claim_boundary",
            "adapter result exceeds the Level0DesignNote ceiling",
        ));
    }
    if result.quarantine_status != oracle_quarantine {
        issues.push(issue(
            OpaqueTraceReplayValidationIssueKind::UnexpectedObservation,
            "quarantine_status",
            "adapter quarantine status differs from the semantic oracle",
        ));
    }
    if result.backend_outcome == BackendOutcome::Accepted
        && oracle_verdict != ExpectedVerdict::Accept
    {
        issues.push(issue(
            OpaqueTraceReplayValidationIssueKind::UnexpectedObservation,
            "backend_outcome",
            "unexpected acceptance remains an unsound candidate and cannot authorize state",
        ));
    }

    OpaqueTraceReplayValidation {
        valid: issues.is_empty(),
        issues,
    }
}

fn synthetic_digest(label: &str, role: ArtifactRole) -> ArtifactDigest {
    compute_artifact_digest_bytes(label.as_bytes(), Some(ArtifactKind::Other), Some(role))
}

fn variant_name(variant: OpaqueTraceReplayVariant) -> &'static str {
    match variant {
        OpaqueTraceReplayVariant::ValidSameSession => "valid_same_session",
        OpaqueTraceReplayVariant::WrongUserReplay => "wrong_user_replay",
        OpaqueTraceReplayVariant::WrongSessionReplay => "wrong_session_replay",
        OpaqueTraceReplayVariant::WrongModelReplay => "wrong_model_replay",
        OpaqueTraceReplayVariant::OutOfOrderBlock => "out_of_order_block",
        OpaqueTraceReplayVariant::DuplicateBlock => "duplicate_block",
        OpaqueTraceReplayVariant::StaleOrRevokedBlock => "stale_or_revoked_block",
        OpaqueTraceReplayVariant::HiddenInjection => "hidden_injection",
        OpaqueTraceReplayVariant::SecretBearingTranscript => "secret_bearing_transcript",
        OpaqueTraceReplayVariant::MalformedEnvelope => "malformed_envelope",
    }
}

fn context_matches(candidate: &OpaqueTraceReplayCandidate) -> bool {
    candidate.context.expected_user_id == candidate.context.observed_user_id
        && candidate.context.expected_session_id == candidate.context.observed_session_id
        && candidate.context.expected_model_version == candidate.context.observed_model_version
        && candidate.context.expected_predecessor_digest
            == candidate.context.observed_predecessor_digest
        && candidate.context.expected_sequence_number == candidate.context.observed_sequence_number
}

fn validate_digest(
    issues: &mut Vec<OpaqueTraceReplayValidationIssue>,
    path: &str,
    digest: &ArtifactDigest,
) {
    if !valid_digest(digest) {
        issues.push(issue(
            OpaqueTraceReplayValidationIssueKind::InvalidDigest,
            path,
            "digest must be a non-empty SHA-256 value with 64 hexadecimal characters",
        ));
    }
}

fn valid_digest(digest: &ArtifactDigest) -> bool {
    digest.algorithm == ArtifactDigestAlgorithm::Sha256
        && digest.byte_len > 0
        && digest.hex_digest.len() == 64
        && digest
            .hex_digest
            .chars()
            .all(|character| character.is_ascii_hexdigit())
}

fn same_digest(left: &ArtifactDigest, right: &ArtifactDigest) -> bool {
    left.algorithm == right.algorithm
        && left.hex_digest.eq_ignore_ascii_case(&right.hex_digest)
        && left.byte_len == right.byte_len
        && left.kind == right.kind
        && left.role == right.role
}

fn mutation_mismatch(issues: &mut Vec<OpaqueTraceReplayValidationIssue>, variant: &str) {
    issues.push(issue(
        OpaqueTraceReplayValidationIssueKind::MutationMismatch,
        "variant",
        format!("candidate does not satisfy the declared {variant} mutation"),
    ));
}

fn issue(
    kind: OpaqueTraceReplayValidationIssueKind,
    path: impl Into<String>,
    message: impl Into<String>,
) -> OpaqueTraceReplayValidationIssue {
    OpaqueTraceReplayValidationIssue {
        kind,
        path: path.into(),
        message: message.into(),
    }
}

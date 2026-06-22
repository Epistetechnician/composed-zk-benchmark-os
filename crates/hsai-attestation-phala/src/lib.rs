//! Deterministic fixture-oriented Phala/dstack attestation backend preparation.
//!
//! This crate does not perform real TDX quote verification, managed-service
//! signature verification or JWKS/JWT validation. It validates a small local
//! evidence model so the HSAI attestation seam can be tested before real Phala
//! artifacts are introduced. Operator-live invocation plumbing accepts
//! caller-supplied clients and credentials, but normal tests use hermetic
//! in-memory implementations only. The optional `operator-live-provider` feature
//! exposes an operator-owned HTTP client boundary; it is disabled by default.

use hsai_agent_case::{AgentCase, EvidenceLane};
use hsai_attestation::{AttestationInput, AttestationVerifier, VerifiedAttestation, VerifyError};
use hsai_claim_envelope::{ClaimEnvelope, LaneId, Maturity, TimeWindow, TrustRoot, VendorId, VkId};
use hsai_distinct_agent::Anchor;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::cell::RefCell;
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

pub mod artifact;
pub use artifact::{
    parse_phala_artifact, validate_phala_artifact, DstackEvent, ManagedVerifierMode,
    PhalaArtifactAttestationLane, PhalaArtifactBundle, PhalaValidationError, PhalaValidationPolicy,
    RtmrSet, ValidatedPhalaAttestation,
};
pub mod challenge;
pub use challenge::{
    agent_case_hash, build_agent_case_challenge_packet, build_hsai_challenge_packet,
    capture_workflow_manifest, validate_hsai_challenge_packet, CaptureWorkflowManifest,
    ChallengeError, ChallengeReplayGuard, HsaiChallengeInput, HsaiChallengePacket,
    RealArtifactProviderMode, HSAI_CAPTURE_MANIFEST_SCHEMA_VERSION, HSAI_CHALLENGE_SCHEMA_VERSION,
    PHASE_57_CLAIM_BOUNDARY,
};
#[cfg(feature = "operator-live-provider")]
pub mod operator_live_provider;
#[cfg(feature = "operator-live-provider")]
pub use operator_live_provider::{
    PhalaEnvCredentialProvider, PhalaOperatorLiveProviderClient, PhalaOperatorLiveProviderConfig,
    PhalaOperatorLiveProviderError, PhalaOperatorLiveRawResponse, PhalaOperatorLiveTransport,
    UreqPhalaOperatorLiveTransport,
};

/// Claim boundary for this crate.
pub const CLAIM_BOUNDARY: &str =
    "fixture Phala/dstack backend preparation; not real hardware verification or proof";

const LOCAL_FIXTURE_QUOTE_PREFIX: &str = "fixture-tdx-quote:";
const MANAGED_API_ACCEPTED: &str = "managed-api:accepted";
const PHALA_MANAGED_VERIFIER_ROOT: &str = "phala-managed-verifier-api";
const PHALA_LIVE_PROVIDER: &str = "phala-dstack";
const PHALA_LIVE_MODE: &str = "live-managed-verifier";
pub const PHALA_OPERATOR_LIVE_ARTIFACT_SCHEMA_VERSION: &str =
    "hsai.phala.operator-live-artifact.v1";
pub const PHALA_OPERATOR_LIVE_CLAIM_BOUNDARY: &str = "Attested";
pub const PHALA_OPERATOR_LIVE_MAX_TIMEOUT_SECONDS: u64 = 300;
pub const PHALA_OPERATOR_LIVE_MAX_RETRY_LIMIT: u64 = 3;
pub const PHALA_OPERATOR_LIVE_REQUEST_PATH: &str = "operator-live/request.json";
pub const PHALA_OPERATOR_LIVE_NORMALIZED_RESPONSE_PATH: &str =
    "operator-live/normalized-response.json";
pub const PHALA_OPERATOR_LIVE_TRUST_ROOTS_PATH: &str = "operator-live/trust-roots.json";
pub const PHALA_OPERATOR_LIVE_REDACTION_REPORT_PATH: &str = "operator-live/redaction-report.json";
pub const PHALA_OPERATOR_LIVE_AUDIT_PATH: &str = "operator-live/audit.json";
pub const PHALA_OPERATOR_LIVE_RAW_RESPONSE_DIGEST_PATH: &str = "operator-live/raw-response.sha256";

/// Fixture-oriented Phala/dstack evidence.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PhalaEvidence {
    pub anchor_id: String,
    pub quote_hex: String,
    pub report_data: Vec<u8>,
    pub compose_hash: Vec<u8>,
    pub event_log: Option<Vec<u8>>,
    pub docker_image_digest: Option<Vec<u8>>,
    pub not_before: u64,
    pub not_after: u64,
}

/// Local trust policy for fixture evidence.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PhalaTrustPolicy {
    pub expected_anchor_id: String,
    pub expected_report_data: Vec<u8>,
    pub expected_compose_hash: Vec<u8>,
    pub expected_docker_image_digest: Option<Vec<u8>>,
    pub require_event_log_replay: bool,
    pub allow_managed_api: bool,
    pub now: u64,
}

/// Verification mode for fixture evidence.
#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum PhalaVerifyMode {
    /// Deterministic fixture quote mode. This is not real TDX verification.
    Local,
    /// Deterministic fixture managed API response mode. This is not a network call.
    ManagedApi,
}

/// Phase 3 fixture-backend errors.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum PhalaError {
    Parse,
    AnchorMismatch,
    ReportDataMismatch,
    ComposeHashMismatch,
    DockerImageDigestMismatch,
    EventLogReplayMismatch,
    QuoteVerificationFailed,
    ManagedApiRejected,
    ManagedApiDisallowed,
    Expired,
    NotYetValid,
}

impl PhalaError {
    fn as_verify_error(&self) -> VerifyError {
        match self {
            Self::AnchorMismatch => VerifyError::AnchorMismatch,
            Self::ReportDataMismatch => VerifyError::ReportDataMismatch,
            Self::ComposeHashMismatch
            | Self::DockerImageDigestMismatch
            | Self::EventLogReplayMismatch => VerifyError::MeasurementMismatch,
            Self::QuoteVerificationFailed
            | Self::ManagedApiRejected
            | Self::ManagedApiDisallowed
            | Self::Parse => VerifyError::SignatureUnverified,
            Self::Expired | Self::NotYetValid => VerifyError::Expired,
        }
    }
}

/// Fixture Phala verifier implementing the shipped attestation seam.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PhalaAttestationVerifier {
    pub evidence: PhalaEvidence,
    pub policy: PhalaTrustPolicy,
    pub mode: PhalaVerifyMode,
}

impl PhalaAttestationVerifier {
    pub fn new(evidence: PhalaEvidence, policy: PhalaTrustPolicy, mode: PhalaVerifyMode) -> Self {
        Self {
            evidence,
            policy,
            mode,
        }
    }

    /// Trust roots relied on by this fixture verifier for a given anchor.
    pub fn trust_roots_for(&self, anchor: &Anchor) -> BTreeSet<TrustRoot> {
        let mut roots = BTreeSet::from([anchor.trust_root()]);
        if self.mode == PhalaVerifyMode::ManagedApi {
            roots.insert(TrustRoot::VerifyingKey(VkId(
                PHALA_MANAGED_VERIFIER_ROOT.to_owned(),
            )));
        }
        roots
    }
}

impl AttestationVerifier for PhalaAttestationVerifier {
    fn verify(
        &self,
        token: &hsai_attestation::Token,
        expected_nonce: u64,
        expected_report_data: &[u8],
        expected_measurements: &[u8],
        anchor_id: &str,
        now: u64,
    ) -> Result<VerifiedAttestation, VerifyError> {
        if token.anchor_id != anchor_id
            || self.evidence.anchor_id != anchor_id
            || self.policy.expected_anchor_id != anchor_id
        {
            return Err(VerifyError::AnchorMismatch);
        }
        if token.nonce != expected_nonce {
            return Err(VerifyError::NonceMismatch);
        }
        if token.report_data != expected_report_data {
            return Err(VerifyError::ReportDataMismatch);
        }
        if token.measurements != expected_measurements {
            return Err(VerifyError::MeasurementMismatch);
        }

        let mut policy = self.policy.clone();
        policy.now = now;
        verify_phala_quote_or_report(&self.evidence, &policy, self.mode)
            .map_err(|error| error.as_verify_error())?;

        if self.evidence.report_data != token.report_data {
            return Err(VerifyError::ReportDataMismatch);
        }
        if self.evidence.compose_hash != token.measurements {
            return Err(VerifyError::MeasurementMismatch);
        }

        Ok(map_phala_to_verified_attestation(&self.evidence))
    }
}

/// Phala-specific attestation lane that preserves provider trust roots.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PhalaAttestationLane {
    pub verifier: PhalaAttestationVerifier,
    pub inputs: Vec<AttestationInput>,
}

impl PhalaAttestationLane {
    pub fn new(verifier: PhalaAttestationVerifier, inputs: Vec<AttestationInput>) -> Self {
        Self { verifier, inputs }
    }
}

impl EvidenceLane for PhalaAttestationLane {
    fn id(&self) -> LaneId {
        LaneId::Named("phala-attestation".to_owned())
    }

    fn ceiling(&self) -> Maturity {
        Maturity::Attested
    }

    fn evaluate(&self, case: &AgentCase) -> ClaimEnvelope {
        let mut guarantees = BTreeSet::new();
        let mut trust_roots = BTreeSet::new();
        let mut window = TimeWindow::all();

        for input in &self.inputs {
            if let Ok(verified) = self.verifier.verify(
                &input.token,
                input.expected_nonce,
                &input.expected_report_data,
                &input.expected_measurements,
                &input.anchor.anchor_id(),
                case.observed_at,
            ) {
                guarantees.insert(input.anchor.validity_assumption(&case.subject));
                trust_roots.extend(self.verifier.trust_roots_for(&input.anchor));
                window = window.intersect(&TimeWindow {
                    start: verified.not_before,
                    end: verified.not_after,
                });
            }
        }

        if guarantees.is_empty() {
            ClaimEnvelope::new(
                BTreeSet::new(),
                BTreeSet::new(),
                case.oracle.excluded.clone(),
                Maturity::Stub,
                BTreeSet::new(),
                TimeWindow::all(),
                self.id(),
            )
        } else {
            ClaimEnvelope::new(
                guarantees,
                BTreeSet::new(),
                case.oracle.excluded.clone(),
                Maturity::Attested,
                trust_roots,
                window,
                self.id(),
            )
        }
    }
}

/// Parse deterministic Phala fixture evidence from JSON.
pub fn parse_phala_evidence(bytes: &[u8]) -> Result<PhalaEvidence, PhalaError> {
    serde_json::from_slice(bytes).map_err(|_| PhalaError::Parse)
}

/// Verify the evidence report-data binding.
pub fn verify_report_data_binding(
    evidence: &PhalaEvidence,
    expected: &[u8],
) -> Result<(), PhalaError> {
    if evidence.report_data == expected {
        Ok(())
    } else {
        Err(PhalaError::ReportDataMismatch)
    }
}

/// Verify the evidence compose hash.
pub fn verify_compose_hash(evidence: &PhalaEvidence, expected: &[u8]) -> Result<(), PhalaError> {
    if evidence.compose_hash == expected {
        Ok(())
    } else {
        Err(PhalaError::ComposeHashMismatch)
    }
}

/// Verify the evidence validity window.
pub fn verify_freshness(evidence: &PhalaEvidence, now: u64) -> Result<(), PhalaError> {
    if now < evidence.not_before {
        Err(PhalaError::NotYetValid)
    } else if now > evidence.not_after {
        Err(PhalaError::Expired)
    } else {
        Ok(())
    }
}

/// Map accepted fixture evidence into the shipped attestation result type.
pub fn map_phala_to_verified_attestation(evidence: &PhalaEvidence) -> VerifiedAttestation {
    VerifiedAttestation {
        anchor_id: evidence.anchor_id.clone(),
        not_before: evidence.not_before,
        not_after: evidence.not_after,
        verifier_trust_roots: BTreeSet::new(),
    }
}

/// Verify deterministic fixture evidence according to policy and mode.
pub fn verify_phala_quote_or_report(
    evidence: &PhalaEvidence,
    policy: &PhalaTrustPolicy,
    mode: PhalaVerifyMode,
) -> Result<(), PhalaError> {
    if evidence.anchor_id != policy.expected_anchor_id {
        return Err(PhalaError::AnchorMismatch);
    }

    match mode {
        PhalaVerifyMode::Local => {
            if !evidence.quote_hex.starts_with(LOCAL_FIXTURE_QUOTE_PREFIX) {
                return Err(PhalaError::QuoteVerificationFailed);
            }
        }
        PhalaVerifyMode::ManagedApi => {
            if !policy.allow_managed_api {
                return Err(PhalaError::ManagedApiDisallowed);
            }
            if evidence.quote_hex != MANAGED_API_ACCEPTED {
                return Err(PhalaError::ManagedApiRejected);
            }
        }
    }

    verify_report_data_binding(evidence, &policy.expected_report_data)?;
    verify_compose_hash(evidence, &policy.expected_compose_hash)?;
    if evidence.docker_image_digest != policy.expected_docker_image_digest {
        return Err(PhalaError::DockerImageDigestMismatch);
    }
    if policy.require_event_log_replay && evidence.event_log.is_none() {
        return Err(PhalaError::EventLogReplayMismatch);
    }
    verify_freshness(evidence, policy.now)
}

/// Non-secret request passed to a caller-supplied Phala managed-verifier client.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PhalaManagedVerifierRequest {
    pub anchor_id: String,
    pub agent_pubkey: Vec<u8>,
    pub case_hash: Vec<u8>,
    pub nonce: u64,
    pub expected_report_data_binding: Vec<u8>,
    pub expected_compose_hash: Vec<u8>,
    pub expected_runtime_measurements: BTreeSet<String>,
    pub expected_image_digest: String,
    pub freshness_window: u64,
    pub managed_verifier_endpoint_id: String,
    pub request_time: u64,
}

/// Provider verdict after response normalization.
#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum PhalaManagedVerifierVerdict {
    Accepted,
    Rejected,
}

/// Normalized Phala managed-verifier response used by hermetic tests.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PhalaManagedVerifierResponse {
    pub provider: String,
    pub verification_mode: String,
    pub provider_verdict: PhalaManagedVerifierVerdict,
    pub anchor_id: String,
    pub nonce: u64,
    pub report_data: Vec<u8>,
    pub compose_hash: Vec<u8>,
    pub runtime_measurements: BTreeSet<String>,
    pub image_digest: String,
    pub issued_at: u64,
    pub expires_at: u64,
    pub raw_response_digest: Vec<u8>,
    pub provider_trust_roots: BTreeSet<TrustRoot>,
}

/// Trust-root disclosure sidecar for future operator-live bundles.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PhalaOperatorLiveTrustRoots {
    pub schema_version: String,
    pub provider: String,
    pub verification_mode: String,
    pub roots: BTreeSet<TrustRoot>,
}

/// Retained non-secret field plus the rationale for retaining it.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PhalaOperatorLiveRetainedField {
    pub value: String,
    pub rationale: String,
}

/// Redaction report sidecar for future operator-live bundles.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PhalaOperatorLiveRedactionReport {
    pub schema_version: String,
    pub digest_algorithm: String,
    pub removed_fields: BTreeSet<String>,
    pub hashed_fields: BTreeSet<String>,
    pub retained_fields: BTreeMap<String, PhalaOperatorLiveRetainedField>,
    pub dropped_secret_shaped_fields: BTreeSet<String>,
}

/// Audit sidecar binding the future operator-live bundle together.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PhalaOperatorLiveAudit {
    pub schema_version: String,
    pub operator_run_id: String,
    pub provider: String,
    pub verification_mode: String,
    pub request_digest: String,
    pub normalized_response_digest: String,
    pub trust_roots_digest: String,
    pub redaction_report_digest: String,
    pub raw_response_digest: String,
    pub started_at: u64,
    pub finished_at: u64,
    pub timeout_seconds: u64,
    pub retry_limit: u64,
    pub provider_verdict: PhalaManagedVerifierVerdict,
    pub claim_boundary: String,
    pub non_claims: BTreeSet<String>,
}

/// In-memory representation of the declared operator-live artifact files.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PhalaOperatorLiveArtifactBundle {
    pub request: PhalaManagedVerifierRequest,
    pub normalized_response: PhalaManagedVerifierResponse,
    pub trust_roots: PhalaOperatorLiveTrustRoots,
    pub redaction_report: PhalaOperatorLiveRedactionReport,
    pub audit: PhalaOperatorLiveAudit,
    pub raw_response_sha256: String,
}

/// Validated operator-live artifact metadata.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct ValidatedPhalaOperatorLiveArtifact {
    pub anchor_id: String,
    pub operator_run_id: String,
    pub provider: String,
    pub verification_mode: String,
    pub claim_boundary: String,
    pub request_digest: String,
    pub normalized_response_digest: String,
    pub trust_roots: BTreeSet<TrustRoot>,
}

/// Explicit overwrite mode for local operator-live output roots.
#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum PhalaOperatorLiveOutputOverwriteMode {
    RefuseExisting,
    ReplaceExisting,
}

/// Caller-declared inputs for an operator-owned Phala live invocation.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PhalaOperatorLiveInvocationInput {
    pub operator_run_id: String,
    pub operator_acknowledged: bool,
    pub provider_endpoint: String,
    pub credential_source: String,
    pub timeout_seconds: u64,
    pub retry_limit: u64,
    pub anchor_id: String,
    pub agent_pubkey: Vec<u8>,
    pub case_hash: Vec<u8>,
    pub nonce: u64,
    pub expected_report_data_binding: Vec<u8>,
    pub expected_compose_hash: Vec<u8>,
    pub expected_runtime_measurements: BTreeSet<String>,
    pub expected_image_digest: String,
    pub request_time: u64,
    pub started_at: u64,
    pub output_root: PathBuf,
    pub overwrite: PhalaOperatorLiveOutputOverwriteMode,
}

/// Opaque operator credential loaded outside repo fixtures and artifacts.
#[derive(Clone, Eq, PartialEq)]
pub struct PhalaOperatorLiveCredential {
    source_id: String,
    secret: Vec<u8>,
}

impl std::fmt::Debug for PhalaOperatorLiveCredential {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("PhalaOperatorLiveCredential")
            .field("source_id", &self.source_id)
            .field("secret", &"<redacted>")
            .finish()
    }
}

impl PhalaOperatorLiveCredential {
    pub fn new(
        source_id: impl Into<String>,
        secret: impl Into<Vec<u8>>,
    ) -> Result<Self, PhalaOperatorLiveInvocationError> {
        let source_id = source_id.into();
        let secret = secret.into();
        if source_id.trim().is_empty() {
            return Err(PhalaOperatorLiveInvocationError::MissingCredentialSource);
        }
        if secret.is_empty() {
            return Err(PhalaOperatorLiveInvocationError::CredentialUnavailable(
                source_id,
            ));
        }
        Ok(Self { source_id, secret })
    }

    pub fn source_id(&self) -> &str {
        &self.source_id
    }

    pub fn secret_bytes(&self) -> &[u8] {
        &self.secret
    }
}

/// Credential loader boundary. Implementations must keep secrets outside git.
pub trait PhalaOperatorLiveCredentialProvider {
    fn load(
        &self,
        source_id: &str,
    ) -> Result<PhalaOperatorLiveCredential, PhalaOperatorLiveInvocationError>;
}

/// In-memory credential provider for hermetic tests.
#[derive(Clone, Default)]
pub struct InMemoryPhalaOperatorLiveCredentialProvider {
    credentials: BTreeMap<String, Vec<u8>>,
}

impl std::fmt::Debug for InMemoryPhalaOperatorLiveCredentialProvider {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("InMemoryPhalaOperatorLiveCredentialProvider")
            .field("credential_count", &self.credentials.len())
            .finish()
    }
}

impl InMemoryPhalaOperatorLiveCredentialProvider {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_credential(
        mut self,
        source_id: impl Into<String>,
        secret: impl Into<Vec<u8>>,
    ) -> Self {
        self.credentials.insert(source_id.into(), secret.into());
        self
    }
}

impl PhalaOperatorLiveCredentialProvider for InMemoryPhalaOperatorLiveCredentialProvider {
    fn load(
        &self,
        source_id: &str,
    ) -> Result<PhalaOperatorLiveCredential, PhalaOperatorLiveInvocationError> {
        let secret = self.credentials.get(source_id).cloned().ok_or_else(|| {
            PhalaOperatorLiveInvocationError::CredentialUnavailable(source_id.to_owned())
        })?;
        PhalaOperatorLiveCredential::new(source_id.to_owned(), secret)
    }
}

/// Credential-aware live invocation client boundary.
pub trait PhalaOperatorLiveClient {
    fn verify_with_credential(
        &self,
        request: &PhalaManagedVerifierRequest,
        credential: &PhalaOperatorLiveCredential,
    ) -> Result<PhalaManagedVerifierResponse, PhalaManagedVerifierError>;
}

impl<T: PhalaManagedVerifierClient> PhalaOperatorLiveClient for T {
    fn verify_with_credential(
        &self,
        request: &PhalaManagedVerifierRequest,
        _credential: &PhalaOperatorLiveCredential,
    ) -> Result<PhalaManagedVerifierResponse, PhalaManagedVerifierError> {
        self.verify(request)
    }
}

/// Operator-live invocation orchestrator.
#[derive(Debug)]
pub struct PhalaOperatorLiveInvocation<C, P> {
    pub client: C,
    pub credential_provider: P,
    replay_guard: RefCell<PhalaReplayGuard>,
}

impl<C, P> PhalaOperatorLiveInvocation<C, P> {
    pub fn new(client: C, credential_provider: P) -> Self {
        Self {
            client,
            credential_provider,
            replay_guard: RefCell::new(PhalaReplayGuard::new()),
        }
    }
}

impl<C, P> PhalaOperatorLiveInvocation<C, P>
where
    C: PhalaOperatorLiveClient,
    P: PhalaOperatorLiveCredentialProvider,
{
    pub fn invoke(
        &self,
        input: &PhalaOperatorLiveInvocationInput,
    ) -> Result<ValidatedPhalaOperatorLiveArtifact, PhalaOperatorLiveInvocationError> {
        validate_phala_operator_live_invocation_input(input)?;
        let credential = self.credential_provider.load(&input.credential_source)?;
        if credential.source_id() != input.credential_source {
            return Err(PhalaOperatorLiveInvocationError::CredentialSourceMismatch {
                expected: input.credential_source.clone(),
                actual: credential.source_id().to_owned(),
            });
        }

        let request = phala_operator_live_invocation_request(input);
        let response = self.invoke_with_retries(&request, &credential, input.retry_limit)?;
        validate_phala_managed_response(&request, &response)
            .map_err(PhalaOperatorLiveInvocationError::ManagedVerifier)?;
        self.replay_guard
            .borrow_mut()
            .check_and_record(&request.anchor_id, request.nonce)
            .map_err(PhalaOperatorLiveInvocationError::ManagedVerifier)?;

        let bundle = build_phala_operator_live_invocation_bundle(input, request, response)?;
        write_phala_operator_live_artifact_output_root(&input.output_root, &bundle, input.overwrite)
            .map_err(PhalaOperatorLiveInvocationError::Artifact)
    }

    fn invoke_with_retries(
        &self,
        request: &PhalaManagedVerifierRequest,
        credential: &PhalaOperatorLiveCredential,
        retry_limit: u64,
    ) -> Result<PhalaManagedVerifierResponse, PhalaOperatorLiveInvocationError> {
        let mut last_error = PhalaManagedVerifierError::ClientUnavailable;
        for _attempt in 0..=retry_limit {
            match self.client.verify_with_credential(request, credential) {
                Ok(response) => return Ok(response),
                Err(error) => last_error = error,
            }
        }
        Err(PhalaOperatorLiveInvocationError::RetryExhausted {
            attempts: retry_limit + 1,
            last_error,
        })
    }
}

/// Failure taxonomy for hermetic Phala managed-verifier preparation.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum PhalaManagedVerifierError {
    ClientUnavailable,
    TransportUnavailable,
    AuthenticationFailed,
    UnexpectedHttpStatus(u16),
    MalformedResponse,
    WrongProvider,
    UnsupportedMode,
    ProviderRejected,
    StaleResponse,
    ReplayedNonce,
    AnchorMismatch,
    NonceMismatch,
    ReportDataMismatch,
    ComposeHashMismatch,
    RuntimeMeasurementMismatch,
    ImageDigestMismatch,
    MissingTrustRoot,
    ClaimBoundaryViolation,
}

/// Failure taxonomy for local operator-live artifact plumbing.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum PhalaOperatorLiveArtifactError {
    MissingFile(String),
    UnexpectedFile(String),
    UnsafePath(String),
    InvalidJson {
        path: String,
        message: String,
    },
    InvalidUtf8(String),
    InvalidDigest {
        field: String,
        value: String,
    },
    SchemaVersionMismatch {
        field: String,
        actual: String,
    },
    DigestMismatch {
        field: String,
        actual: String,
        expected: String,
    },
    ProviderMismatch,
    TrustRootMismatch,
    RedactionRationaleMissing(String),
    RedactionSecretRetained(String),
    ClaimBoundaryViolation,
    MissingNonClaim(String),
    OutputRootInvalid {
        path: String,
        reason: String,
    },
    ExistingBundleRequiresOverwrite(String),
    SymlinkPath(String),
    Filesystem {
        path: String,
        message: String,
    },
    ManagedVerifier(PhalaManagedVerifierError),
}

impl std::fmt::Display for PhalaOperatorLiveArtifactError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{self:?}")
    }
}

impl std::error::Error for PhalaOperatorLiveArtifactError {}

/// Failure taxonomy for operator-owned invocation plumbing.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum PhalaOperatorLiveInvocationError {
    MissingOperatorAcknowledgement,
    MissingCredentialSource,
    EmptyEndpoint,
    TimeoutOutOfBounds {
        actual: u64,
        max: u64,
    },
    RetryLimitOutOfBounds {
        actual: u64,
        max: u64,
    },
    CredentialUnavailable(String),
    CredentialSourceMismatch {
        expected: String,
        actual: String,
    },
    RetryExhausted {
        attempts: u64,
        last_error: PhalaManagedVerifierError,
    },
    ManagedVerifier(PhalaManagedVerifierError),
    Artifact(PhalaOperatorLiveArtifactError),
}

impl std::fmt::Display for PhalaOperatorLiveInvocationError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{self:?}")
    }
}

impl std::error::Error for PhalaOperatorLiveInvocationError {}

impl PhalaManagedVerifierError {
    fn as_verify_error(&self) -> VerifyError {
        match self {
            Self::AnchorMismatch => VerifyError::AnchorMismatch,
            Self::NonceMismatch => VerifyError::NonceMismatch,
            Self::ReportDataMismatch => VerifyError::ReportDataMismatch,
            Self::ComposeHashMismatch
            | Self::RuntimeMeasurementMismatch
            | Self::ImageDigestMismatch => VerifyError::MeasurementMismatch,
            Self::StaleResponse => VerifyError::Expired,
            Self::ClientUnavailable
            | Self::TransportUnavailable
            | Self::AuthenticationFailed
            | Self::UnexpectedHttpStatus(_)
            | Self::MalformedResponse
            | Self::WrongProvider
            | Self::UnsupportedMode
            | Self::ProviderRejected
            | Self::ReplayedNonce
            | Self::MissingTrustRoot
            | Self::ClaimBoundaryViolation => VerifyError::SignatureUnverified,
        }
    }
}

/// Caller-owned Phala managed-verifier boundary.
///
/// Implementations may call a provider outside this crate, but normal workspace
/// tests use [`InMemoryPhalaManagedVerifierClient`] and perform no network I/O.
pub trait PhalaManagedVerifierClient {
    fn verify(
        &self,
        request: &PhalaManagedVerifierRequest,
    ) -> Result<PhalaManagedVerifierResponse, PhalaManagedVerifierError>;
}

/// Parse and validate a declared in-memory operator-live artifact file set.
///
/// This performs no filesystem I/O and no provider I/O. Callers provide the
/// exact logical file names and bytes that would later be materialized under an
/// operator-owned output directory.
pub fn parse_phala_operator_live_artifact_files(
    files: &BTreeMap<String, Vec<u8>>,
) -> Result<PhalaOperatorLiveArtifactBundle, PhalaOperatorLiveArtifactError> {
    validate_operator_live_file_set(files)?;

    let request = parse_operator_live_json(
        PHALA_OPERATOR_LIVE_REQUEST_PATH,
        files
            .get(PHALA_OPERATOR_LIVE_REQUEST_PATH)
            .expect("required path checked"),
    )?;
    let normalized_response = parse_operator_live_json(
        PHALA_OPERATOR_LIVE_NORMALIZED_RESPONSE_PATH,
        files
            .get(PHALA_OPERATOR_LIVE_NORMALIZED_RESPONSE_PATH)
            .expect("required path checked"),
    )?;
    let trust_roots = parse_operator_live_json(
        PHALA_OPERATOR_LIVE_TRUST_ROOTS_PATH,
        files
            .get(PHALA_OPERATOR_LIVE_TRUST_ROOTS_PATH)
            .expect("required path checked"),
    )?;
    let redaction_report = parse_operator_live_json(
        PHALA_OPERATOR_LIVE_REDACTION_REPORT_PATH,
        files
            .get(PHALA_OPERATOR_LIVE_REDACTION_REPORT_PATH)
            .expect("required path checked"),
    )?;
    let audit = parse_operator_live_json(
        PHALA_OPERATOR_LIVE_AUDIT_PATH,
        files
            .get(PHALA_OPERATOR_LIVE_AUDIT_PATH)
            .expect("required path checked"),
    )?;
    let raw_response_sha256 = String::from_utf8(
        files
            .get(PHALA_OPERATOR_LIVE_RAW_RESPONSE_DIGEST_PATH)
            .expect("required path checked")
            .clone(),
    )
    .map_err(|_| {
        PhalaOperatorLiveArtifactError::InvalidUtf8(
            PHALA_OPERATOR_LIVE_RAW_RESPONSE_DIGEST_PATH.to_owned(),
        )
    })?
    .trim()
    .to_owned();

    Ok(PhalaOperatorLiveArtifactBundle {
        request,
        normalized_response,
        trust_roots,
        redaction_report,
        audit,
        raw_response_sha256,
    })
}

/// Validate an in-memory operator-live artifact bundle.
pub fn validate_phala_operator_live_artifact_bundle(
    bundle: &PhalaOperatorLiveArtifactBundle,
) -> Result<ValidatedPhalaOperatorLiveArtifact, PhalaOperatorLiveArtifactError> {
    validate_operator_live_schema(
        "trust_roots.schema_version",
        &bundle.trust_roots.schema_version,
    )?;
    validate_operator_live_schema(
        "redaction_report.schema_version",
        &bundle.redaction_report.schema_version,
    )?;
    validate_operator_live_schema("audit.schema_version", &bundle.audit.schema_version)?;

    if bundle.audit.claim_boundary != PHALA_OPERATOR_LIVE_CLAIM_BOUNDARY {
        return Err(PhalaOperatorLiveArtifactError::ClaimBoundaryViolation);
    }
    validate_operator_live_non_claims(&bundle.audit.non_claims)?;
    validate_operator_live_digest("raw_response_sha256", &bundle.raw_response_sha256)?;
    validate_operator_live_redaction_report(&bundle.redaction_report)?;
    validate_phala_managed_response(&bundle.request, &bundle.normalized_response)
        .map_err(PhalaOperatorLiveArtifactError::ManagedVerifier)?;
    validate_operator_live_provider_consistency(bundle)?;
    validate_operator_live_trust_roots(bundle)?;
    validate_operator_live_audit_digests(bundle)?;

    Ok(ValidatedPhalaOperatorLiveArtifact {
        anchor_id: bundle.request.anchor_id.clone(),
        operator_run_id: bundle.audit.operator_run_id.clone(),
        provider: bundle.audit.provider.clone(),
        verification_mode: bundle.audit.verification_mode.clone(),
        claim_boundary: bundle.audit.claim_boundary.clone(),
        request_digest: bundle.audit.request_digest.clone(),
        normalized_response_digest: bundle.audit.normalized_response_digest.clone(),
        trust_roots: bundle.trust_roots.roots.clone(),
    })
}

/// Parse and validate an in-memory operator-live artifact file set.
pub fn validate_phala_operator_live_artifact_files(
    files: &BTreeMap<String, Vec<u8>>,
) -> Result<ValidatedPhalaOperatorLiveArtifact, PhalaOperatorLiveArtifactError> {
    let bundle = parse_phala_operator_live_artifact_files(files)?;
    validate_phala_operator_live_artifact_bundle(&bundle)
}

/// Write a validated operator-live artifact bundle under a caller-owned output root.
///
/// This performs local filesystem I/O only. It does not call Phala, load
/// credentials, retain raw response bodies, or create evidence stronger than the
/// Phase 83 in-memory validation result.
pub fn write_phala_operator_live_artifact_output_root(
    output_root: impl AsRef<Path>,
    bundle: &PhalaOperatorLiveArtifactBundle,
    overwrite: PhalaOperatorLiveOutputOverwriteMode,
) -> Result<ValidatedPhalaOperatorLiveArtifact, PhalaOperatorLiveArtifactError> {
    let validated = validate_phala_operator_live_artifact_bundle(bundle)?;
    let files = serialize_operator_live_artifact_bundle(bundle)?;
    let output_root = validate_operator_live_output_root(output_root.as_ref())?;
    prepare_operator_live_output_root(&output_root, overwrite)?;

    let staging_root = output_root.join(operator_live_staging_dir_name());
    if staging_root.exists() {
        remove_dir_all(&staging_root)?;
    }
    create_dir(&staging_root)?;

    let write_result = write_operator_live_files_to_root(&staging_root, &files)
        .and_then(|_| read_phala_operator_live_artifact_output_root(&staging_root))
        .and_then(|staged| {
            if staged != validated {
                return Err(PhalaOperatorLiveArtifactError::DigestMismatch {
                    field: "materialized.staged_bundle".to_owned(),
                    actual: staged.request_digest,
                    expected: validated.request_digest.clone(),
                });
            }
            let target = output_root.join("operator-live");
            if target.exists() {
                remove_dir_all(&target)?;
            }
            rename_path(&staging_root.join("operator-live"), &target)?;
            remove_dir_all(&staging_root)?;
            read_phala_operator_live_artifact_output_root(&output_root)
        });

    let _ = fs::remove_dir_all(&staging_root);

    write_result
}

/// Read a materialized operator-live artifact bundle from a caller-owned output root.
///
/// The returned metadata is produced only after parsing the declared local files
/// and passing them through the Phase 83 in-memory validator.
pub fn read_phala_operator_live_artifact_output_root(
    output_root: impl AsRef<Path>,
) -> Result<ValidatedPhalaOperatorLiveArtifact, PhalaOperatorLiveArtifactError> {
    let output_root = validate_operator_live_output_root(output_root.as_ref())?;
    let files = collect_operator_live_materialized_files(&output_root)?;
    validate_phala_operator_live_artifact_files(&files)
}

fn validate_phala_operator_live_invocation_input(
    input: &PhalaOperatorLiveInvocationInput,
) -> Result<(), PhalaOperatorLiveInvocationError> {
    if !input.operator_acknowledged {
        return Err(PhalaOperatorLiveInvocationError::MissingOperatorAcknowledgement);
    }
    if input.credential_source.trim().is_empty() {
        return Err(PhalaOperatorLiveInvocationError::MissingCredentialSource);
    }
    if input.provider_endpoint.trim().is_empty() {
        return Err(PhalaOperatorLiveInvocationError::EmptyEndpoint);
    }
    if input.timeout_seconds == 0 || input.timeout_seconds > PHALA_OPERATOR_LIVE_MAX_TIMEOUT_SECONDS
    {
        return Err(PhalaOperatorLiveInvocationError::TimeoutOutOfBounds {
            actual: input.timeout_seconds,
            max: PHALA_OPERATOR_LIVE_MAX_TIMEOUT_SECONDS,
        });
    }
    if input.retry_limit > PHALA_OPERATOR_LIVE_MAX_RETRY_LIMIT {
        return Err(PhalaOperatorLiveInvocationError::RetryLimitOutOfBounds {
            actual: input.retry_limit,
            max: PHALA_OPERATOR_LIVE_MAX_RETRY_LIMIT,
        });
    }
    Ok(())
}

fn phala_operator_live_invocation_request(
    input: &PhalaOperatorLiveInvocationInput,
) -> PhalaManagedVerifierRequest {
    PhalaManagedVerifierRequest {
        anchor_id: input.anchor_id.clone(),
        agent_pubkey: input.agent_pubkey.clone(),
        case_hash: input.case_hash.clone(),
        nonce: input.nonce,
        expected_report_data_binding: input.expected_report_data_binding.clone(),
        expected_compose_hash: input.expected_compose_hash.clone(),
        expected_runtime_measurements: input.expected_runtime_measurements.clone(),
        expected_image_digest: input.expected_image_digest.clone(),
        freshness_window: input.timeout_seconds,
        managed_verifier_endpoint_id: input.provider_endpoint.clone(),
        request_time: input.request_time,
    }
}

fn build_phala_operator_live_invocation_bundle(
    input: &PhalaOperatorLiveInvocationInput,
    request: PhalaManagedVerifierRequest,
    normalized_response: PhalaManagedVerifierResponse,
) -> Result<PhalaOperatorLiveArtifactBundle, PhalaOperatorLiveInvocationError> {
    let raw_response_sha256 = hex_lower(&normalized_response.raw_response_digest);
    let trust_roots = PhalaOperatorLiveTrustRoots {
        schema_version: PHALA_OPERATOR_LIVE_ARTIFACT_SCHEMA_VERSION.to_owned(),
        provider: PHALA_LIVE_PROVIDER.to_owned(),
        verification_mode: PHALA_LIVE_MODE.to_owned(),
        roots: normalized_response.provider_trust_roots.clone(),
    };
    let redaction_report = PhalaOperatorLiveRedactionReport {
        schema_version: PHALA_OPERATOR_LIVE_ARTIFACT_SCHEMA_VERSION.to_owned(),
        digest_algorithm: "sha256".to_owned(),
        removed_fields: BTreeSet::from([
            "authorization_header".to_owned(),
            "credential_source_value".to_owned(),
        ]),
        hashed_fields: BTreeSet::from(["raw_response_body".to_owned()]),
        retained_fields: BTreeMap::from([(
            "managed_verifier_endpoint_id".to_owned(),
            PhalaOperatorLiveRetainedField {
                value: input.provider_endpoint.clone(),
                rationale: "public provider endpoint label".to_owned(),
            },
        )]),
        dropped_secret_shaped_fields: BTreeSet::from([
            "bearer_token".to_owned(),
            "operator_credential".to_owned(),
        ]),
    };
    let audit = PhalaOperatorLiveAudit {
        schema_version: PHALA_OPERATOR_LIVE_ARTIFACT_SCHEMA_VERSION.to_owned(),
        operator_run_id: input.operator_run_id.clone(),
        provider: PHALA_LIVE_PROVIDER.to_owned(),
        verification_mode: PHALA_LIVE_MODE.to_owned(),
        request_digest: phala_operator_live_json_digest(&request)
            .map_err(PhalaOperatorLiveInvocationError::Artifact)?,
        normalized_response_digest: phala_operator_live_json_digest(&normalized_response)
            .map_err(PhalaOperatorLiveInvocationError::Artifact)?,
        trust_roots_digest: phala_operator_live_json_digest(&trust_roots)
            .map_err(PhalaOperatorLiveInvocationError::Artifact)?,
        redaction_report_digest: phala_operator_live_json_digest(&redaction_report)
            .map_err(PhalaOperatorLiveInvocationError::Artifact)?,
        raw_response_digest: raw_response_sha256.clone(),
        started_at: input.started_at,
        finished_at: input.request_time,
        timeout_seconds: input.timeout_seconds,
        retry_limit: input.retry_limit,
        provider_verdict: normalized_response.provider_verdict,
        claim_boundary: PHALA_OPERATOR_LIVE_CLAIM_BOUNDARY.to_owned(),
        non_claims: operator_live_invocation_non_claims(),
    };

    Ok(PhalaOperatorLiveArtifactBundle {
        request,
        normalized_response,
        trust_roots,
        redaction_report,
        audit,
        raw_response_sha256,
    })
}

fn operator_live_invocation_non_claims() -> BTreeSet<String> {
    BTreeSet::from([
        "not proof".to_owned(),
        "not local DCAP verification".to_owned(),
        "not managed-service signature/JWKS/JWT verification".to_owned(),
        "not TLS channel binding".to_owned(),
        "not benchmark evidence".to_owned(),
        "not global software-agent uniqueness".to_owned(),
        "not semantic correctness".to_owned(),
    ])
}

/// Deterministic SHA-256 digest over the crate-local JSON representation.
pub fn phala_operator_live_json_digest<T: Serialize>(
    value: &T,
) -> Result<String, PhalaOperatorLiveArtifactError> {
    let bytes =
        serde_json::to_vec(value).map_err(|error| PhalaOperatorLiveArtifactError::InvalidJson {
            path: "in-memory-json".to_owned(),
            message: error.to_string(),
        })?;
    Ok(sha256_hex(&bytes))
}

/// Deterministic fake client for hermetic tests and local verification plumbing.
#[derive(Clone, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
pub struct InMemoryPhalaManagedVerifierClient {
    responses:
        BTreeMap<(String, u64), Result<PhalaManagedVerifierResponse, PhalaManagedVerifierError>>,
}

impl InMemoryPhalaManagedVerifierClient {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn with_response(
        mut self,
        anchor_id: impl Into<String>,
        nonce: u64,
        response: PhalaManagedVerifierResponse,
    ) -> Self {
        self.responses
            .insert((anchor_id.into(), nonce), Ok(response));
        self
    }

    pub fn with_error(
        mut self,
        anchor_id: impl Into<String>,
        nonce: u64,
        error: PhalaManagedVerifierError,
    ) -> Self {
        self.responses.insert((anchor_id.into(), nonce), Err(error));
        self
    }
}

impl PhalaManagedVerifierClient for InMemoryPhalaManagedVerifierClient {
    fn verify(
        &self,
        request: &PhalaManagedVerifierRequest,
    ) -> Result<PhalaManagedVerifierResponse, PhalaManagedVerifierError> {
        self.responses
            .get(&(request.anchor_id.clone(), request.nonce))
            .cloned()
            .unwrap_or(Err(PhalaManagedVerifierError::ClientUnavailable))
    }
}

/// In-memory nonce replay guard for one verifier instance.
#[derive(Clone, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
pub struct PhalaReplayGuard {
    seen: BTreeSet<(String, u64)>,
}

impl PhalaReplayGuard {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn check_and_record(
        &mut self,
        anchor_id: &str,
        nonce: u64,
    ) -> Result<(), PhalaManagedVerifierError> {
        if !self.seen.insert((anchor_id.to_owned(), nonce)) {
            return Err(PhalaManagedVerifierError::ReplayedNonce);
        }
        Ok(())
    }
}

/// Hermetic Phala live managed-verifier preparation.
///
/// This type owns no credentials and performs no network calls. All provider
/// behavior enters through an injected client trait.
#[derive(Debug)]
pub struct PhalaLiveManagedVerifier<C> {
    pub client: C,
    pub agent_pubkey: Vec<u8>,
    pub case_hash: Vec<u8>,
    pub managed_verifier_endpoint_id: String,
    pub freshness_window: u64,
    pub expected_runtime_measurements: BTreeSet<String>,
    pub expected_image_digest: String,
    replay_guard: RefCell<PhalaReplayGuard>,
}

impl<C> PhalaLiveManagedVerifier<C> {
    pub fn new(
        client: C,
        agent_pubkey: impl Into<Vec<u8>>,
        case_hash: impl Into<Vec<u8>>,
        managed_verifier_endpoint_id: impl Into<String>,
        freshness_window: u64,
        expected_runtime_measurements: BTreeSet<String>,
        expected_image_digest: impl Into<String>,
    ) -> Self {
        Self {
            client,
            agent_pubkey: agent_pubkey.into(),
            case_hash: case_hash.into(),
            managed_verifier_endpoint_id: managed_verifier_endpoint_id.into(),
            freshness_window,
            expected_runtime_measurements,
            expected_image_digest: expected_image_digest.into(),
            replay_guard: RefCell::new(PhalaReplayGuard::new()),
        }
    }
}

impl<C: PhalaManagedVerifierClient> PhalaLiveManagedVerifier<C> {
    pub fn verify_request(
        &self,
        request: &PhalaManagedVerifierRequest,
    ) -> Result<VerifiedAttestation, PhalaManagedVerifierError> {
        let response = self.client.verify(request)?;
        self.verify_response(request, response)
    }

    fn verify_response(
        &self,
        request: &PhalaManagedVerifierRequest,
        response: PhalaManagedVerifierResponse,
    ) -> Result<VerifiedAttestation, PhalaManagedVerifierError> {
        validate_phala_managed_response(request, &response)?;
        self.replay_guard
            .borrow_mut()
            .check_and_record(&request.anchor_id, request.nonce)?;

        let mut verifier_trust_roots = response.provider_trust_roots;
        verifier_trust_roots.insert(TrustRoot::HardwareVendor(VendorId(format!(
            "expected-compose-hash:{}",
            hex_lower(&request.expected_compose_hash)
        ))));
        verifier_trust_roots.insert(TrustRoot::HardwareVendor(VendorId(format!(
            "expected-image-digest:{}",
            request.expected_image_digest
        ))));

        Ok(VerifiedAttestation {
            anchor_id: response.anchor_id,
            not_before: response.issued_at,
            not_after: response.expires_at,
            verifier_trust_roots,
        })
    }
}

impl<C: PhalaManagedVerifierClient> AttestationVerifier for PhalaLiveManagedVerifier<C> {
    fn verify(
        &self,
        token: &hsai_attestation::Token,
        expected_nonce: u64,
        expected_report_data: &[u8],
        expected_measurements: &[u8],
        anchor_id: &str,
        now: u64,
    ) -> Result<VerifiedAttestation, VerifyError> {
        if token.anchor_id != anchor_id {
            return Err(VerifyError::AnchorMismatch);
        }
        if token.nonce != expected_nonce {
            return Err(VerifyError::NonceMismatch);
        }
        if token.report_data != expected_report_data {
            return Err(VerifyError::ReportDataMismatch);
        }
        if token.measurements != expected_measurements {
            return Err(VerifyError::MeasurementMismatch);
        }

        let request = PhalaManagedVerifierRequest {
            anchor_id: anchor_id.to_owned(),
            agent_pubkey: self.agent_pubkey.clone(),
            case_hash: self.case_hash.clone(),
            nonce: expected_nonce,
            expected_report_data_binding: expected_report_data.to_vec(),
            expected_compose_hash: expected_measurements.to_vec(),
            expected_runtime_measurements: self.expected_runtime_measurements.clone(),
            expected_image_digest: self.expected_image_digest.clone(),
            freshness_window: self.freshness_window,
            managed_verifier_endpoint_id: self.managed_verifier_endpoint_id.clone(),
            request_time: now,
        };

        self.verify_request(&request)
            .map_err(|error| error.as_verify_error())
    }
}

fn validate_phala_managed_response(
    request: &PhalaManagedVerifierRequest,
    response: &PhalaManagedVerifierResponse,
) -> Result<(), PhalaManagedVerifierError> {
    if response.raw_response_digest.is_empty() || response.expires_at < response.issued_at {
        return Err(PhalaManagedVerifierError::MalformedResponse);
    }
    if response.provider != PHALA_LIVE_PROVIDER {
        return Err(PhalaManagedVerifierError::WrongProvider);
    }
    if response.verification_mode != PHALA_LIVE_MODE {
        return Err(PhalaManagedVerifierError::UnsupportedMode);
    }
    if response.provider_verdict != PhalaManagedVerifierVerdict::Accepted {
        return Err(PhalaManagedVerifierError::ProviderRejected);
    }
    if request.request_time < response.issued_at
        || request.request_time > response.expires_at
        || request.request_time.saturating_sub(response.issued_at) > request.freshness_window
    {
        return Err(PhalaManagedVerifierError::StaleResponse);
    }
    if response.anchor_id != request.anchor_id {
        return Err(PhalaManagedVerifierError::AnchorMismatch);
    }
    if response.nonce != request.nonce {
        return Err(PhalaManagedVerifierError::NonceMismatch);
    }
    if response.report_data != request.expected_report_data_binding {
        return Err(PhalaManagedVerifierError::ReportDataMismatch);
    }
    if response.compose_hash != request.expected_compose_hash {
        return Err(PhalaManagedVerifierError::ComposeHashMismatch);
    }
    if response.runtime_measurements != request.expected_runtime_measurements {
        return Err(PhalaManagedVerifierError::RuntimeMeasurementMismatch);
    }
    if response.image_digest != request.expected_image_digest {
        return Err(PhalaManagedVerifierError::ImageDigestMismatch);
    }
    if !has_hardware_root_prefix(
        &response.provider_trust_roots,
        &format!(
            "phala-managed-verifier:{}",
            request.managed_verifier_endpoint_id
        ),
    ) || !has_hardware_root_prefix(&response.provider_trust_roots, "dstack-runtime-format:")
        || !has_hardware_root_prefix(
            &response.provider_trust_roots,
            "provider-disclosed-hardware-root:",
        )
    {
        return Err(PhalaManagedVerifierError::MissingTrustRoot);
    }
    Ok(())
}

fn validate_operator_live_file_set(
    files: &BTreeMap<String, Vec<u8>>,
) -> Result<(), PhalaOperatorLiveArtifactError> {
    let required = required_operator_live_paths();
    for path in files.keys() {
        validate_operator_live_path(path)?;
        if !required.contains(path.as_str()) {
            return Err(PhalaOperatorLiveArtifactError::UnexpectedFile(path.clone()));
        }
    }
    for path in required {
        if !files.contains_key(path) {
            return Err(PhalaOperatorLiveArtifactError::MissingFile(path.to_owned()));
        }
    }
    Ok(())
}

fn serialize_operator_live_artifact_bundle(
    bundle: &PhalaOperatorLiveArtifactBundle,
) -> Result<BTreeMap<String, Vec<u8>>, PhalaOperatorLiveArtifactError> {
    Ok(BTreeMap::from([
        (
            PHALA_OPERATOR_LIVE_REQUEST_PATH.to_owned(),
            serialize_operator_live_json(PHALA_OPERATOR_LIVE_REQUEST_PATH, &bundle.request)?,
        ),
        (
            PHALA_OPERATOR_LIVE_NORMALIZED_RESPONSE_PATH.to_owned(),
            serialize_operator_live_json(
                PHALA_OPERATOR_LIVE_NORMALIZED_RESPONSE_PATH,
                &bundle.normalized_response,
            )?,
        ),
        (
            PHALA_OPERATOR_LIVE_TRUST_ROOTS_PATH.to_owned(),
            serialize_operator_live_json(
                PHALA_OPERATOR_LIVE_TRUST_ROOTS_PATH,
                &bundle.trust_roots,
            )?,
        ),
        (
            PHALA_OPERATOR_LIVE_REDACTION_REPORT_PATH.to_owned(),
            serialize_operator_live_json(
                PHALA_OPERATOR_LIVE_REDACTION_REPORT_PATH,
                &bundle.redaction_report,
            )?,
        ),
        (
            PHALA_OPERATOR_LIVE_AUDIT_PATH.to_owned(),
            serialize_operator_live_json(PHALA_OPERATOR_LIVE_AUDIT_PATH, &bundle.audit)?,
        ),
        (
            PHALA_OPERATOR_LIVE_RAW_RESPONSE_DIGEST_PATH.to_owned(),
            bundle.raw_response_sha256.as_bytes().to_vec(),
        ),
    ]))
}

fn serialize_operator_live_json<T: Serialize>(
    path: &str,
    value: &T,
) -> Result<Vec<u8>, PhalaOperatorLiveArtifactError> {
    serde_json::to_vec(value).map_err(|error| PhalaOperatorLiveArtifactError::InvalidJson {
        path: path.to_owned(),
        message: error.to_string(),
    })
}

fn validate_operator_live_output_root(
    output_root: &Path,
) -> Result<PathBuf, PhalaOperatorLiveArtifactError> {
    if output_root.as_os_str().is_empty() {
        return Err(PhalaOperatorLiveArtifactError::OutputRootInvalid {
            path: path_display(output_root),
            reason: "empty output root".to_owned(),
        });
    }
    reject_symlink_path(output_root)?;
    let metadata = fs::metadata(output_root).map_err(|error| {
        PhalaOperatorLiveArtifactError::OutputRootInvalid {
            path: path_display(output_root),
            reason: error.to_string(),
        }
    })?;
    if !metadata.is_dir() {
        return Err(PhalaOperatorLiveArtifactError::OutputRootInvalid {
            path: path_display(output_root),
            reason: "output root is not a directory".to_owned(),
        });
    }

    let canonical = fs::canonicalize(output_root).map_err(|error| {
        PhalaOperatorLiveArtifactError::OutputRootInvalid {
            path: path_display(output_root),
            reason: error.to_string(),
        }
    })?;
    if looks_like_workspace_repo_root(&canonical) {
        return Err(PhalaOperatorLiveArtifactError::OutputRootInvalid {
            path: path_display(output_root),
            reason: "repository root is not an operator artifact output root".to_owned(),
        });
    }
    Ok(canonical)
}

fn looks_like_workspace_repo_root(path: &Path) -> bool {
    path.join(".git").exists()
        && path.join("Cargo.toml").is_file()
        && path.join("crates").is_dir()
        && path.join("docs").is_dir()
}

fn prepare_operator_live_output_root(
    output_root: &Path,
    overwrite: PhalaOperatorLiveOutputOverwriteMode,
) -> Result<(), PhalaOperatorLiveArtifactError> {
    let mut has_operator_live = false;
    for entry in read_dir(output_root)? {
        let entry = dir_entry(entry, output_root)?;
        let path = entry.path();
        reject_symlink_path(&path)?;
        let name = entry_file_name(&entry)?;
        if name == "operator-live" {
            has_operator_live = true;
            if !entry_file_type(&entry)?.is_dir() {
                return Err(PhalaOperatorLiveArtifactError::UnexpectedFile(name));
            }
        } else {
            return Err(PhalaOperatorLiveArtifactError::UnexpectedFile(name));
        }
    }

    if has_operator_live {
        read_phala_operator_live_artifact_output_root(output_root)?;
        if overwrite == PhalaOperatorLiveOutputOverwriteMode::RefuseExisting {
            return Err(
                PhalaOperatorLiveArtifactError::ExistingBundleRequiresOverwrite(
                    "operator-live".to_owned(),
                ),
            );
        }
    }
    Ok(())
}

fn write_operator_live_files_to_root(
    root: &Path,
    files: &BTreeMap<String, Vec<u8>>,
) -> Result<(), PhalaOperatorLiveArtifactError> {
    validate_operator_live_file_set(files)?;
    for (logical_path, bytes) in files {
        validate_operator_live_path(logical_path)?;
        let destination = root.join(logical_path);
        if let Some(parent) = destination.parent() {
            create_dir_all(parent)?;
        }
        if destination.exists() {
            return Err(PhalaOperatorLiveArtifactError::UnexpectedFile(
                logical_path.clone(),
            ));
        }
        fs::write(&destination, bytes).map_err(|error| {
            PhalaOperatorLiveArtifactError::Filesystem {
                path: path_display(&destination),
                message: error.to_string(),
            }
        })?;
        reject_symlink_path(&destination)?;
    }
    Ok(())
}

fn collect_operator_live_materialized_files(
    output_root: &Path,
) -> Result<BTreeMap<String, Vec<u8>>, PhalaOperatorLiveArtifactError> {
    let mut files = BTreeMap::new();
    let mut saw_operator_live = false;
    for entry in read_dir(output_root)? {
        let entry = dir_entry(entry, output_root)?;
        let path = entry.path();
        reject_symlink_path(&path)?;
        let name = entry_file_name(&entry)?;
        if name != "operator-live" {
            return Err(PhalaOperatorLiveArtifactError::UnexpectedFile(name));
        }
        if !entry_file_type(&entry)?.is_dir() {
            return Err(PhalaOperatorLiveArtifactError::UnexpectedFile(name));
        }
        saw_operator_live = true;
        for child in read_dir(&path)? {
            let child = dir_entry(child, &path)?;
            let child_path = child.path();
            reject_symlink_path(&child_path)?;
            let child_name = entry_file_name(&child)?;
            let logical_path = format!("operator-live/{child_name}");
            validate_operator_live_path(&logical_path)?;
            if !entry_file_type(&child)?.is_file() {
                return Err(PhalaOperatorLiveArtifactError::UnexpectedFile(logical_path));
            }
            let bytes = fs::read(&child_path).map_err(|error| {
                PhalaOperatorLiveArtifactError::Filesystem {
                    path: path_display(&child_path),
                    message: error.to_string(),
                }
            })?;
            files.insert(logical_path, bytes);
        }
    }
    if !saw_operator_live {
        return Err(PhalaOperatorLiveArtifactError::MissingFile(
            PHALA_OPERATOR_LIVE_REQUEST_PATH.to_owned(),
        ));
    }
    Ok(files)
}

fn read_dir(path: &Path) -> Result<fs::ReadDir, PhalaOperatorLiveArtifactError> {
    fs::read_dir(path).map_err(|error| PhalaOperatorLiveArtifactError::Filesystem {
        path: path_display(path),
        message: error.to_string(),
    })
}

fn dir_entry(
    entry: Result<fs::DirEntry, std::io::Error>,
    parent: &Path,
) -> Result<fs::DirEntry, PhalaOperatorLiveArtifactError> {
    entry.map_err(|error| PhalaOperatorLiveArtifactError::Filesystem {
        path: path_display(parent),
        message: error.to_string(),
    })
}

fn create_dir(path: &Path) -> Result<(), PhalaOperatorLiveArtifactError> {
    fs::create_dir(path).map_err(|error| PhalaOperatorLiveArtifactError::Filesystem {
        path: path_display(path),
        message: error.to_string(),
    })
}

fn create_dir_all(path: &Path) -> Result<(), PhalaOperatorLiveArtifactError> {
    fs::create_dir_all(path).map_err(|error| PhalaOperatorLiveArtifactError::Filesystem {
        path: path_display(path),
        message: error.to_string(),
    })
}

fn remove_dir_all(path: &Path) -> Result<(), PhalaOperatorLiveArtifactError> {
    fs::remove_dir_all(path).map_err(|error| PhalaOperatorLiveArtifactError::Filesystem {
        path: path_display(path),
        message: error.to_string(),
    })
}

fn rename_path(from: &Path, to: &Path) -> Result<(), PhalaOperatorLiveArtifactError> {
    fs::rename(from, to).map_err(|error| PhalaOperatorLiveArtifactError::Filesystem {
        path: format!("{} -> {}", path_display(from), path_display(to)),
        message: error.to_string(),
    })
}

fn reject_symlink_path(path: &Path) -> Result<(), PhalaOperatorLiveArtifactError> {
    if fs::symlink_metadata(path)
        .map(|metadata| metadata.file_type().is_symlink())
        .unwrap_or(false)
    {
        return Err(PhalaOperatorLiveArtifactError::SymlinkPath(path_display(
            path,
        )));
    }
    Ok(())
}

fn entry_file_name(entry: &fs::DirEntry) -> Result<String, PhalaOperatorLiveArtifactError> {
    entry
        .file_name()
        .into_string()
        .map_err(|_| PhalaOperatorLiveArtifactError::UnsafePath(path_display(&entry.path())))
}

fn entry_file_type(entry: &fs::DirEntry) -> Result<fs::FileType, PhalaOperatorLiveArtifactError> {
    entry
        .file_type()
        .map_err(|error| PhalaOperatorLiveArtifactError::Filesystem {
            path: path_display(&entry.path()),
            message: error.to_string(),
        })
}

fn operator_live_staging_dir_name() -> String {
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_nanos())
        .unwrap_or_default();
    format!(".operator-live.tmp.{nanos}")
}

fn required_operator_live_paths() -> BTreeSet<&'static str> {
    BTreeSet::from([
        PHALA_OPERATOR_LIVE_REQUEST_PATH,
        PHALA_OPERATOR_LIVE_NORMALIZED_RESPONSE_PATH,
        PHALA_OPERATOR_LIVE_TRUST_ROOTS_PATH,
        PHALA_OPERATOR_LIVE_REDACTION_REPORT_PATH,
        PHALA_OPERATOR_LIVE_AUDIT_PATH,
        PHALA_OPERATOR_LIVE_RAW_RESPONSE_DIGEST_PATH,
    ])
}

fn validate_operator_live_path(path: &str) -> Result<(), PhalaOperatorLiveArtifactError> {
    if path.is_empty()
        || path.starts_with('/')
        || path.contains('\\')
        || path
            .split('/')
            .any(|segment| segment.is_empty() || segment == "." || segment == "..")
    {
        return Err(PhalaOperatorLiveArtifactError::UnsafePath(path.to_owned()));
    }
    Ok(())
}

fn path_display(path: &Path) -> String {
    path.display().to_string()
}

fn parse_operator_live_json<T: for<'de> Deserialize<'de>>(
    path: &str,
    bytes: &[u8],
) -> Result<T, PhalaOperatorLiveArtifactError> {
    serde_json::from_slice(bytes).map_err(|error| PhalaOperatorLiveArtifactError::InvalidJson {
        path: path.to_owned(),
        message: error.to_string(),
    })
}

fn validate_operator_live_schema(
    field: &str,
    actual: &str,
) -> Result<(), PhalaOperatorLiveArtifactError> {
    if actual != PHALA_OPERATOR_LIVE_ARTIFACT_SCHEMA_VERSION {
        return Err(PhalaOperatorLiveArtifactError::SchemaVersionMismatch {
            field: field.to_owned(),
            actual: actual.to_owned(),
        });
    }
    Ok(())
}

fn validate_operator_live_provider_consistency(
    bundle: &PhalaOperatorLiveArtifactBundle,
) -> Result<(), PhalaOperatorLiveArtifactError> {
    if bundle.audit.provider != PHALA_LIVE_PROVIDER
        || bundle.audit.verification_mode != PHALA_LIVE_MODE
        || bundle.audit.provider_verdict != bundle.normalized_response.provider_verdict
        || bundle.trust_roots.provider != PHALA_LIVE_PROVIDER
        || bundle.trust_roots.verification_mode != PHALA_LIVE_MODE
        || bundle.normalized_response.provider != PHALA_LIVE_PROVIDER
        || bundle.normalized_response.verification_mode != PHALA_LIVE_MODE
    {
        return Err(PhalaOperatorLiveArtifactError::ProviderMismatch);
    }
    Ok(())
}

fn validate_operator_live_trust_roots(
    bundle: &PhalaOperatorLiveArtifactBundle,
) -> Result<(), PhalaOperatorLiveArtifactError> {
    if bundle.trust_roots.roots != bundle.normalized_response.provider_trust_roots {
        return Err(PhalaOperatorLiveArtifactError::TrustRootMismatch);
    }
    Ok(())
}

fn validate_operator_live_audit_digests(
    bundle: &PhalaOperatorLiveArtifactBundle,
) -> Result<(), PhalaOperatorLiveArtifactError> {
    expect_digest_match(
        "audit.request_digest",
        &bundle.audit.request_digest,
        &phala_operator_live_json_digest(&bundle.request)?,
    )?;
    expect_digest_match(
        "audit.normalized_response_digest",
        &bundle.audit.normalized_response_digest,
        &phala_operator_live_json_digest(&bundle.normalized_response)?,
    )?;
    expect_digest_match(
        "audit.trust_roots_digest",
        &bundle.audit.trust_roots_digest,
        &phala_operator_live_json_digest(&bundle.trust_roots)?,
    )?;
    expect_digest_match(
        "audit.redaction_report_digest",
        &bundle.audit.redaction_report_digest,
        &phala_operator_live_json_digest(&bundle.redaction_report)?,
    )?;
    expect_digest_match(
        "audit.raw_response_digest",
        &bundle.audit.raw_response_digest,
        &bundle.raw_response_sha256,
    )?;
    expect_digest_match(
        "response.raw_response_digest",
        &hex_lower(&bundle.normalized_response.raw_response_digest),
        &bundle.raw_response_sha256,
    )?;
    Ok(())
}

fn expect_digest_match(
    field: &str,
    actual: &str,
    expected: &str,
) -> Result<(), PhalaOperatorLiveArtifactError> {
    validate_operator_live_digest(field, actual)?;
    validate_operator_live_digest(field, expected)?;
    if actual != expected {
        return Err(PhalaOperatorLiveArtifactError::DigestMismatch {
            field: field.to_owned(),
            actual: actual.to_owned(),
            expected: expected.to_owned(),
        });
    }
    Ok(())
}

fn validate_operator_live_digest(
    field: &str,
    value: &str,
) -> Result<(), PhalaOperatorLiveArtifactError> {
    if value.len() != 64
        || !value
            .as_bytes()
            .iter()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(byte))
    {
        return Err(PhalaOperatorLiveArtifactError::InvalidDigest {
            field: field.to_owned(),
            value: value.to_owned(),
        });
    }
    Ok(())
}

fn validate_operator_live_redaction_report(
    report: &PhalaOperatorLiveRedactionReport,
) -> Result<(), PhalaOperatorLiveArtifactError> {
    if report.digest_algorithm != "sha256" {
        return Err(PhalaOperatorLiveArtifactError::InvalidDigest {
            field: "redaction_report.digest_algorithm".to_owned(),
            value: report.digest_algorithm.clone(),
        });
    }

    for (field, retained) in &report.retained_fields {
        if retained.rationale.trim().is_empty() {
            return Err(PhalaOperatorLiveArtifactError::RedactionRationaleMissing(
                field.clone(),
            ));
        }
        if looks_secret_shaped(field) || looks_secret_shaped(&retained.value) {
            return Err(PhalaOperatorLiveArtifactError::RedactionSecretRetained(
                field.clone(),
            ));
        }
    }
    Ok(())
}

fn validate_operator_live_non_claims(
    non_claims: &BTreeSet<String>,
) -> Result<(), PhalaOperatorLiveArtifactError> {
    for required in [
        "not proof",
        "not local DCAP verification",
        "not benchmark evidence",
        "not global software-agent uniqueness",
        "not semantic correctness",
    ] {
        if !non_claims.iter().any(|claim| claim == required) {
            return Err(PhalaOperatorLiveArtifactError::MissingNonClaim(
                required.to_owned(),
            ));
        }
    }
    Ok(())
}

fn looks_secret_shaped(value: &str) -> bool {
    let value = value.to_ascii_lowercase();
    [
        "authorization",
        "bearer ",
        "api_key",
        "apikey",
        "private_key",
        "cookie",
        "secret",
        "token",
        "aws_access_key",
        "aws_secret",
        "credential",
    ]
    .iter()
    .any(|needle| value.contains(needle))
}

fn has_hardware_root_prefix(roots: &BTreeSet<TrustRoot>, prefix: &str) -> bool {
    roots.iter().any(|root| {
        matches!(
            root,
            TrustRoot::HardwareVendor(VendorId(value)) if value.starts_with(prefix)
        )
    })
}

fn hex_lower(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn sha256_hex(bytes: &[u8]) -> String {
    hex_lower(&Sha256::digest(bytes))
}

#[cfg(test)]
mod tests {
    use super::*;
    use hsai_agent_case::{ActionId, MemoryRoot, ModelId, OracleContract, Verdict};
    use hsai_attestation::{report_data_binding, AttestationLane, Token};
    use hsai_claim_envelope::{
        admits, conjoin, AcceptancePolicy, SubjectId, TrustRootClass, VendorId,
    };
    use hsai_distinct_agent::{distinctness, AnchorBundle, DistinctAgentLane};
    use proptest::prelude::*;

    const NOW: u64 = 150;
    const NONCE: u64 = 42;

    fn subject(id: &str) -> SubjectId {
        SubjectId(id.to_owned())
    }

    fn anchor() -> Anchor {
        Anchor::HardwareAttested {
            vendor: "phala-dstack-tdx".to_owned(),
            device: "agent-case-emitter-v1".to_owned(),
        }
    }

    fn case() -> AgentCase {
        let subject = subject("agent-phala");
        AgentCase {
            action: ActionId("phala-action".to_owned()),
            subject: subject.clone(),
            claimed_model: ModelId("phala-agent-case-emitter".to_owned()),
            memory_root: MemoryRoot([5; 32]),
            observed_at: NOW,
            oracle: OracleContract {
                expected: Verdict::Accept,
                target_guarantees: BTreeSet::from([distinctness(&subject)]),
                excluded: BTreeSet::new(),
            },
        }
    }

    fn report_data() -> Vec<u8> {
        report_data_binding(b"phala-agent-pubkey", NONCE, b"phala-case-hash")
    }

    fn compose_hash() -> Vec<u8> {
        b"compose-hash:phala-agent-case-emitter-v1".to_vec()
    }

    fn docker_digest() -> Vec<u8> {
        b"docker-image-digest:v1".to_vec()
    }

    fn evidence(mode: PhalaVerifyMode) -> PhalaEvidence {
        PhalaEvidence {
            anchor_id: anchor().anchor_id(),
            quote_hex: match mode {
                PhalaVerifyMode::Local => "fixture-tdx-quote:accepted".to_owned(),
                PhalaVerifyMode::ManagedApi => "managed-api:accepted".to_owned(),
            },
            report_data: report_data(),
            compose_hash: compose_hash(),
            event_log: Some(b"event-log-replayed".to_vec()),
            docker_image_digest: Some(docker_digest()),
            not_before: 100,
            not_after: 300,
        }
    }

    fn policy(mode: PhalaVerifyMode) -> PhalaTrustPolicy {
        PhalaTrustPolicy {
            expected_anchor_id: anchor().anchor_id(),
            expected_report_data: report_data(),
            expected_compose_hash: compose_hash(),
            expected_docker_image_digest: Some(docker_digest()),
            require_event_log_replay: true,
            allow_managed_api: mode == PhalaVerifyMode::ManagedApi,
            now: NOW,
        }
    }

    fn verifier(mode: PhalaVerifyMode) -> PhalaAttestationVerifier {
        PhalaAttestationVerifier::new(evidence(mode), policy(mode), mode)
    }

    fn input() -> AttestationInput {
        AttestationInput {
            anchor: anchor(),
            token: Token {
                signed_jwt: None,
                anchor_id: anchor().anchor_id(),
                nonce: NONCE,
                report_data: report_data(),
                measurements: compose_hash(),
                not_before: 100,
                not_after: 300,
            },
            expected_nonce: NONCE,
            expected_report_data: report_data(),
            expected_measurements: compose_hash(),
        }
    }

    fn distinct_policy(subject: &SubjectId) -> AcceptancePolicy {
        AcceptancePolicy {
            require: BTreeSet::from([distinctness(subject)]),
            min_maturity: Maturity::Attested,
            forbid_roots: BTreeSet::<TrustRootClass>::new(),
            require_closed: true,
            at: NOW,
        }
    }

    #[test]
    fn ph_1_report_data_binding() {
        let evidence = evidence(PhalaVerifyMode::Local);
        assert_eq!(
            verify_report_data_binding(&evidence, &report_data()),
            Ok(())
        );
        assert_eq!(
            parse_phala_evidence(&serde_json::to_vec(&evidence).expect("fixture serializes")),
            Ok(evidence)
        );
    }

    #[test]
    fn ph_2_report_data_mismatch() {
        let mut evidence = evidence(PhalaVerifyMode::Local);
        evidence.report_data.push(1);
        let verifier = PhalaAttestationVerifier::new(
            evidence,
            policy(PhalaVerifyMode::Local),
            PhalaVerifyMode::Local,
        );

        assert_eq!(
            verifier.verify(
                &input().token,
                NONCE,
                &report_data(),
                &compose_hash(),
                &anchor().anchor_id(),
                NOW
            ),
            Err(VerifyError::ReportDataMismatch)
        );
    }

    #[test]
    fn ph_3_compose_hash_mismatch() {
        let mut trust_policy = policy(PhalaVerifyMode::Local);
        trust_policy.expected_compose_hash = b"wrong-compose".to_vec();
        let verifier = PhalaAttestationVerifier::new(
            evidence(PhalaVerifyMode::Local),
            trust_policy,
            PhalaVerifyMode::Local,
        );

        assert_eq!(
            verifier.verify(
                &input().token,
                NONCE,
                &report_data(),
                &compose_hash(),
                &anchor().anchor_id(),
                NOW
            ),
            Err(VerifyError::MeasurementMismatch)
        );
    }

    #[test]
    fn ph_4_expired_evidence() {
        let mut evidence = evidence(PhalaVerifyMode::Local);
        evidence.not_after = NOW - 1;
        let verifier = PhalaAttestationVerifier::new(
            evidence,
            policy(PhalaVerifyMode::Local),
            PhalaVerifyMode::Local,
        );

        assert_eq!(
            verifier.verify(
                &input().token,
                NONCE,
                &report_data(),
                &compose_hash(),
                &anchor().anchor_id(),
                NOW
            ),
            Err(VerifyError::Expired)
        );
    }

    #[test]
    fn ph_5_managed_api_disallowed() {
        let mut trust_policy = policy(PhalaVerifyMode::ManagedApi);
        trust_policy.allow_managed_api = false;
        let verifier = PhalaAttestationVerifier::new(
            evidence(PhalaVerifyMode::ManagedApi),
            trust_policy,
            PhalaVerifyMode::ManagedApi,
        );
        let env = PhalaAttestationLane::new(verifier, vec![input()]).evaluate(&case());

        assert!(env.guarantees.is_empty());
        assert!(env.trust_roots.is_empty());
        assert_eq!(env.maturity, Maturity::Stub);
    }

    #[test]
    fn ph_6_accepted_evidence_closes_distinctness() {
        let case = case();
        let distinct =
            DistinctAgentLane::new(AnchorBundle(BTreeSet::from([anchor()]))).evaluate(&case);
        let attestation =
            AttestationLane::new(verifier(PhalaVerifyMode::Local), vec![input()]).evaluate(&case);
        let closed = conjoin(distinct, attestation);

        assert!(closed.assumptions.is_empty());
        assert_eq!(closed.maturity, Maturity::Attested);
        assert_eq!(admits(distinct_policy(&case.subject), closed), Ok(()));
    }

    #[test]
    fn ph_7_managed_api_trust_root_is_visible() {
        let case = case();
        let env = PhalaAttestationLane::new(verifier(PhalaVerifyMode::ManagedApi), vec![input()])
            .evaluate(&case);

        assert_eq!(env.maturity, Maturity::Attested);
        assert!(env
            .trust_roots
            .contains(&TrustRoot::HardwareVendor(VendorId(anchor().anchor_id()))));
        assert!(env.trust_roots.contains(&TrustRoot::VerifyingKey(VkId(
            PHALA_MANAGED_VERIFIER_ROOT.to_owned()
        ))));
    }

    fn mode_strategy() -> impl Strategy<Value = PhalaVerifyMode> {
        prop_oneof![
            Just(PhalaVerifyMode::Local),
            Just(PhalaVerifyMode::ManagedApi)
        ]
    }

    proptest! {
        #[test]
        fn php_1_determinism(mode in mode_strategy()) {
            let verifier = verifier(mode);
            let first = verifier.verify(&input().token, NONCE, &report_data(), &compose_hash(), &anchor().anchor_id(), NOW);
            let second = verifier.verify(&input().token, NONCE, &report_data(), &compose_hash(), &anchor().anchor_id(), NOW);
            prop_assert_eq!(first, second);
        }

        #[test]
        fn php_2_single_field_mutation_rejects(field in 0_u8..4) {
            let mut evidence = evidence(PhalaVerifyMode::Local);
            match field {
                0 => evidence.report_data.push(1),
                1 => evidence.compose_hash.push(1),
                2 => evidence.anchor_id.push_str("-wrong"),
                _ => evidence.not_after = NOW - 1,
            }
            let verifier = PhalaAttestationVerifier::new(evidence, policy(PhalaVerifyMode::Local), PhalaVerifyMode::Local);

            prop_assert!(verifier
                .verify(&input().token, NONCE, &report_data(), &compose_hash(), &anchor().anchor_id(), NOW)
                .is_err());
        }

        #[test]
        fn php_3_maturity_ceiling(mode in mode_strategy()) {
            let env = PhalaAttestationLane::new(verifier(mode), vec![input()]).evaluate(&case());
            prop_assert!(env.maturity <= Maturity::Attested);
        }

        #[test]
        fn php_4_no_hidden_trust_root(mode in mode_strategy()) {
            let env = PhalaAttestationLane::new(verifier(mode), vec![input()]).evaluate(&case());
            let expected = verifier(mode).trust_roots_for(&anchor());

            prop_assert_eq!(&env.trust_roots, &expected);
            if mode == PhalaVerifyMode::ManagedApi {
                prop_assert!(env.trust_roots.contains(&TrustRoot::VerifyingKey(VkId(
                    PHALA_MANAGED_VERIFIER_ROOT.to_owned()
                ))));
            }
        }
    }
}

//! Deterministic fixture-oriented Phala/dstack attestation backend preparation.
//!
//! This crate does not perform real TDX quote verification, managed-service
//! signature verification, JWKS/JWT validation, or network calls. It validates a
//! small local evidence model so the HSAI attestation seam can be tested before
//! real Phala artifacts are introduced.

use hsai_agent_case::{AgentCase, EvidenceLane};
use hsai_attestation::{AttestationInput, AttestationVerifier, VerifiedAttestation, VerifyError};
use hsai_claim_envelope::{ClaimEnvelope, LaneId, Maturity, TimeWindow, TrustRoot, VkId};
use hsai_distinct_agent::Anchor;
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

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

/// Claim boundary for this crate.
pub const CLAIM_BOUNDARY: &str =
    "fixture Phala/dstack backend preparation; not real hardware verification or proof";

const LOCAL_FIXTURE_QUOTE_PREFIX: &str = "fixture-tdx-quote:";
const MANAGED_API_ACCEPTED: &str = "managed-api:accepted";
const PHALA_MANAGED_VERIFIER_ROOT: &str = "phala-managed-verifier-api";

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

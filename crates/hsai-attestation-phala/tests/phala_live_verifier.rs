use hsai_agent_case::EvidenceLane;
use hsai_agent_case::{ActionId, AgentCase, MemoryRoot, ModelId, OracleContract, Verdict};
use hsai_attestation::{
    report_data_binding, AttestationInput, AttestationLane, AttestationVerifier, Token,
};
use hsai_attestation_phala::{
    InMemoryPhalaManagedVerifierClient, PhalaLiveManagedVerifier, PhalaManagedVerifierError,
    PhalaManagedVerifierRequest, PhalaManagedVerifierResponse, PhalaManagedVerifierVerdict,
};
use hsai_claim_envelope::{Maturity, SubjectId, TrustRoot, VendorId};
use hsai_distinct_agent::{distinctness, Anchor};
use std::collections::BTreeSet;

const NOW: u64 = 1_000;
const NONCE: u64 = 99;
const ENDPOINT_ID: &str = "phala-trust-center:test";
const IMAGE_DIGEST: &str = "sha256:0123456789abcdef";
const AGENT_PUBKEY: &[u8] = b"phala-live-agent-key";
const CASE_HASH: &[u8] = b"phala-live-case";

fn anchor() -> Anchor {
    Anchor::HardwareAttested {
        vendor: "phala-dstack".to_owned(),
        device: "hermetic-live-verifier".to_owned(),
    }
}

fn subject() -> SubjectId {
    SubjectId("phala-live-agent".to_owned())
}

fn case() -> AgentCase {
    AgentCase {
        action: ActionId("phala-live-action".to_owned()),
        subject: subject(),
        claimed_model: ModelId("phala-live-model".to_owned()),
        memory_root: MemoryRoot([9; 32]),
        observed_at: NOW,
        oracle: OracleContract {
            expected: Verdict::Accept,
            target_guarantees: BTreeSet::from([distinctness(&subject())]),
            excluded: BTreeSet::new(),
        },
    }
}

fn report_data() -> Vec<u8> {
    report_data_binding(AGENT_PUBKEY, NONCE, CASE_HASH)
}

fn compose_hash() -> Vec<u8> {
    b"compose-hash:phala-live-v1".to_vec()
}

fn runtime_measurements() -> BTreeSet<String> {
    BTreeSet::from([
        "rtmr0:aaaaaaaa".to_owned(),
        "rtmr1:bbbbbbbb".to_owned(),
        "rtmr2:cccccccc".to_owned(),
    ])
}

fn request() -> PhalaManagedVerifierRequest {
    PhalaManagedVerifierRequest {
        anchor_id: anchor().anchor_id(),
        agent_pubkey: AGENT_PUBKEY.to_vec(),
        case_hash: CASE_HASH.to_vec(),
        nonce: NONCE,
        expected_report_data_binding: report_data(),
        expected_compose_hash: compose_hash(),
        expected_runtime_measurements: runtime_measurements(),
        expected_image_digest: IMAGE_DIGEST.to_owned(),
        freshness_window: 200,
        managed_verifier_endpoint_id: ENDPOINT_ID.to_owned(),
        request_time: NOW,
    }
}

fn required_roots() -> BTreeSet<TrustRoot> {
    BTreeSet::from([
        TrustRoot::HardwareVendor(VendorId(format!("phala-managed-verifier:{ENDPOINT_ID}"))),
        TrustRoot::HardwareVendor(VendorId("dstack-runtime-format:v1".to_owned())),
        TrustRoot::HardwareVendor(VendorId(
            "provider-disclosed-hardware-root:intel-tdx".to_owned(),
        )),
    ])
}

fn response() -> PhalaManagedVerifierResponse {
    PhalaManagedVerifierResponse {
        provider: "phala-dstack".to_owned(),
        verification_mode: "live-managed-verifier".to_owned(),
        provider_verdict: PhalaManagedVerifierVerdict::Accepted,
        anchor_id: anchor().anchor_id(),
        nonce: NONCE,
        report_data: report_data(),
        compose_hash: compose_hash(),
        runtime_measurements: runtime_measurements(),
        image_digest: IMAGE_DIGEST.to_owned(),
        issued_at: NOW - 10,
        expires_at: NOW + 100,
        raw_response_digest: vec![7; 32],
        provider_trust_roots: required_roots(),
    }
}

fn token() -> Token {
    Token {
        signed_jwt: None,
        anchor_id: anchor().anchor_id(),
        nonce: NONCE,
        report_data: report_data(),
        measurements: compose_hash(),
        not_before: NOW - 10,
        not_after: NOW + 100,
    }
}

fn input() -> AttestationInput {
    AttestationInput {
        anchor: anchor(),
        token: token(),
        expected_nonce: NONCE,
        expected_report_data: report_data(),
        expected_measurements: compose_hash(),
    }
}

fn verifier_with_response(
    response: PhalaManagedVerifierResponse,
) -> PhalaLiveManagedVerifier<InMemoryPhalaManagedVerifierClient> {
    let request = request();
    let client = InMemoryPhalaManagedVerifierClient::new().with_response(
        request.anchor_id,
        request.nonce,
        response,
    );
    PhalaLiveManagedVerifier::new(
        client,
        AGENT_PUBKEY,
        CASE_HASH,
        ENDPOINT_ID,
        200,
        runtime_measurements(),
        IMAGE_DIGEST,
    )
}

#[test]
fn live_accepted_fake_response_maps_to_attested_with_roots() {
    let verifier = verifier_with_response(response());
    let env = AttestationLane::new(verifier, vec![input()]).evaluate(&case());

    assert_eq!(env.maturity, Maturity::Attested);
    assert!(!env.guarantees.is_empty());
    assert!(env
        .trust_roots
        .contains(&TrustRoot::HardwareVendor(VendorId(anchor().anchor_id()))));
    assert!(env
        .trust_roots
        .contains(&TrustRoot::HardwareVendor(VendorId(format!(
            "phala-managed-verifier:{ENDPOINT_ID}"
        )))));
    assert!(env
        .trust_roots
        .contains(&TrustRoot::HardwareVendor(VendorId(format!(
            "expected-image-digest:{IMAGE_DIGEST}"
        )))));
}

#[test]
fn provider_rejection_fails_closed_without_roots() {
    let mut rejected = response();
    rejected.provider_verdict = PhalaManagedVerifierVerdict::Rejected;
    let verifier = verifier_with_response(rejected);
    let env = AttestationLane::new(verifier, vec![input()]).evaluate(&case());

    assert_eq!(env.maturity, Maturity::Stub);
    assert!(env.guarantees.is_empty());
    assert!(env.trust_roots.is_empty());
}

#[test]
fn stale_response_fails_closed() {
    let mut stale = response();
    stale.issued_at = NOW - 300;
    stale.expires_at = NOW + 100;
    let verifier = verifier_with_response(stale);

    assert_eq!(
        verifier.verify_request(&request()),
        Err(PhalaManagedVerifierError::StaleResponse)
    );
}

#[test]
fn replayed_nonce_fails_closed_for_same_verifier_instance() {
    let verifier = verifier_with_response(response());

    assert!(verifier.verify_request(&request()).is_ok());
    assert_eq!(
        verifier.verify_request(&request()),
        Err(PhalaManagedVerifierError::ReplayedNonce)
    );
}

#[test]
fn anchor_and_report_data_mismatches_fail_closed() {
    let mut wrong_anchor = response();
    wrong_anchor.anchor_id = "wrong-anchor".to_owned();
    let verifier = verifier_with_response(wrong_anchor);
    assert_eq!(
        verifier.verify_request(&request()),
        Err(PhalaManagedVerifierError::AnchorMismatch)
    );

    let mut wrong_report_data = response();
    wrong_report_data.report_data.push(1);
    let verifier = verifier_with_response(wrong_report_data);
    assert_eq!(
        verifier.verify_request(&request()),
        Err(PhalaManagedVerifierError::ReportDataMismatch)
    );
}

#[test]
fn compose_runtime_image_and_missing_root_fail_closed() {
    let mut wrong_compose = response();
    wrong_compose.compose_hash.push(1);
    let verifier = verifier_with_response(wrong_compose);
    assert_eq!(
        verifier.verify_request(&request()),
        Err(PhalaManagedVerifierError::ComposeHashMismatch)
    );

    let mut wrong_runtime = response();
    wrong_runtime
        .runtime_measurements
        .insert("rtmr3:dddddddd".to_owned());
    let verifier = verifier_with_response(wrong_runtime);
    assert_eq!(
        verifier.verify_request(&request()),
        Err(PhalaManagedVerifierError::RuntimeMeasurementMismatch)
    );

    let mut wrong_image = response();
    wrong_image.image_digest = "sha256:bad".to_owned();
    let verifier = verifier_with_response(wrong_image);
    assert_eq!(
        verifier.verify_request(&request()),
        Err(PhalaManagedVerifierError::ImageDigestMismatch)
    );

    let mut missing_root = response();
    missing_root.provider_trust_roots = BTreeSet::new();
    let verifier = verifier_with_response(missing_root);
    assert_eq!(
        verifier.verify_request(&request()),
        Err(PhalaManagedVerifierError::MissingTrustRoot)
    );
}

#[test]
fn attestation_verifier_mapping_never_exceeds_attested() {
    let verifier = verifier_with_response(response());
    let verified = verifier
        .verify(
            &token(),
            NONCE,
            &report_data(),
            &compose_hash(),
            &anchor().anchor_id(),
            NOW,
        )
        .expect("fake response verifies");

    assert_eq!(verified.anchor_id, anchor().anchor_id());
    assert!(!verified.verifier_trust_roots.is_empty());
    let env =
        AttestationLane::new(verifier_with_response(response()), vec![input()]).evaluate(&case());
    assert!(env.maturity <= Maturity::Attested);
}

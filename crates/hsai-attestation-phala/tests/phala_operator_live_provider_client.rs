#![cfg(feature = "operator-live-provider")]

use hsai_attestation::report_data_binding;
use hsai_attestation_phala::{
    read_phala_operator_live_artifact_output_root, PhalaEnvCredentialProvider,
    PhalaManagedVerifierError, PhalaManagedVerifierRequest, PhalaManagedVerifierResponse,
    PhalaManagedVerifierVerdict, PhalaOperatorLiveClient, PhalaOperatorLiveCredential,
    PhalaOperatorLiveCredentialProvider, PhalaOperatorLiveInvocation,
    PhalaOperatorLiveInvocationError, PhalaOperatorLiveInvocationInput,
    PhalaOperatorLiveOutputOverwriteMode, PhalaOperatorLiveProviderClient,
    PhalaOperatorLiveProviderConfig, PhalaOperatorLiveProviderError, PhalaOperatorLiveRawResponse,
    PhalaOperatorLiveTransport, PHALA_OPERATOR_LIVE_CLAIM_BOUNDARY,
    PHALA_OPERATOR_LIVE_MAX_TIMEOUT_SECONDS,
};
use hsai_claim_envelope::{TrustRoot, VendorId};
use hsai_distinct_agent::Anchor;
use sha2::{Digest, Sha256};
use std::cell::RefCell;
use std::collections::BTreeSet;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Mutex, MutexGuard};

static TEMP_COUNTER: AtomicU64 = AtomicU64::new(0);
static ENV_LOCK: Mutex<()> = Mutex::new(());

const NOW: u64 = 4_000;
const NONCE: u64 = 606;
const ENDPOINT: &str = "https://operator.example.invalid/phala/managed-verify";
const CREDENTIAL_SOURCE: &str = "env:HSAI_TEST_PHALA_OPERATOR_TOKEN_PHASE_102";
const CREDENTIAL_VALUE: &str = "phase-102-secret-not-for-artifacts";
const IMAGE_DIGEST: &str = "sha256:102102102102";
const AGENT_PUBKEY: &[u8] = b"operator-live-provider-agent-key";
const CASE_HASH: &[u8] = b"operator-live-provider-case-hash";

#[derive(Debug)]
struct FakeTransport {
    response: Result<PhalaOperatorLiveRawResponse, PhalaOperatorLiveProviderError>,
    seen_endpoint: RefCell<Option<String>>,
    seen_body: RefCell<Vec<u8>>,
    seen_credential: RefCell<Vec<u8>>,
}

#[derive(Debug)]
struct PanicTransport;

impl PhalaOperatorLiveTransport for PanicTransport {
    fn post_json(
        &self,
        _endpoint: &str,
        _bearer_token: &[u8],
        _timeout_seconds: u64,
        _body: &[u8],
    ) -> Result<PhalaOperatorLiveRawResponse, PhalaOperatorLiveProviderError> {
        panic!("transport must not be called after local preflight rejection")
    }
}

impl FakeTransport {
    fn accepted() -> Self {
        let body = serde_json::to_vec(&response_with_raw_digest(vec![0; 32]))
            .expect("response serializes");
        Self::new(Ok(PhalaOperatorLiveRawResponse {
            status_code: 200,
            body,
        }))
    }

    fn new(response: Result<PhalaOperatorLiveRawResponse, PhalaOperatorLiveProviderError>) -> Self {
        Self {
            response,
            seen_endpoint: RefCell::new(None),
            seen_body: RefCell::new(Vec::new()),
            seen_credential: RefCell::new(Vec::new()),
        }
    }
}

impl PhalaOperatorLiveTransport for FakeTransport {
    fn post_json(
        &self,
        endpoint: &str,
        bearer_token: &[u8],
        _timeout_seconds: u64,
        body: &[u8],
    ) -> Result<PhalaOperatorLiveRawResponse, PhalaOperatorLiveProviderError> {
        *self.seen_endpoint.borrow_mut() = Some(endpoint.to_owned());
        *self.seen_body.borrow_mut() = body.to_vec();
        *self.seen_credential.borrow_mut() = bearer_token.to_vec();
        self.response.clone()
    }
}

fn anchor() -> Anchor {
    Anchor::HardwareAttested {
        vendor: "phala-dstack".to_owned(),
        device: "operator-live-provider".to_owned(),
    }
}

fn report_data() -> Vec<u8> {
    report_data_binding(AGENT_PUBKEY, NONCE, CASE_HASH)
}

fn compose_hash() -> Vec<u8> {
    b"compose-hash:operator-live-provider".to_vec()
}

fn runtime_measurements() -> BTreeSet<String> {
    BTreeSet::from([
        "rtmr0:aaaa102".to_owned(),
        "rtmr1:bbbb102".to_owned(),
        "rtmr2:cccc102".to_owned(),
    ])
}

fn required_roots() -> BTreeSet<TrustRoot> {
    BTreeSet::from([
        TrustRoot::HardwareVendor(VendorId(format!("phala-managed-verifier:{ENDPOINT}"))),
        TrustRoot::HardwareVendor(VendorId("dstack-runtime-format:v1".to_owned())),
        TrustRoot::HardwareVendor(VendorId(
            "provider-disclosed-hardware-root:intel-tdx".to_owned(),
        )),
    ])
}

fn response_with_raw_digest(raw_response_digest: Vec<u8>) -> PhalaManagedVerifierResponse {
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
        raw_response_digest,
        provider_trust_roots: required_roots(),
    }
}

fn input(output_root: PathBuf) -> PhalaOperatorLiveInvocationInput {
    PhalaOperatorLiveInvocationInput {
        operator_run_id: "operator-live-provider-run-001".to_owned(),
        operator_acknowledged: true,
        provider_endpoint: ENDPOINT.to_owned(),
        credential_source: CREDENTIAL_SOURCE.to_owned(),
        timeout_seconds: 30,
        retry_limit: 0,
        anchor_id: anchor().anchor_id(),
        agent_pubkey: AGENT_PUBKEY.to_vec(),
        case_hash: CASE_HASH.to_vec(),
        nonce: NONCE,
        expected_report_data_binding: report_data(),
        expected_compose_hash: compose_hash(),
        expected_runtime_measurements: runtime_measurements(),
        expected_image_digest: IMAGE_DIGEST.to_owned(),
        request_time: NOW,
        started_at: NOW - 2,
        output_root,
        overwrite: PhalaOperatorLiveOutputOverwriteMode::RefuseExisting,
    }
}

fn config() -> PhalaOperatorLiveProviderConfig {
    PhalaOperatorLiveProviderConfig::new(
        ENDPOINT,
        30,
        BTreeSet::from([CREDENTIAL_SOURCE.to_owned()]),
    )
}

fn temp_output_root(label: &str) -> PathBuf {
    let unique = TEMP_COUNTER.fetch_add(1, Ordering::SeqCst);
    let nanos = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|duration| duration.as_nanos())
        .unwrap_or_default();
    let root = std::env::temp_dir().join(format!(
        "hsai-phala-operator-live-provider-{label}-{nanos}-{unique}"
    ));
    let _ = fs::remove_dir_all(&root);
    fs::create_dir(&root).expect("temp output root created");
    root
}

fn cleanup(path: &Path) {
    let _ = fs::remove_dir_all(path);
}

fn set_test_credential() {
    std::env::set_var("HSAI_TEST_PHALA_OPERATOR_TOKEN_PHASE_102", CREDENTIAL_VALUE);
}

fn clear_test_credential() {
    std::env::remove_var("HSAI_TEST_PHALA_OPERATOR_TOKEN_PHASE_102");
}

#[test]
fn provider_client_invocation_writes_redacted_bundle_with_raw_digest_only() {
    let _env = lock_env();
    let root = temp_output_root("success");
    set_test_credential();
    let transport = FakeTransport::accepted();
    let raw_body = transport.response.clone().expect("raw response").body;
    let client = PhalaOperatorLiveProviderClient::new(config(), transport);
    let invocation = PhalaOperatorLiveInvocation::new(
        client,
        PhalaEnvCredentialProvider::new(BTreeSet::from([CREDENTIAL_SOURCE.to_owned()])),
    );

    let validated = invocation
        .invoke(&input(root.clone()))
        .expect("provider invocation succeeds");
    let read_back =
        read_phala_operator_live_artifact_output_root(&root).expect("bundle reads back");
    let expected_raw_digest = Sha256::digest(&raw_body).to_vec();

    assert_eq!(validated, read_back);
    assert_eq!(validated.claim_boundary, PHALA_OPERATOR_LIVE_CLAIM_BOUNDARY);
    assert_eq!(
        fs::read_to_string(root.join("operator-live/raw-response.sha256")).expect("digest reads"),
        hex_lower(&expected_raw_digest)
    );
    assert!(!root.join("operator-live/raw-response.json").exists());

    let mut concatenated = String::new();
    for entry in fs::read_dir(root.join("operator-live")).expect("operator dir reads") {
        let entry = entry.expect("operator file entry");
        concatenated.push_str(
            &String::from_utf8(fs::read(entry.path()).expect("operator file reads"))
                .unwrap_or_default(),
        );
    }
    assert!(!concatenated.contains(CREDENTIAL_VALUE));
    assert!(!concatenated.contains("HSAI_TEST_PHALA_OPERATOR_TOKEN_PHASE_102"));
    clear_test_credential();
    cleanup(&root);
}

#[test]
fn provider_client_rejects_config_errors_before_transport() {
    let mut empty_endpoint = config();
    empty_endpoint.endpoint.clear();
    assert_eq!(
        empty_endpoint.validate(),
        Err(PhalaOperatorLiveProviderError::EmptyEndpoint)
    );

    let mut zero_timeout = config();
    zero_timeout.timeout_seconds = 0;
    assert_eq!(
        zero_timeout.validate(),
        Err(PhalaOperatorLiveProviderError::TimeoutOutOfBounds {
            actual: 0,
            max: PHALA_OPERATOR_LIVE_MAX_TIMEOUT_SECONDS,
        })
    );

    let mut unbounded_timeout = config();
    unbounded_timeout.timeout_seconds = PHALA_OPERATOR_LIVE_MAX_TIMEOUT_SECONDS + 1;
    assert_eq!(
        unbounded_timeout.validate(),
        Err(PhalaOperatorLiveProviderError::TimeoutOutOfBounds {
            actual: PHALA_OPERATOR_LIVE_MAX_TIMEOUT_SECONDS + 1,
            max: PHALA_OPERATOR_LIVE_MAX_TIMEOUT_SECONDS,
        })
    );

    let mut no_sources = config();
    no_sources.allowed_credential_sources.clear();
    assert_eq!(
        no_sources.validate(),
        Err(PhalaOperatorLiveProviderError::MissingAllowedCredentialSource)
    );
}

#[test]
fn provider_client_rejects_unapproved_credential_before_transport() {
    let request = request();
    let credential = PhalaOperatorLiveCredential::new(
        "env:HSAI_TEST_UNAPPROVED_PROVIDER_TOKEN",
        CREDENTIAL_VALUE.as_bytes(),
    )
    .expect("credential");
    let client = PhalaOperatorLiveProviderClient::new(config(), PanicTransport);

    assert_eq!(
        client.verify_with_credential(&request, &credential),
        Err(PhalaManagedVerifierError::ClientUnavailable)
    );
}

#[test]
fn env_credential_provider_requires_allowed_available_nonempty_source() {
    let _env = lock_env();
    clear_test_credential();
    let provider = PhalaEnvCredentialProvider::new(BTreeSet::from([CREDENTIAL_SOURCE.to_owned()]));
    assert_eq!(
        provider.load(CREDENTIAL_SOURCE),
        Err(PhalaOperatorLiveInvocationError::CredentialUnavailable(
            CREDENTIAL_SOURCE.to_owned()
        ))
    );

    std::env::set_var("HSAI_TEST_PHALA_OPERATOR_TOKEN_PHASE_102", "");
    assert_eq!(
        provider.load(CREDENTIAL_SOURCE),
        Err(PhalaOperatorLiveInvocationError::CredentialUnavailable(
            CREDENTIAL_SOURCE.to_owned()
        ))
    );

    set_test_credential();
    let credential = provider
        .load(CREDENTIAL_SOURCE)
        .expect("credential loads when explicitly allowed and present");
    assert_eq!(credential.source_id(), CREDENTIAL_SOURCE);
    assert_eq!(credential.secret_bytes(), CREDENTIAL_VALUE.as_bytes());

    assert_eq!(
        provider.load("env:UNAPPROVED_TOKEN"),
        Err(PhalaOperatorLiveInvocationError::CredentialUnavailable(
            "env:UNAPPROVED_TOKEN".to_owned()
        ))
    );
    clear_test_credential();
}

#[test]
fn provider_client_maps_fail_closed_http_and_transport_errors() {
    let request = request();
    let credential =
        PhalaOperatorLiveCredential::new(CREDENTIAL_SOURCE, CREDENTIAL_VALUE.as_bytes())
            .expect("credential");

    let auth = PhalaOperatorLiveProviderClient::new(
        config(),
        FakeTransport::new(Ok(PhalaOperatorLiveRawResponse {
            status_code: 401,
            body: br#"{"error":"unauthorized"}"#.to_vec(),
        })),
    );
    assert_eq!(
        auth.verify_with_credential(&request, &credential),
        Err(PhalaManagedVerifierError::AuthenticationFailed)
    );

    let forbidden = PhalaOperatorLiveProviderClient::new(
        config(),
        FakeTransport::new(Ok(PhalaOperatorLiveRawResponse {
            status_code: 403,
            body: br#"{"error":"forbidden"}"#.to_vec(),
        })),
    );
    assert_eq!(
        forbidden.verify_with_credential(&request, &credential),
        Err(PhalaManagedVerifierError::AuthenticationFailed)
    );

    let status = PhalaOperatorLiveProviderClient::new(
        config(),
        FakeTransport::new(Ok(PhalaOperatorLiveRawResponse {
            status_code: 500,
            body: br#"{"error":"provider"}"#.to_vec(),
        })),
    );
    assert_eq!(
        status.verify_with_credential(&request, &credential),
        Err(PhalaManagedVerifierError::UnexpectedHttpStatus(500))
    );

    let malformed = PhalaOperatorLiveProviderClient::new(
        config(),
        FakeTransport::new(Ok(PhalaOperatorLiveRawResponse {
            status_code: 200,
            body: b"not-json".to_vec(),
        })),
    );
    assert_eq!(
        malformed.verify_with_credential(&request, &credential),
        Err(PhalaManagedVerifierError::MalformedResponse)
    );

    let transport = PhalaOperatorLiveProviderClient::new(
        config(),
        FakeTransport::new(Err(PhalaOperatorLiveProviderError::TransportUnavailable)),
    );
    assert_eq!(
        transport.verify_with_credential(&request, &credential),
        Err(PhalaManagedVerifierError::TransportUnavailable)
    );
}

#[test]
fn ureq_transport_rejects_non_utf8_credential_before_network() {
    let transport = hsai_attestation_phala::UreqPhalaOperatorLiveTransport;
    assert_eq!(
        transport.post_json(ENDPOINT, &[0xff, 0xfe], 30, b"{}"),
        Err(PhalaOperatorLiveProviderError::CredentialNotUtf8)
    );
}

#[test]
fn provider_client_rejection_flows_through_phase100_orchestrator() {
    let _env = lock_env();
    let root = temp_output_root("rejected");
    set_test_credential();
    let mut rejected = response_with_raw_digest(vec![0; 32]);
    rejected.provider_verdict = PhalaManagedVerifierVerdict::Rejected;
    let body = serde_json::to_vec(&rejected).expect("rejected response serializes");
    let client = PhalaOperatorLiveProviderClient::new(
        config(),
        FakeTransport::new(Ok(PhalaOperatorLiveRawResponse {
            status_code: 200,
            body,
        })),
    );
    let invocation = PhalaOperatorLiveInvocation::new(
        client,
        PhalaEnvCredentialProvider::new(BTreeSet::from([CREDENTIAL_SOURCE.to_owned()])),
    );

    assert_eq!(
        invocation.invoke(&input(root.clone())),
        Err(PhalaOperatorLiveInvocationError::ManagedVerifier(
            PhalaManagedVerifierError::ProviderRejected
        ))
    );
    clear_test_credential();
    cleanup(&root);
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
        freshness_window: 30,
        managed_verifier_endpoint_id: ENDPOINT.to_owned(),
        request_time: NOW,
    }
}

fn hex_lower(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn lock_env() -> MutexGuard<'static, ()> {
    ENV_LOCK.lock().expect("env lock")
}

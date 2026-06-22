use hsai_attestation::report_data_binding;
use hsai_attestation_phala::{
    read_phala_operator_live_artifact_output_root, InMemoryPhalaManagedVerifierClient,
    InMemoryPhalaOperatorLiveCredentialProvider, PhalaManagedVerifierError,
    PhalaManagedVerifierRequest, PhalaManagedVerifierResponse, PhalaManagedVerifierVerdict,
    PhalaOperatorLiveClient, PhalaOperatorLiveCredential, PhalaOperatorLiveCredentialProvider,
    PhalaOperatorLiveInvocation, PhalaOperatorLiveInvocationError,
    PhalaOperatorLiveInvocationInput, PhalaOperatorLiveOutputOverwriteMode,
    PHALA_OPERATOR_LIVE_CLAIM_BOUNDARY, PHALA_OPERATOR_LIVE_MAX_RETRY_LIMIT,
    PHALA_OPERATOR_LIVE_MAX_TIMEOUT_SECONDS, PHALA_OPERATOR_LIVE_RAW_RESPONSE_DIGEST_PATH,
    PHALA_OPERATOR_LIVE_REQUEST_PATH,
};
use hsai_claim_envelope::{TrustRoot, VendorId};
use hsai_distinct_agent::Anchor;
use std::cell::RefCell;
use std::collections::BTreeSet;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

static TEMP_COUNTER: AtomicU64 = AtomicU64::new(0);

const NOW: u64 = 3_000;
const NONCE: u64 = 505;
const ENDPOINT_ID: &str = "phala-trust-center:operator-invocation";
const CREDENTIAL_SOURCE: &str = "env:PHALA_OPERATOR_TOKEN";
const CREDENTIAL_SECRET: &[u8] = b"operator-secret-not-for-artifacts";
const IMAGE_DIGEST: &str = "sha256:feedfacecafebeef";
const AGENT_PUBKEY: &[u8] = b"operator-live-invocation-agent-key";
const CASE_HASH: &[u8] = b"operator-live-invocation-case-hash";

#[derive(Debug)]
struct RetryClient {
    failures_left: RefCell<u64>,
    response: PhalaManagedVerifierResponse,
}

impl RetryClient {
    fn new(failures_left: u64, response: PhalaManagedVerifierResponse) -> Self {
        Self {
            failures_left: RefCell::new(failures_left),
            response,
        }
    }
}

impl PhalaOperatorLiveClient for RetryClient {
    fn verify_with_credential(
        &self,
        _request: &PhalaManagedVerifierRequest,
        credential: &PhalaOperatorLiveCredential,
    ) -> Result<PhalaManagedVerifierResponse, PhalaManagedVerifierError> {
        assert_eq!(credential.source_id(), CREDENTIAL_SOURCE);
        assert_eq!(credential.secret_bytes(), CREDENTIAL_SECRET);
        let mut failures_left = self.failures_left.borrow_mut();
        if *failures_left > 0 {
            *failures_left -= 1;
            return Err(PhalaManagedVerifierError::ClientUnavailable);
        }
        Ok(self.response.clone())
    }
}

#[derive(Debug)]
struct MismatchedCredentialProvider;

impl PhalaOperatorLiveCredentialProvider for MismatchedCredentialProvider {
    fn load(
        &self,
        _source_id: &str,
    ) -> Result<PhalaOperatorLiveCredential, PhalaOperatorLiveInvocationError> {
        PhalaOperatorLiveCredential::new("env:OTHER_TOKEN", CREDENTIAL_SECRET)
    }
}

fn anchor() -> Anchor {
    Anchor::HardwareAttested {
        vendor: "phala-dstack".to_owned(),
        device: "operator-live-invocation".to_owned(),
    }
}

fn report_data() -> Vec<u8> {
    report_data_binding(AGENT_PUBKEY, NONCE, CASE_HASH)
}

fn compose_hash() -> Vec<u8> {
    b"compose-hash:operator-live-invocation".to_vec()
}

fn runtime_measurements() -> BTreeSet<String> {
    BTreeSet::from([
        "rtmr0:11111111".to_owned(),
        "rtmr1:22222222".to_owned(),
        "rtmr2:33333333".to_owned(),
    ])
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
        raw_response_digest: vec![9; 32],
        provider_trust_roots: required_roots(),
    }
}

fn input(output_root: PathBuf) -> PhalaOperatorLiveInvocationInput {
    PhalaOperatorLiveInvocationInput {
        operator_run_id: "operator-live-run-001".to_owned(),
        operator_acknowledged: true,
        provider_endpoint: ENDPOINT_ID.to_owned(),
        credential_source: CREDENTIAL_SOURCE.to_owned(),
        timeout_seconds: 30,
        retry_limit: 1,
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

fn credential_provider() -> InMemoryPhalaOperatorLiveCredentialProvider {
    InMemoryPhalaOperatorLiveCredentialProvider::new()
        .with_credential(CREDENTIAL_SOURCE, CREDENTIAL_SECRET)
}

fn invocation(
    output_root: &Path,
) -> PhalaOperatorLiveInvocation<
    InMemoryPhalaManagedVerifierClient,
    InMemoryPhalaOperatorLiveCredentialProvider,
> {
    let request_input = input(output_root.to_path_buf());
    let client = InMemoryPhalaManagedVerifierClient::new().with_response(
        request_input.anchor_id,
        request_input.nonce,
        response(),
    );
    PhalaOperatorLiveInvocation::new(client, credential_provider())
}

fn temp_output_root(label: &str) -> PathBuf {
    let unique = TEMP_COUNTER.fetch_add(1, Ordering::SeqCst);
    let nanos = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|duration| duration.as_nanos())
        .unwrap_or_default();
    let root = std::env::temp_dir().join(format!(
        "hsai-phala-operator-live-invocation-{label}-{nanos}-{unique}"
    ));
    let _ = fs::remove_dir_all(&root);
    fs::create_dir(&root).expect("temp output root created");
    root
}

fn cleanup(path: &Path) {
    let _ = fs::remove_dir_all(path);
}

#[test]
fn operator_live_invocation_writes_valid_redacted_bundle() {
    let root = temp_output_root("success");
    let invocation = invocation(&root);
    let validated = invocation
        .invoke(&input(root.clone()))
        .expect("operator invocation succeeds");
    let read_back =
        read_phala_operator_live_artifact_output_root(&root).expect("bundle reads back");

    assert_eq!(validated, read_back);
    assert_eq!(validated.claim_boundary, PHALA_OPERATOR_LIVE_CLAIM_BOUNDARY);
    assert_eq!(validated.trust_roots, required_roots());
    assert!(root.join(PHALA_OPERATOR_LIVE_REQUEST_PATH).is_file());
    assert!(root
        .join(PHALA_OPERATOR_LIVE_RAW_RESPONSE_DIGEST_PATH)
        .is_file());
    assert!(!root.join("operator-live/raw-response.json").exists());

    let mut concatenated = String::new();
    for entry in fs::read_dir(root.join("operator-live")).expect("operator dir reads") {
        let entry = entry.expect("operator file entry");
        concatenated.push_str(
            &String::from_utf8(fs::read(entry.path()).expect("operator file reads"))
                .unwrap_or_default(),
        );
    }
    assert!(!concatenated.contains("operator-secret-not-for-artifacts"));
    assert!(!concatenated.contains("PHALA_OPERATOR_TOKEN"));
    cleanup(&root);
}

#[test]
fn operator_live_invocation_fails_closed_before_client_on_missing_controls() {
    let root = temp_output_root("controls");
    let invocation = invocation(&root);

    let mut missing_ack = input(root.clone());
    missing_ack.operator_acknowledged = false;
    assert_eq!(
        invocation.invoke(&missing_ack),
        Err(PhalaOperatorLiveInvocationError::MissingOperatorAcknowledgement)
    );

    let mut missing_credential = input(root.clone());
    missing_credential.credential_source.clear();
    assert_eq!(
        invocation.invoke(&missing_credential),
        Err(PhalaOperatorLiveInvocationError::MissingCredentialSource)
    );

    let mut empty_endpoint = input(root.clone());
    empty_endpoint.provider_endpoint.clear();
    assert_eq!(
        invocation.invoke(&empty_endpoint),
        Err(PhalaOperatorLiveInvocationError::EmptyEndpoint)
    );

    let mut unbounded_timeout = input(root.clone());
    unbounded_timeout.timeout_seconds = PHALA_OPERATOR_LIVE_MAX_TIMEOUT_SECONDS + 1;
    assert_eq!(
        invocation.invoke(&unbounded_timeout),
        Err(PhalaOperatorLiveInvocationError::TimeoutOutOfBounds {
            actual: PHALA_OPERATOR_LIVE_MAX_TIMEOUT_SECONDS + 1,
            max: PHALA_OPERATOR_LIVE_MAX_TIMEOUT_SECONDS,
        })
    );

    let mut unbounded_retry = input(root.clone());
    unbounded_retry.retry_limit = PHALA_OPERATOR_LIVE_MAX_RETRY_LIMIT + 1;
    assert_eq!(
        invocation.invoke(&unbounded_retry),
        Err(PhalaOperatorLiveInvocationError::RetryLimitOutOfBounds {
            actual: PHALA_OPERATOR_LIVE_MAX_RETRY_LIMIT + 1,
            max: PHALA_OPERATOR_LIVE_MAX_RETRY_LIMIT,
        })
    );
    cleanup(&root);
}

#[test]
fn operator_live_invocation_requires_available_matching_credential() {
    let root = temp_output_root("credential");
    let request_input = input(root.clone());
    let client = InMemoryPhalaManagedVerifierClient::new().with_response(
        request_input.anchor_id.clone(),
        request_input.nonce,
        response(),
    );
    let missing = PhalaOperatorLiveInvocation::new(
        client.clone(),
        InMemoryPhalaOperatorLiveCredentialProvider::new(),
    );
    assert_eq!(
        missing.invoke(&request_input),
        Err(PhalaOperatorLiveInvocationError::CredentialUnavailable(
            CREDENTIAL_SOURCE.to_owned()
        ))
    );

    let mismatched = PhalaOperatorLiveInvocation::new(client, MismatchedCredentialProvider);
    assert_eq!(
        mismatched.invoke(&request_input),
        Err(PhalaOperatorLiveInvocationError::CredentialSourceMismatch {
            expected: CREDENTIAL_SOURCE.to_owned(),
            actual: "env:OTHER_TOKEN".to_owned(),
        })
    );
    cleanup(&root);
}

#[test]
fn operator_live_invocation_maps_retry_exhaustion_and_provider_rejection() {
    let root = temp_output_root("errors");
    let retrying =
        PhalaOperatorLiveInvocation::new(RetryClient::new(2, response()), credential_provider());
    let mut retry_input = input(root.clone());
    retry_input.retry_limit = 1;
    assert_eq!(
        retrying.invoke(&retry_input),
        Err(PhalaOperatorLiveInvocationError::RetryExhausted {
            attempts: 2,
            last_error: PhalaManagedVerifierError::ClientUnavailable,
        })
    );

    let mut rejected_response = response();
    rejected_response.provider_verdict = PhalaManagedVerifierVerdict::Rejected;
    let rejected_client = InMemoryPhalaManagedVerifierClient::new().with_response(
        retry_input.anchor_id.clone(),
        retry_input.nonce,
        rejected_response,
    );
    let rejected = PhalaOperatorLiveInvocation::new(rejected_client, credential_provider());
    assert_eq!(
        rejected.invoke(&retry_input),
        Err(PhalaOperatorLiveInvocationError::ManagedVerifier(
            PhalaManagedVerifierError::ProviderRejected
        ))
    );
    cleanup(&root);
}

#[test]
fn operator_live_invocation_records_replay_before_second_write() {
    let root = temp_output_root("replay");
    let invocation = invocation(&root);
    invocation
        .invoke(&input(root.clone()))
        .expect("first invocation succeeds");
    assert_eq!(
        invocation.invoke(&input(root.clone())),
        Err(PhalaOperatorLiveInvocationError::ManagedVerifier(
            PhalaManagedVerifierError::ReplayedNonce
        ))
    );
    cleanup(&root);
}

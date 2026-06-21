use hsai_attestation::report_data_binding;
use hsai_attestation_phala::{
    parse_phala_operator_live_artifact_files, phala_operator_live_json_digest,
    validate_phala_operator_live_artifact_files, PhalaManagedVerifierError,
    PhalaManagedVerifierRequest, PhalaManagedVerifierResponse, PhalaManagedVerifierVerdict,
    PhalaOperatorLiveArtifactBundle, PhalaOperatorLiveArtifactError, PhalaOperatorLiveAudit,
    PhalaOperatorLiveRedactionReport, PhalaOperatorLiveRetainedField, PhalaOperatorLiveTrustRoots,
    PHALA_OPERATOR_LIVE_ARTIFACT_SCHEMA_VERSION, PHALA_OPERATOR_LIVE_AUDIT_PATH,
    PHALA_OPERATOR_LIVE_CLAIM_BOUNDARY, PHALA_OPERATOR_LIVE_NORMALIZED_RESPONSE_PATH,
    PHALA_OPERATOR_LIVE_RAW_RESPONSE_DIGEST_PATH, PHALA_OPERATOR_LIVE_REDACTION_REPORT_PATH,
    PHALA_OPERATOR_LIVE_REQUEST_PATH, PHALA_OPERATOR_LIVE_TRUST_ROOTS_PATH,
};
use hsai_claim_envelope::{TrustRoot, VendorId};
use hsai_distinct_agent::Anchor;
use std::collections::{BTreeMap, BTreeSet};

const NOW: u64 = 2_000;
const NONCE: u64 = 777;
const ENDPOINT_ID: &str = "phala-trust-center:operator-live";
const IMAGE_DIGEST: &str = "sha256:0123456789abcdef";
const RAW_RESPONSE_SHA256: &str =
    "0707070707070707070707070707070707070707070707070707070707070707";
const AGENT_PUBKEY: &[u8] = b"operator-live-agent-key";
const CASE_HASH: &[u8] = b"operator-live-case-hash";

fn anchor() -> Anchor {
    Anchor::HardwareAttested {
        vendor: "phala-dstack".to_owned(),
        device: "operator-live-artifact".to_owned(),
    }
}

fn report_data() -> Vec<u8> {
    report_data_binding(AGENT_PUBKEY, NONCE, CASE_HASH)
}

fn compose_hash() -> Vec<u8> {
    b"compose-hash:operator-live".to_vec()
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

fn trust_roots(response: &PhalaManagedVerifierResponse) -> PhalaOperatorLiveTrustRoots {
    PhalaOperatorLiveTrustRoots {
        schema_version: PHALA_OPERATOR_LIVE_ARTIFACT_SCHEMA_VERSION.to_owned(),
        provider: "phala-dstack".to_owned(),
        verification_mode: "live-managed-verifier".to_owned(),
        roots: response.provider_trust_roots.clone(),
    }
}

fn redaction_report() -> PhalaOperatorLiveRedactionReport {
    PhalaOperatorLiveRedactionReport {
        schema_version: PHALA_OPERATOR_LIVE_ARTIFACT_SCHEMA_VERSION.to_owned(),
        digest_algorithm: "sha256".to_owned(),
        removed_fields: BTreeSet::from(["authorization_header".to_owned()]),
        hashed_fields: BTreeSet::from(["raw_response_body".to_owned()]),
        retained_fields: BTreeMap::from([(
            "managed_verifier_endpoint_id".to_owned(),
            PhalaOperatorLiveRetainedField {
                value: ENDPOINT_ID.to_owned(),
                rationale: "public provider endpoint label".to_owned(),
            },
        )]),
        dropped_secret_shaped_fields: BTreeSet::from(["bearer_token".to_owned()]),
    }
}

fn non_claims() -> BTreeSet<String> {
    BTreeSet::from([
        "not proof".to_owned(),
        "not local DCAP verification".to_owned(),
        "not benchmark evidence".to_owned(),
        "not global software-agent uniqueness".to_owned(),
        "not semantic correctness".to_owned(),
    ])
}

fn bundle() -> PhalaOperatorLiveArtifactBundle {
    let request = request();
    let normalized_response = response();
    let trust_roots = trust_roots(&normalized_response);
    let redaction_report = redaction_report();
    let audit = PhalaOperatorLiveAudit {
        schema_version: PHALA_OPERATOR_LIVE_ARTIFACT_SCHEMA_VERSION.to_owned(),
        operator_run_id: "operator-run-001".to_owned(),
        provider: "phala-dstack".to_owned(),
        verification_mode: "live-managed-verifier".to_owned(),
        request_digest: phala_operator_live_json_digest(&request).expect("request digests"),
        normalized_response_digest: phala_operator_live_json_digest(&normalized_response)
            .expect("response digests"),
        trust_roots_digest: phala_operator_live_json_digest(&trust_roots)
            .expect("trust roots digest"),
        redaction_report_digest: phala_operator_live_json_digest(&redaction_report)
            .expect("redaction digest"),
        raw_response_digest: RAW_RESPONSE_SHA256.to_owned(),
        started_at: NOW - 20,
        finished_at: NOW - 5,
        timeout_seconds: 30,
        retry_limit: 1,
        provider_verdict: PhalaManagedVerifierVerdict::Accepted,
        claim_boundary: PHALA_OPERATOR_LIVE_CLAIM_BOUNDARY.to_owned(),
        non_claims: non_claims(),
    };

    PhalaOperatorLiveArtifactBundle {
        request,
        normalized_response,
        trust_roots,
        redaction_report,
        audit,
        raw_response_sha256: RAW_RESPONSE_SHA256.to_owned(),
    }
}

fn files_for(bundle: &PhalaOperatorLiveArtifactBundle) -> BTreeMap<String, Vec<u8>> {
    BTreeMap::from([
        (
            PHALA_OPERATOR_LIVE_REQUEST_PATH.to_owned(),
            serde_json::to_vec(&bundle.request).expect("request serializes"),
        ),
        (
            PHALA_OPERATOR_LIVE_NORMALIZED_RESPONSE_PATH.to_owned(),
            serde_json::to_vec(&bundle.normalized_response).expect("response serializes"),
        ),
        (
            PHALA_OPERATOR_LIVE_TRUST_ROOTS_PATH.to_owned(),
            serde_json::to_vec(&bundle.trust_roots).expect("trust roots serialize"),
        ),
        (
            PHALA_OPERATOR_LIVE_REDACTION_REPORT_PATH.to_owned(),
            serde_json::to_vec(&bundle.redaction_report).expect("redaction serializes"),
        ),
        (
            PHALA_OPERATOR_LIVE_AUDIT_PATH.to_owned(),
            serde_json::to_vec(&bundle.audit).expect("audit serializes"),
        ),
        (
            PHALA_OPERATOR_LIVE_RAW_RESPONSE_DIGEST_PATH.to_owned(),
            bundle.raw_response_sha256.as_bytes().to_vec(),
        ),
    ])
}

fn error_for(bundle: PhalaOperatorLiveArtifactBundle) -> PhalaOperatorLiveArtifactError {
    validate_phala_operator_live_artifact_files(&files_for(&bundle)).expect_err("bundle rejects")
}

#[test]
fn valid_operator_live_bundle_round_trips_without_live_io() {
    let files = files_for(&bundle());
    let parsed = parse_phala_operator_live_artifact_files(&files).expect("files parse");
    let validated = validate_phala_operator_live_artifact_files(&files).expect("bundle validates");

    assert_eq!(parsed.request.anchor_id, anchor().anchor_id());
    assert_eq!(validated.claim_boundary, PHALA_OPERATOR_LIVE_CLAIM_BOUNDARY);
    assert_eq!(validated.provider, "phala-dstack");
    assert_eq!(validated.trust_roots, required_roots());
}

#[test]
fn missing_extra_and_unsafe_paths_fail_closed() {
    let mut missing = files_for(&bundle());
    missing.remove(PHALA_OPERATOR_LIVE_AUDIT_PATH);
    assert_eq!(
        validate_phala_operator_live_artifact_files(&missing),
        Err(PhalaOperatorLiveArtifactError::MissingFile(
            PHALA_OPERATOR_LIVE_AUDIT_PATH.to_owned()
        ))
    );

    let mut extra = files_for(&bundle());
    extra.insert("operator-live/extra.json".to_owned(), b"{}".to_vec());
    assert_eq!(
        validate_phala_operator_live_artifact_files(&extra),
        Err(PhalaOperatorLiveArtifactError::UnexpectedFile(
            "operator-live/extra.json".to_owned()
        ))
    );

    let mut unsafe_path = files_for(&bundle());
    unsafe_path.insert("operator-live/../secret.json".to_owned(), b"{}".to_vec());
    assert_eq!(
        validate_phala_operator_live_artifact_files(&unsafe_path),
        Err(PhalaOperatorLiveArtifactError::UnsafePath(
            "operator-live/../secret.json".to_owned()
        ))
    );
}

#[test]
fn digest_and_schema_drift_fail_closed() {
    let mut bad_digest = bundle();
    bad_digest.audit.request_digest =
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa".to_owned();
    assert!(matches!(
        error_for(bad_digest),
        PhalaOperatorLiveArtifactError::DigestMismatch { .. }
    ));

    let mut bad_schema = bundle();
    bad_schema.audit.schema_version = "wrong-schema".to_owned();
    assert_eq!(
        error_for(bad_schema),
        PhalaOperatorLiveArtifactError::SchemaVersionMismatch {
            field: "audit.schema_version".to_owned(),
            actual: "wrong-schema".to_owned(),
        }
    );
}

#[test]
fn stale_response_and_missing_trust_roots_fail_closed() {
    let mut stale = bundle();
    stale.normalized_response.issued_at = NOW - 300;
    stale.audit.normalized_response_digest =
        phala_operator_live_json_digest(&stale.normalized_response).expect("response digests");
    assert_eq!(
        error_for(stale),
        PhalaOperatorLiveArtifactError::ManagedVerifier(PhalaManagedVerifierError::StaleResponse)
    );

    let mut missing_roots = bundle();
    missing_roots.normalized_response.provider_trust_roots = BTreeSet::new();
    missing_roots.trust_roots.roots = BTreeSet::new();
    missing_roots.audit.normalized_response_digest =
        phala_operator_live_json_digest(&missing_roots.normalized_response)
            .expect("response digests");
    missing_roots.audit.trust_roots_digest =
        phala_operator_live_json_digest(&missing_roots.trust_roots).expect("trust roots digest");
    assert_eq!(
        error_for(missing_roots),
        PhalaOperatorLiveArtifactError::ManagedVerifier(
            PhalaManagedVerifierError::MissingTrustRoot
        )
    );
}

#[test]
fn redaction_report_must_explain_retained_non_secret_fields() {
    let mut missing_rationale = bundle();
    missing_rationale
        .redaction_report
        .retained_fields
        .get_mut("managed_verifier_endpoint_id")
        .expect("field exists")
        .rationale
        .clear();
    missing_rationale.audit.redaction_report_digest =
        phala_operator_live_json_digest(&missing_rationale.redaction_report)
            .expect("redaction digests");
    assert_eq!(
        error_for(missing_rationale),
        PhalaOperatorLiveArtifactError::RedactionRationaleMissing(
            "managed_verifier_endpoint_id".to_owned()
        )
    );

    let mut token_value = bundle();
    token_value.redaction_report.retained_fields.insert(
        "operator_header".to_owned(),
        PhalaOperatorLiveRetainedField {
            value: "Bearer secret-token".to_owned(),
            rationale: "should not be retained".to_owned(),
        },
    );
    token_value.audit.redaction_report_digest =
        phala_operator_live_json_digest(&token_value.redaction_report).expect("redaction digests");
    assert_eq!(
        error_for(token_value),
        PhalaOperatorLiveArtifactError::RedactionSecretRetained("operator_header".to_owned())
    );
}

#[test]
fn claim_boundary_and_rejected_provider_verdict_fail_closed() {
    let mut elevated = bundle();
    elevated.audit.claim_boundary = "Proven".to_owned();
    assert_eq!(
        error_for(elevated),
        PhalaOperatorLiveArtifactError::ClaimBoundaryViolation
    );

    let mut rejected = bundle();
    rejected.normalized_response.provider_verdict = PhalaManagedVerifierVerdict::Rejected;
    rejected.normalized_response.provider_trust_roots = BTreeSet::new();
    rejected.trust_roots.roots = BTreeSet::new();
    rejected.audit.provider_verdict = PhalaManagedVerifierVerdict::Rejected;
    rejected.audit.normalized_response_digest =
        phala_operator_live_json_digest(&rejected.normalized_response).expect("response digests");
    rejected.audit.trust_roots_digest =
        phala_operator_live_json_digest(&rejected.trust_roots).expect("trust roots digest");
    assert_eq!(
        error_for(rejected),
        PhalaOperatorLiveArtifactError::ManagedVerifier(
            PhalaManagedVerifierError::ProviderRejected
        )
    );
}

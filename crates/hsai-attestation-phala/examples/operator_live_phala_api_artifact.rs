use hsai_attestation_phala::{
    phala_operator_live_json_digest, read_phala_operator_live_artifact_output_root,
    write_phala_operator_live_artifact_output_root, PhalaManagedVerifierRequest,
    PhalaManagedVerifierResponse, PhalaManagedVerifierVerdict, PhalaOperatorLiveArtifactBundle,
    PhalaOperatorLiveAudit, PhalaOperatorLiveOutputOverwriteMode, PhalaOperatorLiveRedactionReport,
    PhalaOperatorLiveRetainedField, PhalaOperatorLiveTrustRoots,
    PHALA_OPERATOR_LIVE_ARTIFACT_SCHEMA_VERSION, PHALA_OPERATOR_LIVE_CLAIM_BOUNDARY,
};
use hsai_claim_envelope::{TrustRoot, VendorId};
use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::env;
use std::error::Error;
use std::fs;
use std::io::{Error as IoError, ErrorKind};
use std::path::PathBuf;

const ACK_ENV: &str = "HSAI_PHALA_OPERATOR_ACK";
const ACK_VALUE: &str = "I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN";
const INPUT_JSON_ENV: &str = "HSAI_PHALA_API_ARTIFACT_INPUT_JSON";
const PROVIDER: &str = "phala-dstack";
const MODE: &str = "live-managed-verifier";

#[derive(Deserialize)]
struct ArtifactRunInput {
    operator_run_id: String,
    artifact_bundle_path: PathBuf,
    phala_verify_response_path: PathBuf,
    phala_verify_endpoint: String,
    output_root: PathBuf,
    request_time: u64,
    started_at: u64,
    finished_at: u64,
    timeout_seconds: u64,
    retry_limit: u64,
    overwrite: Option<PhalaOperatorLiveOutputOverwriteMode>,
}

#[derive(Deserialize)]
struct CapturedArtifactBundle {
    anchor_id: String,
    agent_public_key_spki_hex: String,
    case_hash_hex: String,
    nonce_hex: String,
    compose_hash: String,
    report_data_hex: String,
    docker_image_digests: Vec<String>,
}

#[derive(Deserialize)]
struct PhalaVerifyResponse {
    success: bool,
    checksum: String,
    quote: PhalaQuote,
}

#[derive(Deserialize)]
struct PhalaQuote {
    verified: bool,
    header: PhalaQuoteHeader,
    body: PhalaQuoteBody,
}

#[derive(Deserialize)]
struct PhalaQuoteHeader {
    tee_type: String,
}

#[derive(Deserialize)]
struct PhalaQuoteBody {
    reportdata: String,
    rtmr0: String,
    rtmr1: String,
    rtmr2: String,
    rtmr3: String,
}

fn invalid_input(message: impl Into<String>) -> IoError {
    IoError::new(ErrorKind::InvalidInput, message.into())
}

fn decode_hex(label: &str, value: &str) -> Result<Vec<u8>, IoError> {
    let value = value.strip_prefix("0x").unwrap_or(value);
    if value.len() % 2 != 0 {
        return Err(invalid_input(format!("{label} hex length must be even")));
    }
    let mut out = Vec::with_capacity(value.len() / 2);
    for chunk in value.as_bytes().chunks(2) {
        let pair = std::str::from_utf8(chunk)
            .map_err(|_| invalid_input(format!("{label} hex is not utf8")))?;
        let byte = u8::from_str_radix(pair, 16)
            .map_err(|_| invalid_input(format!("{label} is not lowercase/uppercase hex")))?;
        out.push(byte);
    }
    Ok(out)
}

fn hex_lower(bytes: &[u8]) -> String {
    let mut out = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        out.push_str(&format!("{byte:02x}"));
    }
    out
}

fn parse_nonce(value: &str) -> Result<u64, IoError> {
    let bytes = decode_hex("nonce_hex", value)?;
    if bytes.len() > 8 {
        return Err(invalid_input("nonce_hex must fit in u64"));
    }
    let mut nonce = 0_u64;
    for byte in bytes {
        nonce = (nonce << 8) | u64::from(byte);
    }
    Ok(nonce)
}

fn normalized_rtmr(value: &str) -> String {
    value
        .strip_prefix("0x")
        .unwrap_or(value)
        .to_ascii_lowercase()
}

fn runtime_measurements(body: &PhalaQuoteBody) -> BTreeSet<String> {
    BTreeSet::from([
        format!("rtmr0:{}", normalized_rtmr(&body.rtmr0)),
        format!("rtmr1:{}", normalized_rtmr(&body.rtmr1)),
        format!("rtmr2:{}", normalized_rtmr(&body.rtmr2)),
        format!("rtmr3:{}", normalized_rtmr(&body.rtmr3)),
    ])
}

fn non_claims() -> BTreeSet<String> {
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

fn read_input() -> Result<ArtifactRunInput, Box<dyn Error>> {
    let ack = env::var(ACK_ENV).map_err(|_| invalid_input(format!("{ACK_ENV} is required")))?;
    if ack != ACK_VALUE {
        return Err(invalid_input(format!("{ACK_ENV} must equal {ACK_VALUE}")).into());
    }
    let input_path = env::var(INPUT_JSON_ENV)
        .map_err(|_| invalid_input(format!("{INPUT_JSON_ENV} is required")))?;
    let input_bytes = fs::read(input_path)?;
    Ok(serde_json::from_slice(&input_bytes)?)
}

fn build_bundle(
    input: &ArtifactRunInput,
) -> Result<PhalaOperatorLiveArtifactBundle, Box<dyn Error>> {
    let captured: CapturedArtifactBundle =
        serde_json::from_slice(&fs::read(&input.artifact_bundle_path)?)?;
    let raw_response = fs::read(&input.phala_verify_response_path)?;
    let raw_response_digest = Sha256::digest(&raw_response).to_vec();
    let response: PhalaVerifyResponse = serde_json::from_slice(&raw_response)?;

    if !response.success || !response.quote.verified {
        return Err(invalid_input("Phala verification response was not accepted").into());
    }
    if response.quote.header.tee_type != "TEE_TDX" {
        return Err(invalid_input("Phala verification response is not TEE_TDX").into());
    }

    let report_data = decode_hex("quote.body.reportdata", &response.quote.body.reportdata)?;
    let expected_report_prefix =
        decode_hex("artifact_bundle.report_data_hex", &captured.report_data_hex)?;
    if !report_data.starts_with(&expected_report_prefix) {
        return Err(
            invalid_input("quote reportdata does not start with captured report_data_hex").into(),
        );
    }

    let compose_hash = decode_hex("artifact_bundle.compose_hash", &captured.compose_hash)?;
    let runtime_measurements = runtime_measurements(&response.quote.body);
    let image_digest = captured
        .docker_image_digests
        .first()
        .cloned()
        .unwrap_or_else(|| "no-docker-image-digest-declared".to_owned());

    let request = PhalaManagedVerifierRequest {
        anchor_id: captured.anchor_id.clone(),
        agent_pubkey: decode_hex(
            "artifact_bundle.agent_public_key_spki_hex",
            &captured.agent_public_key_spki_hex,
        )?,
        case_hash: decode_hex("artifact_bundle.case_hash_hex", &captured.case_hash_hex)?,
        nonce: parse_nonce(&captured.nonce_hex)?,
        expected_report_data_binding: report_data.clone(),
        expected_compose_hash: compose_hash.clone(),
        expected_runtime_measurements: runtime_measurements.clone(),
        expected_image_digest: image_digest.clone(),
        freshness_window: input.timeout_seconds,
        managed_verifier_endpoint_id: input.phala_verify_endpoint.clone(),
        request_time: input.request_time,
    };

    let provider_trust_roots = BTreeSet::from([
        TrustRoot::HardwareVendor(VendorId(format!(
            "phala-managed-verifier:{}",
            input.phala_verify_endpoint
        ))),
        TrustRoot::HardwareVendor(VendorId(
            "dstack-runtime-format:phala-cloud-attestations-verify-api".to_owned(),
        )),
        TrustRoot::HardwareVendor(VendorId(
            "provider-disclosed-hardware-root:intel-tdx".to_owned(),
        )),
        TrustRoot::HardwareVendor(VendorId(format!(
            "phala-attestation-checksum:{}",
            response.checksum
        ))),
    ]);

    let normalized_response = PhalaManagedVerifierResponse {
        provider: PROVIDER.to_owned(),
        verification_mode: MODE.to_owned(),
        provider_verdict: PhalaManagedVerifierVerdict::Accepted,
        anchor_id: request.anchor_id.clone(),
        nonce: request.nonce,
        report_data,
        compose_hash,
        runtime_measurements,
        image_digest,
        issued_at: input.request_time,
        expires_at: input.request_time + input.timeout_seconds,
        raw_response_digest: raw_response_digest.clone(),
        provider_trust_roots,
    };

    let trust_roots = PhalaOperatorLiveTrustRoots {
        schema_version: PHALA_OPERATOR_LIVE_ARTIFACT_SCHEMA_VERSION.to_owned(),
        provider: PROVIDER.to_owned(),
        verification_mode: MODE.to_owned(),
        roots: normalized_response.provider_trust_roots.clone(),
    };
    let redaction_report = PhalaOperatorLiveRedactionReport {
        schema_version: PHALA_OPERATOR_LIVE_ARTIFACT_SCHEMA_VERSION.to_owned(),
        digest_algorithm: "sha256".to_owned(),
        removed_fields: BTreeSet::new(),
        hashed_fields: BTreeSet::from(["raw_response_body".to_owned()]),
        retained_fields: BTreeMap::from([
            (
                "managed_verifier_endpoint_id".to_owned(),
                PhalaOperatorLiveRetainedField {
                    value: input.phala_verify_endpoint.clone(),
                    rationale: "public Phala Cloud verification endpoint".to_owned(),
                },
            ),
            (
                "phala_attestation_checksum".to_owned(),
                PhalaOperatorLiveRetainedField {
                    value: response.checksum,
                    rationale: "public Phala quote verification checksum".to_owned(),
                },
            ),
        ]),
        dropped_secret_shaped_fields: BTreeSet::new(),
    };
    let raw_response_sha256 = hex_lower(&raw_response_digest);
    let audit = PhalaOperatorLiveAudit {
        schema_version: PHALA_OPERATOR_LIVE_ARTIFACT_SCHEMA_VERSION.to_owned(),
        operator_run_id: input.operator_run_id.clone(),
        provider: PROVIDER.to_owned(),
        verification_mode: MODE.to_owned(),
        request_digest: phala_operator_live_json_digest(&request)?,
        normalized_response_digest: phala_operator_live_json_digest(&normalized_response)?,
        trust_roots_digest: phala_operator_live_json_digest(&trust_roots)?,
        redaction_report_digest: phala_operator_live_json_digest(&redaction_report)?,
        raw_response_digest: raw_response_sha256.clone(),
        started_at: input.started_at,
        finished_at: input.finished_at,
        timeout_seconds: input.timeout_seconds,
        retry_limit: input.retry_limit,
        provider_verdict: PhalaManagedVerifierVerdict::Accepted,
        claim_boundary: PHALA_OPERATOR_LIVE_CLAIM_BOUNDARY.to_owned(),
        non_claims: non_claims(),
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

fn run() -> Result<(), Box<dyn Error>> {
    let input = read_input()?;
    let bundle = build_bundle(&input)?;
    let overwrite = input
        .overwrite
        .unwrap_or(PhalaOperatorLiveOutputOverwriteMode::RefuseExisting);
    let validated =
        write_phala_operator_live_artifact_output_root(&input.output_root, &bundle, overwrite)?;
    let read_back = read_phala_operator_live_artifact_output_root(&input.output_root)?;
    if read_back != validated {
        return Err(invalid_input("materialized bundle did not validate after write").into());
    }

    println!("operator_run_id={}", validated.operator_run_id);
    println!("anchor_id={}", validated.anchor_id);
    println!("claim_boundary={}", validated.claim_boundary);
    println!("request_digest={}", validated.request_digest);
    println!(
        "normalized_response_digest={}",
        validated.normalized_response_digest
    );
    println!("operator_live_output_root={}", input.output_root.display());
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    run()
}

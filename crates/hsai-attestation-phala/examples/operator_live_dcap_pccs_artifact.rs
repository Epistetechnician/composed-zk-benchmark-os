use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::env;
use std::error::Error;
use std::fs;
use std::io::{Error as IoError, ErrorKind};
use std::path::{Path, PathBuf};

const ACK_ENV: &str = "HSAI_PHALA_OPERATOR_ACK";
const ACK_VALUE: &str = "I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN";
const INPUT_JSON_ENV: &str = "HSAI_PHALA_DCAP_PCCS_INPUT_JSON";

#[derive(Deserialize)]
struct DcapPccsRunInput {
    operator_run_id: String,
    checksum: String,
    phala_verify_endpoint: String,
    phala_collateral_endpoint: String,
    phala_verify_response_path: PathBuf,
    phala_collateral_response_path: PathBuf,
    output_root: PathBuf,
    started_at: u64,
    finished_at: u64,
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
}

#[derive(Deserialize)]
struct PhalaQuoteHeader {
    tee_type: String,
}

#[derive(Deserialize)]
struct PhalaCollateralResponse {
    pck_crl: String,
    pck_crl_issuer_chain: String,
    qe_identity: String,
    qe_identity_issuer_chain: String,
    qe_identity_signature: String,
    root_ca_crl: String,
    tcb_info: String,
    tcb_info_issuer_chain: String,
    tcb_info_signature: String,
}

#[derive(Serialize)]
struct DcapPccsSummary {
    schema_version: String,
    operator_run_id: String,
    checksum: String,
    provider: String,
    verification_mode: String,
    tee_type: String,
    phala_verify_endpoint: String,
    phala_collateral_endpoint: String,
    verify_response_sha256: String,
    collateral_response_sha256: String,
    collateral_field_digests: BTreeMap<String, String>,
    started_at: u64,
    finished_at: u64,
    claim_boundary: String,
    non_claims: Vec<String>,
}

fn invalid_input(message: impl Into<String>) -> IoError {
    IoError::new(ErrorKind::InvalidInput, message.into())
}

fn sha256_hex(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    let mut out = String::with_capacity(digest.len() * 2);
    for byte in digest {
        out.push_str(&format!("{byte:02x}"));
    }
    out
}

fn read_input() -> Result<DcapPccsRunInput, Box<dyn Error>> {
    let ack = env::var(ACK_ENV).map_err(|_| invalid_input(format!("{ACK_ENV} is required")))?;
    if ack != ACK_VALUE {
        return Err(invalid_input(format!("{ACK_ENV} must equal {ACK_VALUE}")).into());
    }
    let input_path = env::var(INPUT_JSON_ENV)
        .map_err(|_| invalid_input(format!("{INPUT_JSON_ENV} is required")))?;
    let input_bytes = fs::read(input_path)?;
    Ok(serde_json::from_slice(&input_bytes)?)
}

fn require_nonempty(field: &str, value: &str) -> Result<(), IoError> {
    if value.trim().is_empty() {
        return Err(invalid_input(format!("{field} is empty")));
    }
    Ok(())
}

fn collateral_digests(
    collateral: &PhalaCollateralResponse,
) -> Result<BTreeMap<String, String>, IoError> {
    let fields = [
        ("pck_crl", collateral.pck_crl.as_str()),
        (
            "pck_crl_issuer_chain",
            collateral.pck_crl_issuer_chain.as_str(),
        ),
        ("qe_identity", collateral.qe_identity.as_str()),
        (
            "qe_identity_issuer_chain",
            collateral.qe_identity_issuer_chain.as_str(),
        ),
        (
            "qe_identity_signature",
            collateral.qe_identity_signature.as_str(),
        ),
        ("root_ca_crl", collateral.root_ca_crl.as_str()),
        ("tcb_info", collateral.tcb_info.as_str()),
        (
            "tcb_info_issuer_chain",
            collateral.tcb_info_issuer_chain.as_str(),
        ),
        ("tcb_info_signature", collateral.tcb_info_signature.as_str()),
    ];
    let mut out = BTreeMap::new();
    for (field, value) in fields {
        require_nonempty(field, value)?;
        out.insert(field.to_owned(), sha256_hex(value.as_bytes()));
    }
    Ok(out)
}

fn ensure_output_root(path: &Path) -> Result<(), IoError> {
    if path.as_os_str().is_empty() {
        return Err(invalid_input("output_root is empty"));
    }
    if path.exists() && !path.is_dir() {
        return Err(invalid_input("output_root exists and is not a directory"));
    }
    fs::create_dir_all(path)
}

fn write_json<T: Serialize>(path: &Path, value: &T) -> Result<(), Box<dyn Error>> {
    let bytes = serde_json::to_vec_pretty(value)?;
    fs::write(path, bytes)?;
    Ok(())
}

fn run() -> Result<(), Box<dyn Error>> {
    let input = read_input()?;
    let verify_bytes = fs::read(&input.phala_verify_response_path)?;
    let collateral_bytes = fs::read(&input.phala_collateral_response_path)?;
    let verify: PhalaVerifyResponse = serde_json::from_slice(&verify_bytes)?;
    let collateral: PhalaCollateralResponse = serde_json::from_slice(&collateral_bytes)?;

    if !verify.success || !verify.quote.verified {
        return Err(invalid_input("Phala verification response was not accepted").into());
    }
    if verify.checksum != input.checksum {
        return Err(invalid_input("verification checksum does not match input checksum").into());
    }
    if verify.quote.header.tee_type != "TEE_TDX" {
        return Err(invalid_input("verification response is not TEE_TDX").into());
    }

    let collateral_field_digests = collateral_digests(&collateral)?;
    let output_dir = input.output_root.join("dcap-pccs");
    ensure_output_root(&output_dir)?;

    let summary = DcapPccsSummary {
        schema_version: "hsai.phala.dcap-pccs-artifact.v1".to_owned(),
        operator_run_id: input.operator_run_id,
        checksum: input.checksum,
        provider: "phala-dstack".to_owned(),
        verification_mode: "phala-cloud-attestations-collateral".to_owned(),
        tee_type: verify.quote.header.tee_type,
        phala_verify_endpoint: input.phala_verify_endpoint,
        phala_collateral_endpoint: input.phala_collateral_endpoint,
        verify_response_sha256: sha256_hex(&verify_bytes),
        collateral_response_sha256: sha256_hex(&collateral_bytes),
        collateral_field_digests,
        started_at: input.started_at,
        finished_at: input.finished_at,
        claim_boundary: "Attested".to_owned(),
        non_claims: vec![
            "not proof".to_owned(),
            "not local DCAP quote verification".to_owned(),
            "not local PCCS service operation".to_owned(),
            "not managed-service signature/JWKS/JWT verification".to_owned(),
            "not TLS channel binding".to_owned(),
            "not benchmark evidence".to_owned(),
            "not accepted evidence".to_owned(),
            "not semantic correctness".to_owned(),
        ],
    };

    write_json(&output_dir.join("summary.json"), &summary)?;
    fs::write(
        output_dir.join("raw-verification-response.sha256"),
        format!("{}\n", summary.verify_response_sha256),
    )?;
    fs::write(
        output_dir.join("raw-collateral-response.sha256"),
        format!("{}\n", summary.collateral_response_sha256),
    )?;

    println!("operator_run_id={}", summary.operator_run_id);
    println!("checksum={}", summary.checksum);
    println!("claim_boundary={}", summary.claim_boundary);
    println!(
        "collateral_response_sha256={}",
        summary.collateral_response_sha256
    );
    println!("dcap_pccs_output_root={}", input.output_root.display());
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    run()
}

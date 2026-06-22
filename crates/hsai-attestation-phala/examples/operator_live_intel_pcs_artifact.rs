use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::env;
use std::error::Error;
use std::fs;
use std::io::{Error as IoError, ErrorKind};
use std::path::{Path, PathBuf};

const ACK_ENV: &str = "HSAI_PHALA_OPERATOR_ACK";
const ACK_VALUE: &str = "I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN";
const INPUT_JSON_ENV: &str = "HSAI_PHALA_INTEL_PCS_INPUT_JSON";
const INTEL_PCS_URL: &str = "https://api.trustedservices.intel.com";

#[derive(Deserialize)]
struct IntelPcsRunInput {
    operator_run_id: String,
    checksum: String,
    raw_quote_path: PathBuf,
    pck_info_path: PathBuf,
    qvl_report_path: PathBuf,
    qvl_stderr_path: PathBuf,
    qvl_tool: String,
    qvl_tool_version: String,
    pccs_url: String,
    output_root: PathBuf,
    started_at: u64,
    finished_at: u64,
}

#[derive(Deserialize)]
struct PckInfo {
    quote_version: u64,
    tee_type: String,
    fmspc: String,
    certificate_chain: Vec<PckCertificateInfo>,
}

#[derive(Deserialize)]
struct PckCertificateInfo {
    role: String,
}

#[derive(Deserialize)]
struct QvlReport {
    status: String,
    advisory_ids: Vec<String>,
    qe_status: QvlStatus,
    platform_status: QvlStatus,
}

#[derive(Deserialize)]
struct QvlStatus {
    status: String,
    advisory_ids: Vec<String>,
}

#[derive(Serialize)]
struct IntelPcsSummary {
    schema_version: String,
    operator_run_id: String,
    checksum: String,
    provider: String,
    verification_mode: String,
    qvl_tool: String,
    qvl_tool_version: String,
    pccs_url: String,
    tee_type: String,
    qvl_status: String,
    qe_status: String,
    platform_status: String,
    advisory_ids: Vec<String>,
    qe_advisory_ids: Vec<String>,
    platform_advisory_ids: Vec<String>,
    fmspc: String,
    raw_quote_sha256: String,
    pck_info_sha256: String,
    qvl_report_sha256: String,
    qvl_stderr_sha256: String,
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

fn read_json<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<(T, Vec<u8>), Box<dyn Error>> {
    let bytes = fs::read(path)?;
    let value = serde_json::from_slice(&bytes)?;
    Ok((value, bytes))
}

fn read_input() -> Result<IntelPcsRunInput, Box<dyn Error>> {
    let ack = env::var(ACK_ENV).map_err(|_| invalid_input(format!("{ACK_ENV} is required")))?;
    if ack != ACK_VALUE {
        return Err(invalid_input(format!("{ACK_ENV} must equal {ACK_VALUE}")).into());
    }
    let input_path = env::var(INPUT_JSON_ENV)
        .map_err(|_| invalid_input(format!("{INPUT_JSON_ENV} is required")))?;
    let input_bytes = fs::read(input_path)?;
    Ok(serde_json::from_slice(&input_bytes)?)
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

fn require_up_to_date(label: &str, status: &QvlStatus) -> Result<(), IoError> {
    if status.status != "UpToDate" {
        return Err(invalid_input(format!(
            "{label} status must be UpToDate, got {}",
            status.status
        )));
    }
    if !status.advisory_ids.is_empty() {
        return Err(invalid_input(format!(
            "{label} advisory_ids must be empty for this materializer"
        )));
    }
    Ok(())
}

fn run() -> Result<(), Box<dyn Error>> {
    let input = read_input()?;
    if input.pccs_url != INTEL_PCS_URL {
        return Err(invalid_input(format!("pccs_url must equal {INTEL_PCS_URL}")).into());
    }

    let raw_quote_bytes = fs::read(&input.raw_quote_path)?;
    let (pck_info, pck_info_bytes): (PckInfo, Vec<u8>) = read_json(&input.pck_info_path)?;
    let (qvl_report, qvl_report_bytes): (QvlReport, Vec<u8>) = read_json(&input.qvl_report_path)?;
    let qvl_stderr_bytes = fs::read(&input.qvl_stderr_path)?;

    if raw_quote_bytes.is_empty() {
        return Err(invalid_input("raw quote is empty").into());
    }
    if pck_info.quote_version != 4 || pck_info.tee_type != "TDX" {
        return Err(invalid_input("PCK info is not TDX quote version 4").into());
    }
    let roles = pck_info
        .certificate_chain
        .iter()
        .map(|cert| cert.role.as_str())
        .collect::<Vec<_>>();
    if roles != ["Leaf PCK", "PCK CA", "Root CA"] {
        return Err(invalid_input("PCK certificate chain roles are unexpected").into());
    }
    if qvl_report.status != "UpToDate" {
        return Err(invalid_input("QVL report status must be UpToDate").into());
    }
    if !qvl_report.advisory_ids.is_empty() {
        return Err(
            invalid_input("QVL report advisory_ids must be empty for this materializer").into(),
        );
    }
    require_up_to_date("QE", &qvl_report.qe_status)?;
    require_up_to_date("platform", &qvl_report.platform_status)?;

    let output_dir = input.output_root.join("intel-pcs");
    ensure_output_root(&output_dir)?;

    let summary = IntelPcsSummary {
        schema_version: "hsai.phala.intel-pcs-artifact.v1".to_owned(),
        operator_run_id: input.operator_run_id,
        checksum: input.checksum,
        provider: "phala-dstack".to_owned(),
        verification_mode: "operator-direct-intel-pcs-qvl".to_owned(),
        qvl_tool: input.qvl_tool,
        qvl_tool_version: input.qvl_tool_version,
        pccs_url: input.pccs_url,
        tee_type: "TDX".to_owned(),
        qvl_status: qvl_report.status,
        qe_status: qvl_report.qe_status.status,
        platform_status: qvl_report.platform_status.status,
        advisory_ids: qvl_report.advisory_ids,
        qe_advisory_ids: qvl_report.qe_status.advisory_ids,
        platform_advisory_ids: qvl_report.platform_status.advisory_ids,
        fmspc: pck_info.fmspc,
        raw_quote_sha256: sha256_hex(&raw_quote_bytes),
        pck_info_sha256: sha256_hex(&pck_info_bytes),
        qvl_report_sha256: sha256_hex(&qvl_report_bytes),
        qvl_stderr_sha256: sha256_hex(&qvl_stderr_bytes),
        started_at: input.started_at,
        finished_at: input.finished_at,
        claim_boundary: "Attested".to_owned(),
        non_claims: vec![
            "not proof".to_owned(),
            "not repo-native DCAP verifier implementation".to_owned(),
            "not managed-service signature/JWKS/JWT verification".to_owned(),
            "not TLS channel binding".to_owned(),
            "not benchmark evidence".to_owned(),
            "not accepted evidence".to_owned(),
            "not semantic correctness".to_owned(),
        ],
    };

    write_json(&output_dir.join("summary.json"), &summary)?;
    fs::write(
        output_dir.join("raw-quote.sha256"),
        format!("{}\n", summary.raw_quote_sha256),
    )?;
    fs::write(
        output_dir.join("pck-info.sha256"),
        format!("{}\n", summary.pck_info_sha256),
    )?;
    fs::write(
        output_dir.join("qvl-report.sha256"),
        format!("{}\n", summary.qvl_report_sha256),
    )?;
    fs::write(
        output_dir.join("qvl-stderr.sha256"),
        format!("{}\n", summary.qvl_stderr_sha256),
    )?;

    println!("operator_run_id={}", summary.operator_run_id);
    println!("checksum={}", summary.checksum);
    println!("claim_boundary={}", summary.claim_boundary);
    println!("pccs_url={}", summary.pccs_url);
    println!("qvl_status={}", summary.qvl_status);
    println!("qvl_report_sha256={}", summary.qvl_report_sha256);
    println!("intel_pcs_output_root={}", input.output_root.display());
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    run()
}

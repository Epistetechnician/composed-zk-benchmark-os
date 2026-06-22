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
const INPUT_JSON_ENV: &str = "HSAI_PHALA_DCAP_QVL_INPUT_JSON";

#[derive(Deserialize)]
struct DcapQvlRunInput {
    operator_run_id: String,
    checksum: String,
    phala_verify_response_path: PathBuf,
    raw_quote_path: PathBuf,
    decoded_quote_path: PathBuf,
    pck_info_path: PathBuf,
    qvl_report_path: PathBuf,
    qvl_tool: String,
    qvl_tool_version: String,
    pccs_url: String,
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
    mrtd: String,
    mrseam: String,
    mrsignerseam: String,
}

#[derive(Deserialize)]
struct DecodedQuote {
    header: DecodedQuoteHeader,
    report: BTreeMap<String, TdxReport>,
}

#[derive(Deserialize)]
struct DecodedQuoteHeader {
    version: u64,
    tee_type: u64,
}

#[derive(Deserialize)]
struct TdxReport {
    mr_seam: String,
    mr_signer_seam: String,
    mr_td: String,
    rt_mr0: String,
    rt_mr1: String,
    rt_mr2: String,
    rt_mr3: String,
    report_data: String,
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
    report: BTreeMap<String, TdxReport>,
    qe_status: QvlStatus,
    platform_status: QvlStatus,
}

#[derive(Deserialize)]
struct QvlStatus {
    status: String,
    advisory_ids: Vec<String>,
}

#[derive(Serialize)]
struct DcapQvlSummary {
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
    phala_verify_response_sha256: String,
    decoded_quote_sha256: String,
    pck_info_sha256: String,
    qvl_report_sha256: String,
    matched_measurements: Vec<String>,
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

fn normalized_hex(value: &str) -> String {
    value
        .strip_prefix("0x")
        .unwrap_or(value)
        .to_ascii_lowercase()
}

fn read_json<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<(T, Vec<u8>), Box<dyn Error>> {
    let bytes = fs::read(path)?;
    let value = serde_json::from_slice(&bytes)?;
    Ok((value, bytes))
}

fn read_input() -> Result<DcapQvlRunInput, Box<dyn Error>> {
    let ack = env::var(ACK_ENV).map_err(|_| invalid_input(format!("{ACK_ENV} is required")))?;
    if ack != ACK_VALUE {
        return Err(invalid_input(format!("{ACK_ENV} must equal {ACK_VALUE}")).into());
    }
    let input_path = env::var(INPUT_JSON_ENV)
        .map_err(|_| invalid_input(format!("{INPUT_JSON_ENV} is required")))?;
    let input_bytes = fs::read(input_path)?;
    Ok(serde_json::from_slice(&input_bytes)?)
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

fn single_tdx_report<'a>(
    label: &str,
    report: &'a BTreeMap<String, TdxReport>,
) -> Result<(&'a str, &'a TdxReport), IoError> {
    if report.len() != 1 {
        return Err(invalid_input(format!("{label} must contain one TD report")));
    }
    let (kind, report) = report
        .iter()
        .next()
        .ok_or_else(|| invalid_input(format!("{label} is empty")))?;
    Ok((kind.as_str(), report))
}

fn require_equal(label: &str, left: &str, right: &str) -> Result<(), IoError> {
    if normalized_hex(left) != normalized_hex(right) {
        return Err(invalid_input(format!("{label} mismatch")));
    }
    Ok(())
}

fn compare_reports(
    phala: &PhalaQuoteBody,
    decoded: &TdxReport,
    qvl: &TdxReport,
) -> Result<Vec<String>, IoError> {
    let comparisons = [
        (
            "report_data",
            phala.reportdata.as_str(),
            decoded.report_data.as_str(),
            qvl.report_data.as_str(),
        ),
        (
            "rtmr0",
            phala.rtmr0.as_str(),
            decoded.rt_mr0.as_str(),
            qvl.rt_mr0.as_str(),
        ),
        (
            "rtmr1",
            phala.rtmr1.as_str(),
            decoded.rt_mr1.as_str(),
            qvl.rt_mr1.as_str(),
        ),
        (
            "rtmr2",
            phala.rtmr2.as_str(),
            decoded.rt_mr2.as_str(),
            qvl.rt_mr2.as_str(),
        ),
        (
            "rtmr3",
            phala.rtmr3.as_str(),
            decoded.rt_mr3.as_str(),
            qvl.rt_mr3.as_str(),
        ),
        (
            "mrtd",
            phala.mrtd.as_str(),
            decoded.mr_td.as_str(),
            qvl.mr_td.as_str(),
        ),
        (
            "mrseam",
            phala.mrseam.as_str(),
            decoded.mr_seam.as_str(),
            qvl.mr_seam.as_str(),
        ),
        (
            "mrsignerseam",
            phala.mrsignerseam.as_str(),
            decoded.mr_signer_seam.as_str(),
            qvl.mr_signer_seam.as_str(),
        ),
    ];
    let mut matched = Vec::with_capacity(comparisons.len());
    for (label, phala_value, decoded_value, qvl_value) in comparisons {
        require_equal(
            &format!("{label} Phala-vs-decoded"),
            phala_value,
            decoded_value,
        )?;
        require_equal(&format!("{label} Phala-vs-qvl"), phala_value, qvl_value)?;
        matched.push(label.to_owned());
    }
    Ok(matched)
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
    let (phala, phala_bytes): (PhalaVerifyResponse, Vec<u8>) =
        read_json(&input.phala_verify_response_path)?;
    let raw_quote_bytes = fs::read(&input.raw_quote_path)?;
    let (decoded, decoded_bytes): (DecodedQuote, Vec<u8>) = read_json(&input.decoded_quote_path)?;
    let (pck_info, pck_info_bytes): (PckInfo, Vec<u8>) = read_json(&input.pck_info_path)?;
    let (qvl_report, qvl_report_bytes): (QvlReport, Vec<u8>) = read_json(&input.qvl_report_path)?;

    if raw_quote_bytes.is_empty() {
        return Err(invalid_input("raw quote is empty").into());
    }
    if !phala.success || !phala.quote.verified {
        return Err(invalid_input("Phala verification response was not accepted").into());
    }
    if phala.checksum != input.checksum {
        return Err(invalid_input("Phala checksum does not match input checksum").into());
    }
    if phala.quote.header.tee_type != "TEE_TDX" {
        return Err(invalid_input("Phala verification response is not TEE_TDX").into());
    }
    if decoded.header.version != 4 || decoded.header.tee_type != 129 {
        return Err(invalid_input("decoded quote is not TDX quote version 4").into());
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

    let (decoded_report_kind, decoded_report) =
        single_tdx_report("decoded quote report", &decoded.report)?;
    let (qvl_report_kind, qvl_tdx_report) = single_tdx_report("QVL report", &qvl_report.report)?;
    if decoded_report_kind != qvl_report_kind {
        return Err(invalid_input("decoded quote and QVL report kinds differ").into());
    }
    let matched_measurements = compare_reports(&phala.quote.body, decoded_report, qvl_tdx_report)?;

    let output_dir = input.output_root.join("dcap-qvl");
    ensure_output_root(&output_dir)?;

    let summary = DcapQvlSummary {
        schema_version: "hsai.phala.dcap-qvl-artifact.v1".to_owned(),
        operator_run_id: input.operator_run_id,
        checksum: input.checksum,
        provider: "phala-dstack".to_owned(),
        verification_mode: "operator-local-dcap-qvl".to_owned(),
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
        phala_verify_response_sha256: sha256_hex(&phala_bytes),
        decoded_quote_sha256: sha256_hex(&decoded_bytes),
        pck_info_sha256: sha256_hex(&pck_info_bytes),
        qvl_report_sha256: sha256_hex(&qvl_report_bytes),
        matched_measurements,
        started_at: input.started_at,
        finished_at: input.finished_at,
        claim_boundary: "Attested".to_owned(),
        non_claims: vec![
            "not proof".to_owned(),
            "not repo-native DCAP verifier implementation".to_owned(),
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
        output_dir.join("raw-quote.sha256"),
        format!("{}\n", summary.raw_quote_sha256),
    )?;
    fs::write(
        output_dir.join("qvl-report.sha256"),
        format!("{}\n", summary.qvl_report_sha256),
    )?;
    fs::write(
        output_dir.join("pck-info.sha256"),
        format!("{}\n", summary.pck_info_sha256),
    )?;
    fs::write(
        output_dir.join("decoded-quote.sha256"),
        format!("{}\n", summary.decoded_quote_sha256),
    )?;

    println!("operator_run_id={}", summary.operator_run_id);
    println!("checksum={}", summary.checksum);
    println!("claim_boundary={}", summary.claim_boundary);
    println!("qvl_status={}", summary.qvl_status);
    println!("raw_quote_sha256={}", summary.raw_quote_sha256);
    println!("qvl_report_sha256={}", summary.qvl_report_sha256);
    println!("dcap_qvl_output_root={}", input.output_root.display());
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    run()
}

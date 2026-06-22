use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::env;
use std::error::Error;
use std::fs;
use std::io::{Error as IoError, ErrorKind};
use std::path::{Path, PathBuf};

const ACK_ENV: &str = "HSAI_PHALA_OPERATOR_ACK";
const ACK_VALUE: &str = "I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN";
const INPUT_JSON_ENV: &str = "HSAI_PHALA_LOCAL_PCCS_INPUT_JSON";

#[derive(Deserialize)]
struct LocalPccsRunInput {
    operator_run_id: String,
    checksum: String,
    raw_quote_path: PathBuf,
    pck_info_path: PathBuf,
    qvl_report_path: PathBuf,
    access_log_path: PathBuf,
    pck_crl_response_path: PathBuf,
    tcb_response_path: PathBuf,
    qe_identity_response_path: PathBuf,
    root_ca_crl_response_path: PathBuf,
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

#[derive(Deserialize)]
struct PccsAccessEntry {
    method: String,
    path: String,
    query: String,
    status: u16,
    response_file: Option<String>,
    body_sha256: String,
}

#[derive(Serialize)]
struct LocalPccsSummary {
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
    accessed_endpoints: Vec<String>,
    raw_quote_sha256: String,
    pck_info_sha256: String,
    qvl_report_sha256: String,
    access_log_sha256: String,
    pck_crl_response_sha256: String,
    tcb_response_sha256: String,
    qe_identity_response_sha256: String,
    root_ca_crl_response_sha256: String,
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

fn read_input() -> Result<LocalPccsRunInput, Box<dyn Error>> {
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

fn require_localhost_pccs_url(url: &str) -> Result<(), IoError> {
    if url.starts_with("http://127.0.0.1:") || url.starts_with("http://localhost:") {
        return Ok(());
    }
    Err(invalid_input(
        "pccs_url must be an explicit localhost HTTP endpoint",
    ))
}

fn read_access_log(path: &Path) -> Result<(Vec<PccsAccessEntry>, Vec<u8>), Box<dyn Error>> {
    let bytes = fs::read(path)?;
    let text = String::from_utf8(bytes.clone())?;
    let mut entries = Vec::new();
    for (index, line) in text.lines().enumerate() {
        if line.trim().is_empty() {
            continue;
        }
        let entry = serde_json::from_str(line)
            .map_err(|err| invalid_input(format!("invalid access log line {index}: {err}")))?;
        entries.push(entry);
    }
    Ok((entries, bytes))
}

fn require_required_accesses(
    entries: &[PccsAccessEntry],
    fmspc: &str,
    response_digests: &BTreeMap<&str, String>,
) -> Result<Vec<String>, IoError> {
    let mut required = BTreeMap::new();
    required.insert(
        "/sgx/certification/v4/pckcrl",
        BTreeSet::from([
            "ca=processor&encoding=der".to_owned(),
            "ca=platform&encoding=der".to_owned(),
        ]),
    );
    required.insert(
        "/tdx/certification/v4/tcb",
        BTreeSet::from([format!("fmspc={}", fmspc.to_ascii_uppercase())]),
    );
    required.insert(
        "/tdx/certification/v4/qe/identity",
        BTreeSet::from(["update=standard".to_owned()]),
    );
    required.insert(
        "/sgx/certification/v4/rootcacrl",
        BTreeSet::from(["".to_owned()]),
    );

    let file_for_path = BTreeMap::from([
        ("/sgx/certification/v4/pckcrl", "pck_crl.der"),
        ("/tdx/certification/v4/tcb", "tcb.json"),
        ("/tdx/certification/v4/qe/identity", "qe_identity.json"),
        ("/sgx/certification/v4/rootcacrl", "root_ca_crl.hex"),
    ]);

    let mut observed = BTreeSet::new();
    for entry in entries {
        if entry.method != "GET" {
            return Err(invalid_input(
                "local PCCS access log contains non-GET method",
            ));
        }
        if entry.status != 200 {
            return Err(invalid_input(
                "local PCCS access log contains non-200 status",
            ));
        }
        let expected_queries = required
            .get(entry.path.as_str())
            .ok_or_else(|| invalid_input(format!("unexpected PCCS path {}", entry.path)))?;
        if !expected_queries.contains(&entry.query) {
            return Err(invalid_input(format!(
                "unexpected query {} for PCCS path {}",
                entry.query, entry.path
            )));
        }
        let expected_file = file_for_path
            .get(entry.path.as_str())
            .ok_or_else(|| invalid_input("missing response-file expectation"))?;
        if entry.response_file.as_deref() != Some(*expected_file) {
            return Err(invalid_input(format!(
                "unexpected response file for {}",
                entry.path
            )));
        }
        let expected_digest = response_digests
            .get(*expected_file)
            .ok_or_else(|| invalid_input("missing response digest"))?;
        if &entry.body_sha256 != expected_digest {
            return Err(invalid_input(format!(
                "response digest mismatch for {}",
                entry.path
            )));
        }
        observed.insert(format!("{}?{}", entry.path, entry.query));
    }

    for (path, queries) in required {
        if path == "/sgx/certification/v4/pckcrl" {
            if !queries
                .iter()
                .any(|query| observed.contains(&format!("{path}?{query}")))
            {
                return Err(invalid_input("missing required PCCS pckcrl access"));
            }
            continue;
        }
        for query in queries {
            if !observed.contains(&format!("{path}?{query}")) {
                return Err(invalid_input(format!(
                    "missing required PCCS access {path}"
                )));
            }
        }
    }

    Ok(observed.into_iter().collect())
}

fn run() -> Result<(), Box<dyn Error>> {
    let input = read_input()?;
    require_localhost_pccs_url(&input.pccs_url)?;

    let raw_quote_bytes = fs::read(&input.raw_quote_path)?;
    let (pck_info, pck_info_bytes): (PckInfo, Vec<u8>) = read_json(&input.pck_info_path)?;
    let (qvl_report, qvl_report_bytes): (QvlReport, Vec<u8>) = read_json(&input.qvl_report_path)?;
    let (access_entries, access_log_bytes) = read_access_log(&input.access_log_path)?;
    let pck_crl_bytes = fs::read(&input.pck_crl_response_path)?;
    let tcb_response_bytes = fs::read(&input.tcb_response_path)?;
    let qe_identity_response_bytes = fs::read(&input.qe_identity_response_path)?;
    let root_ca_crl_response_bytes = fs::read(&input.root_ca_crl_response_path)?;

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

    let pck_crl_response_sha256 = sha256_hex(&pck_crl_bytes);
    let tcb_response_sha256 = sha256_hex(&tcb_response_bytes);
    let qe_identity_response_sha256 = sha256_hex(&qe_identity_response_bytes);
    let root_ca_crl_response_sha256 = sha256_hex(&root_ca_crl_response_bytes);
    let response_digests = BTreeMap::from([
        ("pck_crl.der", pck_crl_response_sha256.clone()),
        ("tcb.json", tcb_response_sha256.clone()),
        ("qe_identity.json", qe_identity_response_sha256.clone()),
        ("root_ca_crl.hex", root_ca_crl_response_sha256.clone()),
    ]);
    let accessed_endpoints =
        require_required_accesses(&access_entries, &pck_info.fmspc, &response_digests)?;

    let output_dir = input.output_root.join("local-pccs");
    ensure_output_root(&output_dir)?;

    let summary = LocalPccsSummary {
        schema_version: "hsai.phala.local-pccs-artifact.v1".to_owned(),
        operator_run_id: input.operator_run_id,
        checksum: input.checksum,
        provider: "phala-dstack".to_owned(),
        verification_mode: "operator-local-pccs-replay-qvl".to_owned(),
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
        accessed_endpoints,
        raw_quote_sha256: sha256_hex(&raw_quote_bytes),
        pck_info_sha256: sha256_hex(&pck_info_bytes),
        qvl_report_sha256: sha256_hex(&qvl_report_bytes),
        access_log_sha256: sha256_hex(&access_log_bytes),
        pck_crl_response_sha256,
        tcb_response_sha256,
        qe_identity_response_sha256,
        root_ca_crl_response_sha256,
        started_at: input.started_at,
        finished_at: input.finished_at,
        claim_boundary: "Attested".to_owned(),
        non_claims: vec![
            "not proof".to_owned(),
            "not production Intel PCS/PCCS operation".to_owned(),
            "not fresh collateral authority".to_owned(),
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
        output_dir.join("access-log.sha256"),
        format!("{}\n", summary.access_log_sha256),
    )?;
    fs::write(
        output_dir.join("pck-crl-response.sha256"),
        format!("{}\n", summary.pck_crl_response_sha256),
    )?;
    fs::write(
        output_dir.join("tcb-response.sha256"),
        format!("{}\n", summary.tcb_response_sha256),
    )?;
    fs::write(
        output_dir.join("qe-identity-response.sha256"),
        format!("{}\n", summary.qe_identity_response_sha256),
    )?;
    fs::write(
        output_dir.join("root-ca-crl-response.sha256"),
        format!("{}\n", summary.root_ca_crl_response_sha256),
    )?;

    println!("operator_run_id={}", summary.operator_run_id);
    println!("checksum={}", summary.checksum);
    println!("claim_boundary={}", summary.claim_boundary);
    println!("qvl_status={}", summary.qvl_status);
    println!("pccs_url={}", summary.pccs_url);
    println!("access_log_sha256={}", summary.access_log_sha256);
    println!("qvl_report_sha256={}", summary.qvl_report_sha256);
    println!("local_pccs_output_root={}", input.output_root.display());
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    run()
}

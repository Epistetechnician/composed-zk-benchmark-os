#![cfg_attr(not(feature = "operator-live-provider"), allow(dead_code))]

#[cfg(feature = "operator-live-provider")]
use hsai_attestation_phala::{
    PhalaEnvCredentialProvider, PhalaOperatorLiveInvocation, PhalaOperatorLiveInvocationInput,
    PhalaOperatorLiveOutputOverwriteMode, PhalaOperatorLiveProviderClient,
    PhalaOperatorLiveProviderConfig, UreqPhalaOperatorLiveTransport,
};
#[cfg(feature = "operator-live-provider")]
use std::collections::{BTreeMap, BTreeSet};
#[cfg(feature = "operator-live-provider")]
use std::env;
#[cfg(feature = "operator-live-provider")]
use std::error::Error;
#[cfg(feature = "operator-live-provider")]
use std::fs;
#[cfg(feature = "operator-live-provider")]
use std::io::{Error as IoError, ErrorKind};
#[cfg(feature = "operator-live-provider")]
use std::path::PathBuf;

#[cfg(feature = "operator-live-provider")]
const ACK_ENV: &str = "HSAI_PHALA_OPERATOR_ACK";
#[cfg(feature = "operator-live-provider")]
const ACK_VALUE: &str = "I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN";
#[cfg(feature = "operator-live-provider")]
const INPUT_JSON_ENV: &str = "HSAI_PHALA_OPERATOR_INPUT_JSON";
#[cfg(feature = "operator-live-provider")]
const CREDENTIAL_SOURCE_ENV: &str = "HSAI_PHALA_OPERATOR_CREDENTIAL_SOURCE";

#[cfg(feature = "operator-live-provider")]
#[derive(serde::Deserialize)]
struct OperatorLiveRunInput {
    operator_run_id: String,
    operator_acknowledged: bool,
    provider_endpoint: String,
    credential_source: String,
    timeout_seconds: u64,
    retry_limit: u64,
    anchor_id: String,
    agent_pubkey: Vec<u8>,
    case_hash: Vec<u8>,
    nonce: u64,
    expected_report_data_binding: Vec<u8>,
    expected_compose_hash: Vec<u8>,
    expected_runtime_measurements: BTreeSet<String>,
    expected_image_digest: String,
    request_time: u64,
    started_at: u64,
    output_root: PathBuf,
    overwrite: Option<PhalaOperatorLiveOutputOverwriteMode>,
    #[serde(default)]
    extra_operator_notes: BTreeMap<String, String>,
}

#[cfg(feature = "operator-live-provider")]
impl OperatorLiveRunInput {
    fn into_invocation_input(self) -> PhalaOperatorLiveInvocationInput {
        let _ = self.extra_operator_notes;
        PhalaOperatorLiveInvocationInput {
            operator_run_id: self.operator_run_id,
            operator_acknowledged: self.operator_acknowledged,
            provider_endpoint: self.provider_endpoint,
            credential_source: self.credential_source,
            timeout_seconds: self.timeout_seconds,
            retry_limit: self.retry_limit,
            anchor_id: self.anchor_id,
            agent_pubkey: self.agent_pubkey,
            case_hash: self.case_hash,
            nonce: self.nonce,
            expected_report_data_binding: self.expected_report_data_binding,
            expected_compose_hash: self.expected_compose_hash,
            expected_runtime_measurements: self.expected_runtime_measurements,
            expected_image_digest: self.expected_image_digest,
            request_time: self.request_time,
            started_at: self.started_at,
            output_root: self.output_root,
            overwrite: self
                .overwrite
                .unwrap_or(PhalaOperatorLiveOutputOverwriteMode::RefuseExisting),
        }
    }
}

#[cfg(feature = "operator-live-provider")]
fn invalid_input(message: impl Into<String>) -> IoError {
    IoError::new(ErrorKind::InvalidInput, message.into())
}

#[cfg(feature = "operator-live-provider")]
fn read_invocation_input() -> Result<PhalaOperatorLiveInvocationInput, Box<dyn Error>> {
    let ack = env::var(ACK_ENV).map_err(|_| invalid_input(format!("{ACK_ENV} is required")))?;
    if ack != ACK_VALUE {
        return Err(invalid_input(format!("{ACK_ENV} must equal {ACK_VALUE}")).into());
    }

    let input_path = env::var(INPUT_JSON_ENV)
        .map_err(|_| invalid_input(format!("{INPUT_JSON_ENV} is required")))?;
    let input_bytes = fs::read(&input_path)?;
    let input: OperatorLiveRunInput = serde_json::from_slice(&input_bytes)?;
    let invocation_input = input.into_invocation_input();

    let declared_source = env::var(CREDENTIAL_SOURCE_ENV)
        .map_err(|_| invalid_input(format!("{CREDENTIAL_SOURCE_ENV} is required")))?;
    if declared_source != invocation_input.credential_source {
        return Err(invalid_input(format!(
            "{CREDENTIAL_SOURCE_ENV} must match invocation credential_source"
        ))
        .into());
    }

    Ok(invocation_input)
}

#[cfg(feature = "operator-live-provider")]
fn run() -> Result<(), Box<dyn Error>> {
    let input = read_invocation_input()?;
    let allowed_sources = BTreeSet::from([input.credential_source.clone()]);
    let config = PhalaOperatorLiveProviderConfig::new(
        input.provider_endpoint.clone(),
        input.timeout_seconds,
        allowed_sources.clone(),
    );
    let client = PhalaOperatorLiveProviderClient::new(config, UreqPhalaOperatorLiveTransport);
    let credential_provider = PhalaEnvCredentialProvider::new(allowed_sources);
    let invocation = PhalaOperatorLiveInvocation::new(client, credential_provider);
    let validated = invocation.invoke(&input)?;

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

#[cfg(feature = "operator-live-provider")]
fn main() -> Result<(), Box<dyn Error>> {
    run()
}

#[cfg(not(feature = "operator-live-provider"))]
fn main() {
    eprintln!("operator_live_run requires --features operator-live-provider");
}

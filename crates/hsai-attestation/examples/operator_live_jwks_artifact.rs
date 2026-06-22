use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
use std::env;
use std::error::Error;
use std::fs;
use std::io::{Error as IoError, ErrorKind};
use std::path::{Path, PathBuf};

const ACK_ENV: &str = "HSAI_MANAGED_JWKS_OPERATOR_ACK";
const ACK_VALUE: &str = "I_ACKNOWLEDGE_OPERATOR_LIVE_JWKS_FETCH";
const INPUT_JSON_ENV: &str = "HSAI_MANAGED_JWKS_INPUT_JSON";

#[derive(Deserialize)]
struct ManagedJwksRunInput {
    operator_run_id: String,
    provider: String,
    issuer: String,
    openid_configuration_url: String,
    jwks_uri: String,
    openid_response_path: PathBuf,
    jwks_response_path: PathBuf,
    output_root: PathBuf,
    started_at: u64,
    finished_at: u64,
}

#[derive(Deserialize)]
struct OpenIdConfiguration {
    issuer: String,
    jwks_uri: String,
    id_token_signing_alg_values_supported: Vec<String>,
    response_types_supported: Vec<String>,
    claims_supported: Vec<String>,
}

#[derive(Deserialize)]
struct JwksResponse {
    keys: Vec<Jwk>,
}

#[derive(Deserialize)]
struct Jwk {
    kty: String,
    kid: String,
    alg: Option<String>,
    n: Option<String>,
    e: Option<String>,
    x5c: Option<Vec<String>>,
}

#[derive(Serialize)]
struct JwkDigestSummary {
    kid: String,
    kty: String,
    alg: String,
    n_sha256: String,
    e_sha256: String,
    x5c_chain_len: usize,
    x5c_leaf_sha256: Option<String>,
}

#[derive(Serialize)]
struct ManagedJwksSummary {
    schema_version: String,
    operator_run_id: String,
    provider: String,
    issuer: String,
    verification_mode: String,
    openid_configuration_url: String,
    jwks_uri: String,
    openid_response_sha256: String,
    jwks_response_sha256: String,
    supported_signing_algorithms: Vec<String>,
    response_types_supported: Vec<String>,
    claims_supported_count: usize,
    key_count: usize,
    key_digests: Vec<JwkDigestSummary>,
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

fn read_input() -> Result<ManagedJwksRunInput, Box<dyn Error>> {
    let ack = env::var(ACK_ENV).map_err(|_| invalid_input(format!("{ACK_ENV} is required")))?;
    if ack != ACK_VALUE {
        return Err(invalid_input(format!("{ACK_ENV} must equal {ACK_VALUE}")).into());
    }
    let input_path = env::var(INPUT_JSON_ENV)
        .map_err(|_| invalid_input(format!("{INPUT_JSON_ENV} is required")))?;
    let input_bytes = fs::read(input_path)?;
    Ok(serde_json::from_slice(&input_bytes)?)
}

fn require_https(label: &str, value: &str) -> Result<(), IoError> {
    if !value.starts_with("https://") {
        return Err(invalid_input(format!("{label} must be an HTTPS URL")));
    }
    Ok(())
}

fn require_nonempty(label: &str, value: &str) -> Result<(), IoError> {
    if value.trim().is_empty() {
        return Err(invalid_input(format!("{label} is empty")));
    }
    Ok(())
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

fn validate_openid(
    input: &ManagedJwksRunInput,
    openid: &OpenIdConfiguration,
) -> Result<(), IoError> {
    require_nonempty("provider", &input.provider)?;
    require_https("openid_configuration_url", &input.openid_configuration_url)?;
    require_https("jwks_uri", &input.jwks_uri)?;
    require_https("issuer", &input.issuer)?;

    if openid.issuer != input.issuer {
        return Err(invalid_input("OpenID issuer does not match input issuer"));
    }
    if openid.jwks_uri != input.jwks_uri {
        return Err(invalid_input(
            "OpenID jwks_uri does not match input jwks_uri",
        ));
    }
    if !openid
        .response_types_supported
        .iter()
        .any(|ty| ty == "id_token")
    {
        return Err(invalid_input(
            "OpenID response_types_supported must include id_token",
        ));
    }
    for claim in ["iss", "exp", "nbf"] {
        if !openid
            .claims_supported
            .iter()
            .any(|supported| supported == claim)
        {
            return Err(invalid_input(format!(
                "OpenID claims_supported must include {claim}"
            )));
        }
    }
    if openid.id_token_signing_alg_values_supported.is_empty() {
        return Err(invalid_input(
            "OpenID id_token_signing_alg_values_supported is empty",
        ));
    }
    Ok(())
}

fn validate_jwks(
    openid: &OpenIdConfiguration,
    jwks: &JwksResponse,
) -> Result<Vec<JwkDigestSummary>, IoError> {
    if jwks.keys.is_empty() {
        return Err(invalid_input("JWKS keys array is empty"));
    }

    let supported_algs = openid
        .id_token_signing_alg_values_supported
        .iter()
        .cloned()
        .collect::<BTreeSet<_>>();
    let mut seen_kids = BTreeSet::new();
    let mut summaries = Vec::with_capacity(jwks.keys.len());

    for key in &jwks.keys {
        require_nonempty("JWKS kid", &key.kid)?;
        if key.kty != "RSA" {
            return Err(invalid_input(
                "JWKS key kty must be RSA for this materializer",
            ));
        }
        let alg = key
            .alg
            .as_ref()
            .ok_or_else(|| invalid_input("JWKS key alg is missing"))?;
        if !supported_algs.contains(alg) {
            return Err(invalid_input(
                "JWKS key alg is not advertised by OpenID metadata",
            ));
        }
        if !seen_kids.insert(format!("{}:{alg}", key.kid)) {
            return Err(invalid_input("JWKS contains duplicate kid and alg"));
        }
        let n = key
            .n
            .as_ref()
            .ok_or_else(|| invalid_input("JWKS RSA modulus n is missing"))?;
        let e = key
            .e
            .as_ref()
            .ok_or_else(|| invalid_input("JWKS RSA exponent e is missing"))?;
        require_nonempty("JWKS RSA modulus n", n)?;
        require_nonempty("JWKS RSA exponent e", e)?;

        let x5c = key.x5c.as_deref().unwrap_or(&[]);
        let x5c_leaf_sha256 = x5c.first().map(|leaf| sha256_hex(leaf.as_bytes()));

        summaries.push(JwkDigestSummary {
            kid: key.kid.clone(),
            kty: key.kty.clone(),
            alg: alg.clone(),
            n_sha256: sha256_hex(n.as_bytes()),
            e_sha256: sha256_hex(e.as_bytes()),
            x5c_chain_len: x5c.len(),
            x5c_leaf_sha256,
        });
    }

    Ok(summaries)
}

fn run() -> Result<(), Box<dyn Error>> {
    let input = read_input()?;
    let openid_bytes = fs::read(&input.openid_response_path)?;
    let jwks_bytes = fs::read(&input.jwks_response_path)?;
    let openid: OpenIdConfiguration = serde_json::from_slice(&openid_bytes)?;
    let jwks: JwksResponse = serde_json::from_slice(&jwks_bytes)?;

    validate_openid(&input, &openid)?;
    let key_digests = validate_jwks(&openid, &jwks)?;

    let output_dir = input.output_root.join("managed-jwks");
    ensure_output_root(&output_dir)?;

    let supported_signing_algorithms = openid.id_token_signing_alg_values_supported;
    let response_types_supported = openid.response_types_supported;
    let claims_supported_count = openid.claims_supported.len();
    let key_count = key_digests.len();

    let summary = ManagedJwksSummary {
        schema_version: "hsai.managed-jwks-artifact.v1".to_owned(),
        operator_run_id: input.operator_run_id,
        provider: input.provider,
        issuer: input.issuer,
        verification_mode: "operator-live-jwks-fetch".to_owned(),
        openid_configuration_url: input.openid_configuration_url,
        jwks_uri: input.jwks_uri,
        openid_response_sha256: sha256_hex(&openid_bytes),
        jwks_response_sha256: sha256_hex(&jwks_bytes),
        supported_signing_algorithms,
        response_types_supported,
        claims_supported_count,
        key_count,
        key_digests,
        started_at: input.started_at,
        finished_at: input.finished_at,
        claim_boundary: "Attested".to_owned(),
        non_claims: vec![
            "not proof".to_owned(),
            "not token acceptance".to_owned(),
            "not managed-JWT signature verification".to_owned(),
            "not DCAP quote verification".to_owned(),
            "not PCCS service operation".to_owned(),
            "not TLS channel binding".to_owned(),
            "not benchmark evidence".to_owned(),
            "not accepted evidence".to_owned(),
            "not semantic correctness".to_owned(),
        ],
    };

    write_json(&output_dir.join("summary.json"), &summary)?;
    fs::write(
        output_dir.join("openid-configuration.sha256"),
        format!("{}\n", summary.openid_response_sha256),
    )?;
    fs::write(
        output_dir.join("jwks.sha256"),
        format!("{}\n", summary.jwks_response_sha256),
    )?;

    println!("operator_run_id={}", summary.operator_run_id);
    println!("provider={}", summary.provider);
    println!("issuer={}", summary.issuer);
    println!("claim_boundary={}", summary.claim_boundary);
    println!("key_count={}", summary.key_count);
    println!("openid_response_sha256={}", summary.openid_response_sha256);
    println!("jwks_response_sha256={}", summary.jwks_response_sha256);
    println!("managed_jwks_output_root={}", input.output_root.display());
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    run()
}

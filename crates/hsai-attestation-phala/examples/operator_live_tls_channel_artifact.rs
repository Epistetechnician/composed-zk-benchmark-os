#[cfg(not(feature = "operator-live-tls-channel"))]
fn main() {
    eprintln!("operator_live_tls_channel_artifact requires --features operator-live-tls-channel");
    std::process::exit(2);
}

#[cfg(feature = "operator-live-tls-channel")]
mod enabled {
    use rustls::pki_types::ServerName;
    use rustls::{ClientConfig, ClientConnection, RootCertStore, StreamOwned};
    use serde::{Deserialize, Serialize};
    use sha2::{Digest, Sha256};
    use std::collections::BTreeSet;
    use std::env;
    use std::error::Error;
    use std::fs;
    use std::io::{Error as IoError, ErrorKind, Read, Write};
    use std::net::{TcpStream, ToSocketAddrs};
    use std::path::{Component, Path, PathBuf};
    use std::sync::Arc;
    use std::time::Duration;

    const ACK_ENV: &str = "HSAI_PHALA_OPERATOR_ACK";
    const ACK_VALUE: &str = "I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN";
    const INPUT_JSON_ENV: &str = "HSAI_PHALA_TLS_CHANNEL_INPUT_JSON";
    const HOST: &str = "cloud-api.phala.com";
    const PORT: u16 = 443;
    const PATH: &str = "/api/v1/attestations/verify";
    const EXPORTER_LABEL: &[u8] = b"EXPORTER-Channel-Binding";
    const MAX_REQUEST_BYTES: usize = 64 * 1024;
    const MAX_RESPONSE_BYTES: usize = 4 * 1024 * 1024;
    const DECLARED_FILES: [&str; 5] = [
        "summary.json",
        "exporter.sha256",
        "peer-cert-chain.sha256",
        "request.sha256",
        "response.sha256",
    ];

    #[derive(Deserialize)]
    struct TlsChannelRunInput {
        operator_run_id: String,
        request_body_path: PathBuf,
        output_root: PathBuf,
        started_at: u64,
        finished_at: u64,
        timeout_seconds: u64,
        overwrite: Option<bool>,
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

    #[derive(Deserialize, Serialize)]
    struct TlsChannelSummary {
        schema_version: String,
        operator_run_id: String,
        provider: String,
        endpoint_host: String,
        endpoint_path: String,
        tls_version: String,
        cipher_suite: String,
        exporter_label: String,
        exporter_context: String,
        exporter_length: usize,
        peer_certificate_count: usize,
        http_status: u16,
        checksum: String,
        phala_success: bool,
        quote_verified: bool,
        tee_type: String,
        request_sha256: String,
        response_sha256: String,
        exporter_sha256: String,
        peer_cert_chain_sha256: String,
        started_at: u64,
        finished_at: u64,
        claim_boundary: String,
        non_claims: BTreeSet<String>,
    }

    fn invalid_input(message: impl Into<String>) -> IoError {
        IoError::new(ErrorKind::InvalidInput, message.into())
    }

    fn sha256_hex(bytes: &[u8]) -> String {
        let digest = Sha256::digest(bytes);
        let mut out = String::with_capacity(64);
        for byte in digest {
            out.push_str(&format!("{byte:02x}"));
        }
        out
    }

    fn read_input() -> Result<TlsChannelRunInput, Box<dyn Error>> {
        let ack = env::var(ACK_ENV).map_err(|_| invalid_input(format!("{ACK_ENV} is required")))?;
        if ack != ACK_VALUE {
            return Err(invalid_input(format!("{ACK_ENV} must equal {ACK_VALUE}")).into());
        }
        let input_path = env::var(INPUT_JSON_ENV)
            .map_err(|_| invalid_input(format!("{INPUT_JSON_ENV} is required")))?;
        let input: TlsChannelRunInput = serde_json::from_slice(&fs::read(input_path)?)?;
        if input.operator_run_id.trim().is_empty() {
            return Err(invalid_input("operator_run_id is empty").into());
        }
        if input.timeout_seconds == 0 || input.timeout_seconds > 120 {
            return Err(invalid_input("timeout_seconds must be in 1..=120").into());
        }
        if input.finished_at < input.started_at {
            return Err(invalid_input("finished_at precedes started_at").into());
        }
        Ok(input)
    }

    fn build_request(body: &[u8]) -> Result<Vec<u8>, IoError> {
        if body.is_empty() || body.len() > MAX_REQUEST_BYTES {
            return Err(invalid_input("request body size is outside 1..=65536"));
        }
        let value: serde_json::Value =
            serde_json::from_slice(body).map_err(|_| invalid_input("request body is not JSON"))?;
        let quote = value
            .as_object()
            .and_then(|object| object.get("hex"))
            .and_then(serde_json::Value::as_str)
            .ok_or_else(|| invalid_input("request body must contain string field hex"))?;
        if quote.is_empty() || !quote.bytes().all(|byte| byte.is_ascii_hexdigit()) {
            return Err(invalid_input("request hex field is empty or non-hex"));
        }

        let head = format!(
            "POST {PATH} HTTP/1.1\r\nHost: {HOST}\r\nContent-Type: application/json\r\nAccept: application/json\r\nContent-Length: {}\r\nConnection: close\r\nUser-Agent: hsai-phala-tls-channel/1\r\n\r\n",
            body.len()
        );
        let mut request = head.into_bytes();
        request.extend_from_slice(body);
        Ok(request)
    }

    fn decode_chunked(mut input: &[u8]) -> Result<Vec<u8>, IoError> {
        let mut output = Vec::new();
        loop {
            let line_end = input
                .windows(2)
                .position(|window| window == b"\r\n")
                .ok_or_else(|| invalid_input("malformed chunk size"))?;
            let size_text = std::str::from_utf8(&input[..line_end])
                .map_err(|_| invalid_input("chunk size is not UTF-8"))?;
            let size = usize::from_str_radix(size_text.split(';').next().unwrap_or(""), 16)
                .map_err(|_| invalid_input("invalid chunk size"))?;
            input = &input[line_end + 2..];
            if size == 0 {
                return Ok(output);
            }
            if input.len() < size + 2 || &input[size..size + 2] != b"\r\n" {
                return Err(invalid_input("truncated chunked body"));
            }
            output.extend_from_slice(&input[..size]);
            if output.len() > MAX_RESPONSE_BYTES {
                return Err(invalid_input("decoded response exceeds size limit"));
            }
            input = &input[size + 2..];
        }
    }

    fn parse_http_response(bytes: &[u8]) -> Result<(u16, Vec<u8>), IoError> {
        let head_end = bytes
            .windows(4)
            .position(|window| window == b"\r\n\r\n")
            .ok_or_else(|| invalid_input("HTTP response has no header terminator"))?;
        let head = std::str::from_utf8(&bytes[..head_end])
            .map_err(|_| invalid_input("HTTP response headers are not UTF-8"))?;
        let mut lines = head.split("\r\n");
        let status_line = lines
            .next()
            .ok_or_else(|| invalid_input("HTTP response has no status line"))?;
        let mut status_parts = status_line.split_whitespace();
        if status_parts.next() != Some("HTTP/1.1") {
            return Err(invalid_input("HTTP response is not HTTP/1.1"));
        }
        let status = status_parts
            .next()
            .ok_or_else(|| invalid_input("HTTP response has no status code"))?
            .parse::<u16>()
            .map_err(|_| invalid_input("HTTP status code is invalid"))?;
        let mut chunked = false;
        let mut content_length = None;
        for line in lines {
            let (name, value) = line
                .split_once(':')
                .ok_or_else(|| invalid_input("malformed HTTP response header"))?;
            if name.eq_ignore_ascii_case("transfer-encoding")
                && value.trim().eq_ignore_ascii_case("chunked")
            {
                chunked = true;
            }
            if name.eq_ignore_ascii_case("content-length") {
                content_length = Some(
                    value
                        .trim()
                        .parse::<usize>()
                        .map_err(|_| invalid_input("invalid Content-Length"))?,
                );
            }
        }
        let body = &bytes[head_end + 4..];
        if chunked {
            return Ok((status, decode_chunked(body)?));
        }
        if let Some(expected) = content_length {
            if expected != body.len() {
                return Err(invalid_input("Content-Length does not match response body"));
            }
        }
        Ok((status, body.to_vec()))
    }

    fn fetch(body: &[u8], timeout_seconds: u64) -> Result<TlsCapture, Box<dyn Error>> {
        let provider = rustls::crypto::ring::default_provider();
        let roots = RootCertStore::from_iter(webpki_roots::TLS_SERVER_ROOTS.iter().cloned());
        let mut config = ClientConfig::builder_with_provider(Arc::new(provider))
            .with_protocol_versions(&[&rustls::version::TLS13])?
            .with_root_certificates(roots)
            .with_no_client_auth();
        config.alpn_protocols = vec![b"http/1.1".to_vec()];

        let server_name = ServerName::try_from(HOST.to_owned())?;
        let connection = ClientConnection::new(Arc::new(config), server_name)?;
        let address = (HOST, PORT)
            .to_socket_addrs()?
            .next()
            .ok_or_else(|| invalid_input("Phala endpoint did not resolve"))?;
        let tcp = TcpStream::connect_timeout(&address, Duration::from_secs(timeout_seconds))?;
        tcp.set_read_timeout(Some(Duration::from_secs(timeout_seconds)))?;
        tcp.set_write_timeout(Some(Duration::from_secs(timeout_seconds)))?;
        let mut tls = StreamOwned::new(connection, tcp);
        let request = build_request(body)?;
        tls.write_all(&request)?;
        tls.flush()?;

        let mut wire_response = Vec::new();
        let mut buffer = [0_u8; 8192];
        loop {
            let read = tls.read(&mut buffer)?;
            if read == 0 {
                break;
            }
            wire_response.extend_from_slice(&buffer[..read]);
            if wire_response.len() > MAX_RESPONSE_BYTES {
                return Err(invalid_input("HTTP response exceeds size limit").into());
            }
        }
        let (status, response_body) = parse_http_response(&wire_response)?;

        let version = tls
            .conn
            .protocol_version()
            .ok_or_else(|| invalid_input("TLS version is unavailable"))?;
        if version != rustls::ProtocolVersion::TLSv1_3 {
            return Err(invalid_input("TLS 1.3 was not negotiated").into());
        }
        let cipher_suite = tls
            .conn
            .negotiated_cipher_suite()
            .ok_or_else(|| invalid_input("TLS cipher suite is unavailable"))?
            .suite();
        let peer_certificates = tls
            .conn
            .peer_certificates()
            .ok_or_else(|| invalid_input("peer certificate chain is unavailable"))?;
        let mut cert_chain = Vec::new();
        for cert in peer_certificates {
            cert_chain.extend_from_slice(&(cert.as_ref().len() as u64).to_be_bytes());
            cert_chain.extend_from_slice(cert.as_ref());
        }
        let mut exporter = [0_u8; 32];
        tls.conn
            .export_keying_material(&mut exporter, EXPORTER_LABEL, Some(&[]))?;

        Ok(TlsCapture {
            status,
            response_body,
            tls_version: format!("{version:?}"),
            cipher_suite: format!("{cipher_suite:?}"),
            exporter,
            peer_cert_chain: cert_chain,
            peer_certificate_count: peer_certificates.len(),
        })
    }

    struct TlsCapture {
        status: u16,
        response_body: Vec<u8>,
        tls_version: String,
        cipher_suite: String,
        exporter: [u8; 32],
        peer_cert_chain: Vec<u8>,
        peer_certificate_count: usize,
    }

    fn validate_output_root(path: &Path) -> Result<(), IoError> {
        if path.as_os_str().is_empty() || !path.is_absolute() {
            return Err(invalid_input("output_root must be an absolute path"));
        }
        if path
            .components()
            .any(|component| matches!(component, Component::ParentDir))
        {
            return Err(invalid_input(
                "output_root must not contain parent traversal",
            ));
        }
        let repo_root = Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../..")
            .canonicalize()?;
        let existing = path
            .ancestors()
            .find(|candidate| candidate.exists())
            .ok_or_else(|| invalid_input("output_root has no existing ancestor"))?;
        if existing
            .symlink_metadata()
            .is_ok_and(|metadata| metadata.file_type().is_symlink())
        {
            return Err(invalid_input("output_root contains a symlink"));
        }
        let resolved_existing = existing.canonicalize()?;
        if resolved_existing.starts_with(&repo_root) || repo_root.starts_with(&resolved_existing) {
            return Err(invalid_input("output_root overlaps the repository"));
        }
        for ancestor in path
            .ancestors()
            .take_while(|candidate| *candidate != existing)
        {
            if ancestor
                .symlink_metadata()
                .is_ok_and(|metadata| metadata.file_type().is_symlink())
            {
                return Err(invalid_input("output_root contains a symlink"));
            }
        }
        Ok(())
    }

    fn materialize(
        input: &TlsChannelRunInput,
        summary: &TlsChannelSummary,
    ) -> Result<PathBuf, Box<dyn Error>> {
        validate_output_root(&input.output_root)?;
        let output_dir = input.output_root.join("tls-channel");
        if output_dir.exists() {
            if output_dir.symlink_metadata()?.file_type().is_symlink() {
                return Err(invalid_input("existing tls-channel root is a symlink").into());
            }
            if input.overwrite != Some(true) {
                return Err(
                    invalid_input("tls-channel output exists; overwrite is not true").into(),
                );
            }
            let mut actual = fs::read_dir(&output_dir)?
                .map(|entry| entry.map(|entry| entry.file_name().to_string_lossy().into_owned()))
                .collect::<Result<BTreeSet<_>, _>>()?;
            let expected = DECLARED_FILES
                .iter()
                .map(|name| (*name).to_owned())
                .collect();
            if actual != expected {
                actual.clear();
                return Err(
                    invalid_input("existing tls-channel root is partial or undeclared").into(),
                );
            }
            for name in DECLARED_FILES {
                let file = output_dir.join(name);
                if file.symlink_metadata()?.file_type().is_symlink() {
                    return Err(invalid_input("existing tls-channel file is a symlink").into());
                }
            }
            let existing_summary: TlsChannelSummary =
                serde_json::from_slice(&fs::read(output_dir.join("summary.json"))?)?;
            for (name, expected_digest) in [
                ("exporter.sha256", &existing_summary.exporter_sha256),
                (
                    "peer-cert-chain.sha256",
                    &existing_summary.peer_cert_chain_sha256,
                ),
                ("request.sha256", &existing_summary.request_sha256),
                ("response.sha256", &existing_summary.response_sha256),
            ] {
                let actual = fs::read_to_string(output_dir.join(name))?;
                if actual.trim() != expected_digest {
                    return Err(invalid_input(format!(
                        "existing tls-channel digest is stale: {name}"
                    ))
                    .into());
                }
            }
        }

        let staging = input
            .output_root
            .join(format!(".tls-channel-stage-{}", std::process::id()));
        if staging.exists() {
            return Err(invalid_input("TLS channel staging path already exists").into());
        }
        fs::create_dir_all(&staging)?;
        let write_result = (|| -> Result<(), Box<dyn Error>> {
            fs::write(
                staging.join("summary.json"),
                serde_json::to_vec_pretty(summary)?,
            )?;
            fs::write(
                staging.join("exporter.sha256"),
                format!("{}\n", summary.exporter_sha256),
            )?;
            fs::write(
                staging.join("peer-cert-chain.sha256"),
                format!("{}\n", summary.peer_cert_chain_sha256),
            )?;
            fs::write(
                staging.join("request.sha256"),
                format!("{}\n", summary.request_sha256),
            )?;
            fs::write(
                staging.join("response.sha256"),
                format!("{}\n", summary.response_sha256),
            )?;
            Ok(())
        })();
        if let Err(error) = write_result {
            let _ = fs::remove_dir_all(&staging);
            return Err(error);
        }
        if output_dir.exists() {
            fs::remove_dir_all(&output_dir)?;
        }
        fs::rename(&staging, &output_dir)?;
        Ok(output_dir)
    }

    fn run() -> Result<(), Box<dyn Error>> {
        let input = read_input()?;
        let request_body = fs::read(&input.request_body_path)?;
        let capture = fetch(&request_body, input.timeout_seconds)?;
        if capture.status != 200 {
            return Err(invalid_input(format!("Phala returned HTTP {}", capture.status)).into());
        }
        let response: PhalaVerifyResponse = serde_json::from_slice(&capture.response_body)?;
        if !response.success
            || !response.quote.verified
            || response.quote.header.tee_type != "TEE_TDX"
        {
            return Err(invalid_input("Phala response is not an accepted TEE_TDX quote").into());
        }

        let summary = TlsChannelSummary {
            schema_version: "hsai.phala.tls-channel-artifact.v1".to_owned(),
            operator_run_id: input.operator_run_id.clone(),
            provider: "phala-dstack".to_owned(),
            endpoint_host: HOST.to_owned(),
            endpoint_path: PATH.to_owned(),
            tls_version: capture.tls_version,
            cipher_suite: capture.cipher_suite,
            exporter_label: String::from_utf8(EXPORTER_LABEL.to_vec())?,
            exporter_context: "empty".to_owned(),
            exporter_length: capture.exporter.len(),
            peer_certificate_count: capture.peer_certificate_count,
            http_status: capture.status,
            checksum: response.checksum,
            phala_success: response.success,
            quote_verified: response.quote.verified,
            tee_type: response.quote.header.tee_type,
            request_sha256: sha256_hex(&request_body),
            response_sha256: sha256_hex(&capture.response_body),
            exporter_sha256: sha256_hex(&capture.exporter),
            peer_cert_chain_sha256: sha256_hex(&capture.peer_cert_chain),
            started_at: input.started_at,
            finished_at: input.finished_at,
            claim_boundary: "Attested".to_owned(),
            non_claims: BTreeSet::from([
                "not proof".to_owned(),
                "not RA-TLS or an attested server certificate".to_owned(),
                "not independent third-party evidence".to_owned(),
                "not local DCAP verification".to_owned(),
                "not managed-service signature/JWKS/JWT verification".to_owned(),
                "not benchmark evidence or official benchmark evidence".to_owned(),
                "not accepted Evidence Ledger state".to_owned(),
                "not global software-agent uniqueness".to_owned(),
                "not semantic correctness".to_owned(),
            ]),
        };
        let output_dir = materialize(&input, &summary)?;
        println!("operator_run_id={}", summary.operator_run_id);
        println!("checksum={}", summary.checksum);
        println!("tls_version={}", summary.tls_version);
        println!("cipher_suite={}", summary.cipher_suite);
        println!("exporter_sha256={}", summary.exporter_sha256);
        println!("claim_boundary={}", summary.claim_boundary);
        println!("tls_channel_output_root={}", output_dir.display());
        Ok(())
    }

    pub fn main() -> Result<(), Box<dyn Error>> {
        run()
    }

    #[cfg(test)]
    mod tests {
        use super::*;

        #[test]
        fn request_is_pinned_and_validated() {
            let request = build_request(br#"{"hex":"aabb"}"#).expect("valid request");
            let request = String::from_utf8(request).expect("request utf8");
            assert!(request.starts_with(&format!("POST {PATH} HTTP/1.1\r\n")));
            assert!(request.contains(&format!("Host: {HOST}\r\n")));
            assert!(request.contains("Connection: close\r\n"));
            assert!(build_request(br#"{"hex":"not-hex"}"#).is_err());
            assert!(build_request(br#"{"quote":"aabb"}"#).is_err());
        }

        #[test]
        fn parses_content_length_response() {
            let response = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n{}";
            let (status, body) = parse_http_response(response).expect("valid response");
            assert_eq!(status, 200);
            assert_eq!(body, b"{}");

            let truncated = b"HTTP/1.1 200 OK\r\nContent-Length: 3\r\n\r\n{}";
            assert!(parse_http_response(truncated).is_err());
        }

        #[test]
        fn parses_chunked_response() {
            let response =
                b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n2\r\n{}\r\n0\r\n\r\n";
            let (status, body) = parse_http_response(response).expect("valid chunked response");
            assert_eq!(status, 200);
            assert_eq!(body, b"{}");
            assert!(decode_chunked(b"x\r\n").is_err());
        }

        #[test]
        fn repository_output_root_is_rejected() {
            let repo_root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
            assert!(validate_output_root(&repo_root).is_err());
        }
    }
}

#[cfg(feature = "operator-live-tls-channel")]
fn main() -> Result<(), Box<dyn std::error::Error>> {
    enabled::main()
}

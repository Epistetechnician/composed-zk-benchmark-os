use std::fs;
use std::path::Path;

fn source() -> String {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("examples/operator_live_tls_channel_artifact.rs");
    fs::read_to_string(path).expect("TLS channel example source must be readable")
}

#[test]
fn tls_channel_example_is_operator_only_and_protocol_pinned() {
    let source = source();
    for required in [
        "HSAI_PHALA_OPERATOR_ACK",
        "I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN",
        "HSAI_PHALA_TLS_CHANNEL_INPUT_JSON",
        "cloud-api.phala.com",
        "/api/v1/attestations/verify",
        "TLS13",
        "TLSv1_3",
        "EXPORTER-Channel-Binding",
        "Some(&[])",
        "http/1.1",
        "Connection: close",
        "webpki_roots::TLS_SERVER_ROOTS",
        "export_keying_material",
    ] {
        assert!(
            source.contains(required),
            "missing protocol contract: {required}"
        );
    }
    for forbidden in [
        "dangerous()",
        "with_custom_certificate_verifier",
        "http://cloud-api.phala.com",
        "Authorization: Bearer",
        "reqwest::",
        "ureq::",
        "Command::new",
    ] {
        assert!(
            !source.contains(forbidden),
            "forbidden transport surface: {forbidden}"
        );
    }
}

#[test]
fn tls_channel_example_materializes_only_digest_bound_files() {
    let source = source();
    for file in [
        "summary.json",
        "exporter.sha256",
        "peer-cert-chain.sha256",
        "request.sha256",
        "response.sha256",
    ] {
        assert!(
            source.contains(file),
            "missing declared artifact file: {file}"
        );
    }
    for forbidden in [
        "exporter.bin",
        "request.json",
        "response.json",
        "peer-cert.der",
        "credential",
        "api_key",
        "bearer_token",
    ] {
        assert!(
            !source.contains(forbidden),
            "raw or secret output surface: {forbidden}"
        );
    }
    for required in [
        "output_root must be an absolute path",
        "output_root overlaps the repository",
        "output_root contains a symlink",
        "overwrite is not true",
        "partial or undeclared",
        ".tls-channel-stage-",
    ] {
        assert!(
            source.contains(required),
            "missing output safety rule: {required}"
        );
    }
}

#[test]
fn tls_channel_example_preserves_claim_limits() {
    let source = source();
    for required in [
        "Attested",
        "not proof",
        "not RA-TLS or an attested server certificate",
        "not independent third-party evidence",
        "not local DCAP verification",
        "not managed-service signature/JWKS/JWT verification",
        "not benchmark evidence or official benchmark evidence",
        "not accepted Evidence Ledger state",
        "not global software-agent uniqueness",
        "not semantic correctness",
    ] {
        assert!(
            source.contains(required),
            "missing claim boundary: {required}"
        );
    }
    assert!(!source.contains("Proven"));
}

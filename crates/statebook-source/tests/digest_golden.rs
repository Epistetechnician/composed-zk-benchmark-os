use ring::digest::{digest as ring_digest, SHA256};
use statebook_source::{
    captured_artifact_digest, digest_to_hex, import_receipt_digest, provenance_set_digest,
    registration_digest, CAPTURED_ARTIFACT_DOMAIN, IMPORT_RECEIPT_DOMAIN, PROVENANCE_SET_DOMAIN,
    SOURCE_REGISTRATION_DOMAIN,
};

fn ring_domain_digest(domain: &[u8], payload: &[u8]) -> String {
    let mut input = Vec::with_capacity(domain.len() + payload.len() + 2);
    input.extend_from_slice(domain);
    input.extend_from_slice(&1_u16.to_be_bytes());
    input.extend_from_slice(payload);
    hex::encode(ring_digest(&SHA256, &input).as_ref())
}

#[test]
fn independent_ring_digests_reproduce_golden_vectors() {
    let registration = registration_digest(
        "synthetic.clearing.v1",
        "BTC-USD-2026",
        "rev-1",
        "b2e2c19561b98a9240fc638c27c75a5f76ebfcc93f24f10cc903548d867928f3",
        "captured_replay",
        "active",
    );
    assert_eq!(
        digest_to_hex(registration),
        ring_domain_digest(
            SOURCE_REGISTRATION_DOMAIN,
            &tlv_fields(&[
                (1, b"synthetic.clearing.v1".as_slice()),
                (2, b"BTC-USD-2026"),
                (3, b"rev-1"),
                (
                    4,
                    b"b2e2c19561b98a9240fc638c27c75a5f76ebfcc93f24f10cc903548d867928f3"
                ),
                (5, b"captured_replay"),
                (6, b"active"),
            ])
        )
    );

    let artifact = captured_artifact_digest(
        "synthetic-clearing-terms-v1",
        "synthetic.clearing.v1",
        "b2e2c19561b98a9240fc638c27c75a5f76ebfcc93f24f10cc903548d867928f3",
        br#"{"schema_version":"statebook-p6-captured-artifact:v1"}"#,
    );
    assert_eq!(
        digest_to_hex(artifact),
        ring_domain_digest(
            CAPTURED_ARTIFACT_DOMAIN,
            &tlv_fields(&[
                (1, b"synthetic-clearing-terms-v1".as_slice()),
                (2, b"synthetic.clearing.v1"),
                (
                    3,
                    b"b2e2c19561b98a9240fc638c27c75a5f76ebfcc93f24f10cc903548d867928f3"
                ),
                (
                    4,
                    br#"{"schema_version":"statebook-p6-captured-artifact:v1"}"#
                ),
            ])
        )
    );

    let receipt = import_receipt_digest(
        "synthetic-clearing-terms-v1",
        "synthetic.clearing.v1",
        "BTC-USD-2026",
        "rev-1",
        "b2e2c19561b98a9240fc638c27c75a5f76ebfcc93f24f10cc903548d867928f3",
        &digest_to_hex(artifact),
        &digest_to_hex(registration),
    );
    assert_eq!(
        digest_to_hex(receipt),
        ring_domain_digest(
            IMPORT_RECEIPT_DOMAIN,
            &tlv_fields(&[
                (1, b"synthetic-clearing-terms-v1".as_slice()),
                (2, b"synthetic.clearing.v1"),
                (3, b"BTC-USD-2026"),
                (4, b"rev-1"),
                (
                    5,
                    b"b2e2c19561b98a9240fc638c27c75a5f76ebfcc93f24f10cc903548d867928f3"
                ),
                (6, digest_to_hex(artifact).as_bytes()),
                (7, digest_to_hex(registration).as_bytes()),
            ])
        )
    );

    let provenance = provenance_set_digest(
        &["terms-normalization-input".to_owned()],
        &["synthetic-non-authoritative".to_owned()],
    );
    assert_eq!(
        digest_to_hex(provenance),
        ring_domain_digest(
            PROVENANCE_SET_DOMAIN,
            &tlv_fields(&[
                (
                    1,
                    encode_sequence(&[b"terms-normalization-input".to_vec()]).as_slice()
                ),
                (
                    2,
                    encode_sequence(&[b"synthetic-non-authoritative".to_vec()]).as_slice()
                ),
            ])
        )
    );
}

fn tlv_fields(fields: &[(u16, &[u8])]) -> Vec<u8> {
    let mut out = Vec::new();
    for (tag, value) in fields {
        out.extend_from_slice(&tag.to_be_bytes());
        out.extend_from_slice(&(value.len() as u32).to_be_bytes());
        out.extend_from_slice(value);
    }
    out
}

fn encode_sequence(values: &[Vec<u8>]) -> Vec<u8> {
    let mut out = Vec::new();
    out.extend_from_slice(&(values.len() as u32).to_be_bytes());
    for value in values {
        out.extend_from_slice(&(value.len() as u32).to_be_bytes());
        out.extend_from_slice(value);
    }
    out
}

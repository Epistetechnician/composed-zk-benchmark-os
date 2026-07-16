use ring::digest::{digest as ring_digest, SHA256};
use statebook_authority::{
    attach_receipt_digest, authority_statement_digest, capital_overlay_digest, digest_to_hex,
    registration_digest, ATTACH_RECEIPT_DOMAIN, AUTHORITY_REGISTRATION_DOMAIN,
    AUTHORITY_STATEMENT_DOMAIN, CAPITAL_OVERLAY_DOMAIN,
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
    let statement = authority_statement_digest(
        "synthetic-clearing-authority-v1",
        "synthetic.clearing.authority.v1",
        "synthetic-clearing-officer-v1",
        "rev-1",
        "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "1",
        "1",
        1000,
        2000,
    );
    assert_eq!(
        digest_to_hex(statement),
        ring_domain_digest(
            AUTHORITY_STATEMENT_DOMAIN,
            &tlv_fields(&[
                (1, b"synthetic-clearing-authority-v1".as_slice()),
                (2, b"synthetic.clearing.authority.v1"),
                (3, b"synthetic-clearing-officer-v1"),
                (4, b"rev-1"),
                (
                    5,
                    b"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
                ),
                (
                    6,
                    b"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
                ),
                (7, b"1"),
                (8, b"1"),
                (9, &1000_i64.to_be_bytes()),
                (10, &2000_i64.to_be_bytes()),
                (11, &[0_u8]),
            ])
        )
    );

    let registration = registration_digest(
        "synthetic.clearing.authority.v1",
        "synthetic-clearing-officer-v1",
        "rev-1",
        &digest_to_hex(statement),
        "active",
    );
    assert_eq!(
        digest_to_hex(registration),
        ring_domain_digest(
            AUTHORITY_REGISTRATION_DOMAIN,
            &tlv_fields(&[
                (1, b"synthetic.clearing.authority.v1".as_slice()),
                (2, b"synthetic-clearing-officer-v1"),
                (3, b"rev-1"),
                (4, digest_to_hex(statement).as_bytes()),
                (5, b"active"),
            ])
        )
    );

    let overlay = capital_overlay_digest(
        "recognized_in_fixture",
        "synthetic-clearing-officer-v1",
        "acct-fixture-001",
        "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "1",
        "1",
        1500,
    );
    assert_eq!(
        digest_to_hex(overlay),
        ring_domain_digest(
            CAPITAL_OVERLAY_DOMAIN,
            &tlv_fields(&[
                (1, b"recognized_in_fixture".as_slice()),
                (2, b"synthetic-clearing-officer-v1"),
                (3, b"acct-fixture-001"),
                (
                    4,
                    b"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
                ),
                (
                    5,
                    b"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
                ),
                (6, b"1"),
                (7, b"1"),
                (8, &1500_i64.to_be_bytes()),
            ])
        )
    );

    let receipt = attach_receipt_digest(
        "synthetic-clearing-authority-v1",
        "synthetic.clearing.authority.v1",
        "synthetic-clearing-officer-v1",
        "rev-1",
        &digest_to_hex(statement),
        &digest_to_hex(registration),
        &digest_to_hex(overlay),
        "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    );
    assert_eq!(
        digest_to_hex(receipt),
        ring_domain_digest(
            ATTACH_RECEIPT_DOMAIN,
            &tlv_fields(&[
                (1, b"synthetic-clearing-authority-v1".as_slice()),
                (2, b"synthetic.clearing.authority.v1"),
                (3, b"synthetic-clearing-officer-v1"),
                (4, b"rev-1"),
                (5, digest_to_hex(statement).as_bytes()),
                (6, digest_to_hex(registration).as_bytes()),
                (7, digest_to_hex(overlay).as_bytes()),
                (
                    8,
                    b"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
                ),
                (9, &[0_u8]),
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

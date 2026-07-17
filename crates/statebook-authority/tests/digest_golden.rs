use ring::digest::{digest as ring_digest, SHA256};
use statebook_authority::{
    authority_package_digest, digest_to_hex, loss_bound_digest, nonclaim_set_digest,
    preflight_receipt_digest, AUTHORITY_PACKAGE_DOMAIN, LOSS_BOUND_DOMAIN, NONCLAIM_SET_DOMAIN,
    PREFLIGHT_RECEIPT_DOMAIN,
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
    let loss = loss_bound_digest("0", "1");
    assert_eq!(
        digest_to_hex(loss),
        ring_domain_digest(LOSS_BOUND_DOMAIN, &tlv_fields(&[(1, b"0"), (2, b"1")]))
    );

    let package = authority_package_digest(
        "hermetic-authority-preflight-v1",
        "synthetic-ops-owner",
        &digest_to_hex(loss),
        "reject_and_journal",
        "scoped_halt",
        "days_90",
        "synthetic.legal.v1",
        "denied",
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    );
    assert_eq!(
        digest_to_hex(package),
        ring_domain_digest(
            AUTHORITY_PACKAGE_DOMAIN,
            &tlv_fields(&[
                (1, b"hermetic-authority-preflight-v1"),
                (2, b"synthetic-ops-owner"),
                (3, digest_to_hex(loss).as_bytes()),
                (4, b"reject_and_journal"),
                (5, b"scoped_halt"),
                (6, b"days_90"),
                (7, b"synthetic.legal.v1"),
                (8, b"denied"),
                (
                    9,
                    b"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
                ),
            ])
        )
    );

    let nonclaims = nonclaim_set_digest(&["no_controller_invoked".to_owned()]);
    assert_eq!(
        digest_to_hex(nonclaims),
        ring_domain_digest(
            NONCLAIM_SET_DOMAIN,
            &tlv_fields(&[(
                1,
                encode_sequence(&[b"no_controller_invoked".to_vec()]).as_slice()
            )])
        )
    );

    let receipt = preflight_receipt_digest(
        "hermetic-authority-preflight-v1",
        "denied",
        &digest_to_hex(package),
        &digest_to_hex(loss),
        &digest_to_hex(nonclaims),
    );
    assert_eq!(
        digest_to_hex(receipt),
        ring_domain_digest(
            PREFLIGHT_RECEIPT_DOMAIN,
            &tlv_fields(&[
                (1, b"hermetic-authority-preflight-v1"),
                (2, b"denied"),
                (3, digest_to_hex(package).as_bytes()),
                (4, digest_to_hex(loss).as_bytes()),
                (5, digest_to_hex(nonclaims).as_bytes()),
                (6, b"false"),
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

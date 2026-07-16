use ring::digest::{digest as ring_digest, SHA256};
use statebook_report::{
    audit_trace_digest, digest_to_hex, manifest_digest, member_digest, nonclaim_set_digest,
    AUDIT_TRACE_DOMAIN, BUNDLE_MANIFEST_DOMAIN, BUNDLE_MEMBER_DOMAIN, NONCLAIM_SET_DOMAIN,
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
    let member = member_digest("records/decision.json", br#"{"schema_version":1}"#);
    assert_eq!(
        digest_to_hex(member),
        ring_domain_digest(
            BUNDLE_MEMBER_DOMAIN,
            &member_payload("records/decision.json", br#"{"schema_version":1}"#)
        )
    );

    let members = vec![("records/decision.json".to_owned(), member)];
    let manifest = manifest_digest("golden-bundle-v1", &members);
    assert_eq!(
        digest_to_hex(manifest),
        ring_domain_digest(
            BUNDLE_MANIFEST_DOMAIN,
            &manifest_payload("golden-bundle-v1", &members)
        )
    );

    let nonclaims = nonclaim_set_digest(&["no_authority".to_owned()]);
    assert_eq!(
        digest_to_hex(nonclaims),
        ring_domain_digest(
            NONCLAIM_SET_DOMAIN,
            &nonclaim_payload(&["no_authority".to_owned()])
        )
    );

    let trace = audit_trace_digest(
        "trace-golden-bundle-v1",
        "7634410968adb9b56c62f213de7956796f9f3f62b102d4f6efe7f45d86858788",
        "f1662f3fb5a10c074680c0baf76ba488b7230337456358be92f3127d8a632c08",
        "67cb8e1807cd3e619f73d569f70de494ef60610f4d44acea236b0ee006e45e6a",
        "fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321",
        "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        &members,
    );
    assert_eq!(
        digest_to_hex(trace),
        ring_domain_digest(
            AUDIT_TRACE_DOMAIN,
            &trace_payload(
                "trace-golden-bundle-v1",
                "7634410968adb9b56c62f213de7956796f9f3f62b102d4f6efe7f45d86858788",
                "f1662f3fb5a10c074680c0baf76ba488b7230337456358be92f3127d8a632c08",
                "67cb8e1807cd3e619f73d569f70de494ef60610f4d44acea236b0ee006e45e6a",
                "fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321",
                "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                &members,
            )
        )
    );
}

fn member_payload(path: &str, content: &[u8]) -> Vec<u8> {
    tlv_field(1, path.as_bytes(), tlv_field(2, content, Vec::new()))
}

fn manifest_payload(bundle_id: &str, members: &[(String, [u8; 32])]) -> Vec<u8> {
    let mut member_items = Vec::new();
    for (path, digest) in members {
        member_items.push(tlv_field(
            1,
            path.as_bytes(),
            tlv_field(2, digest, Vec::new()),
        ));
    }
    tlv_field(
        1,
        bundle_id.as_bytes(),
        tlv_field(2, &encode_sequence(&member_items), Vec::new()),
    )
}

fn nonclaim_payload(nonclaims: &[String]) -> Vec<u8> {
    let items: Vec<Vec<u8>> = nonclaims
        .iter()
        .map(|value| value.as_bytes().to_vec())
        .collect();
    tlv_field(1, &encode_sequence(&items), Vec::new())
}

#[allow(clippy::too_many_arguments)]
fn trace_payload(
    trace_id: &str,
    terms: &str,
    state_key: &str,
    residual: &str,
    composition: &str,
    decision_context: &str,
    decision_record: &str,
    members: &[(String, [u8; 32])],
) -> Vec<u8> {
    let mut member_items = Vec::new();
    for (path, digest) in members {
        member_items.push(tlv_field(
            1,
            path.as_bytes(),
            tlv_field(2, digest, Vec::new()),
        ));
    }
    let mut out = Vec::new();
    out.extend(tlv_field(1, trace_id.as_bytes(), Vec::new()));
    out.extend(tlv_field(2, terms.as_bytes(), Vec::new()));
    out.extend(tlv_field(3, state_key.as_bytes(), Vec::new()));
    out.extend(tlv_field(4, residual.as_bytes(), Vec::new()));
    out.extend(tlv_field(5, composition.as_bytes(), Vec::new()));
    out.extend(tlv_field(6, decision_context.as_bytes(), Vec::new()));
    out.extend(tlv_field(7, decision_record.as_bytes(), Vec::new()));
    out.extend(tlv_field(8, &encode_sequence(&member_items), Vec::new()));
    out
}

fn tlv_field(tag: u16, value: &[u8], tail: Vec<u8>) -> Vec<u8> {
    let mut out = Vec::new();
    out.extend_from_slice(&tag.to_be_bytes());
    out.extend_from_slice(&(value.len() as u32).to_be_bytes());
    out.extend_from_slice(value);
    out.extend_from_slice(&tail);
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

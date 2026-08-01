#![allow(dead_code)]

use sha2::{Digest as _, Sha256};

pub const BUNDLE_MANIFEST_DOMAIN: &[u8] = b"statebook:p5-bundle-manifest:v1\0";
pub const BUNDLE_MEMBER_DOMAIN: &[u8] = b"statebook:p5-bundle-member:v1\0";
pub const AUDIT_TRACE_DOMAIN: &[u8] = b"statebook:p5-audit-trace:v1\0";
pub const NONCLAIM_SET_DOMAIN: &[u8] = b"statebook:p5-nonclaim-set:v1\0";

pub fn digest(domain: &[u8], payload: &[u8]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(domain);
    hasher.update(1_u16.to_be_bytes());
    hasher.update(payload);
    hasher.finalize().into()
}

pub struct Canonical {
    bytes: Vec<u8>,
}

impl Canonical {
    pub fn new() -> Self {
        Self { bytes: Vec::new() }
    }

    pub fn field(&mut self, tag: u16, value: &[u8]) {
        self.bytes.extend_from_slice(&tag.to_be_bytes());
        self.bytes.extend_from_slice(
            &u32::try_from(value.len())
                .expect("bounded canonical field")
                .to_be_bytes(),
        );
        self.bytes.extend_from_slice(value);
    }

    pub fn finish(self) -> Vec<u8> {
        self.bytes
    }
}

pub fn encode_sequence<I>(values: I) -> Vec<u8>
where
    I: IntoIterator<Item = Vec<u8>>,
{
    let values: Vec<Vec<u8>> = values.into_iter().collect();
    let mut out = Vec::new();
    out.extend_from_slice(
        &u32::try_from(values.len())
            .expect("bounded canonical sequence")
            .to_be_bytes(),
    );
    for value in values {
        out.extend_from_slice(
            &u32::try_from(value.len())
                .expect("bounded canonical item")
                .to_be_bytes(),
        );
        out.extend_from_slice(&value);
    }
    out
}

pub fn encode_string(value: &str) -> Vec<u8> {
    value.as_bytes().to_vec()
}

pub fn encode_digest_hex(value: &str) -> Vec<u8> {
    value.as_bytes().to_vec()
}

pub fn member_digest(path: &str, content: &[u8]) -> [u8; 32] {
    let mut encoder = Canonical::new();
    encoder.field(1, path.as_bytes());
    encoder.field(2, content);
    digest(BUNDLE_MEMBER_DOMAIN, &encoder.finish())
}

pub fn manifest_digest(bundle_id: &str, members: &[(String, [u8; 32])]) -> [u8; 32] {
    let mut encoder = Canonical::new();
    encoder.field(1, bundle_id.as_bytes());
    encoder.field(
        2,
        &encode_sequence(members.iter().map(|(path, digest)| {
            let mut item = Canonical::new();
            item.field(1, path.as_bytes());
            item.field(2, digest);
            item.finish()
        })),
    );
    digest(BUNDLE_MANIFEST_DOMAIN, &encoder.finish())
}

#[allow(clippy::too_many_arguments)]
pub fn audit_trace_digest(
    trace_id: &str,
    terms_digest: &str,
    state_key_digest: &str,
    residual_digest: &str,
    composition_digest: &str,
    decision_context_digest: &str,
    decision_record_digest: &str,
    member_digests: &[(String, [u8; 32])],
) -> [u8; 32] {
    let mut encoder = Canonical::new();
    encoder.field(1, trace_id.as_bytes());
    encoder.field(2, terms_digest.as_bytes());
    encoder.field(3, state_key_digest.as_bytes());
    encoder.field(4, residual_digest.as_bytes());
    encoder.field(5, composition_digest.as_bytes());
    encoder.field(6, decision_context_digest.as_bytes());
    encoder.field(7, decision_record_digest.as_bytes());
    encoder.field(
        8,
        &encode_sequence(member_digests.iter().map(|(path, digest)| {
            let mut item = Canonical::new();
            item.field(1, path.as_bytes());
            item.field(2, digest);
            item.finish()
        })),
    );
    digest(AUDIT_TRACE_DOMAIN, &encoder.finish())
}

pub fn nonclaim_set_digest(nonclaims: &[String]) -> [u8; 32] {
    let mut encoder = Canonical::new();
    encoder.field(
        1,
        &encode_sequence(nonclaims.iter().map(|value| value.as_bytes().to_vec())),
    );
    digest(NONCLAIM_SET_DOMAIN, &encoder.finish())
}

pub fn digest_to_hex(digest: [u8; 32]) -> String {
    hex::encode(digest)
}

pub fn parse_digest_hex(value: &str) -> Result<[u8; 32], DigestParseError> {
    if value.len() != 64 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(DigestParseError);
    }
    let bytes = hex::decode(value).map_err(|_| DigestParseError)?;
    let mut out = [0_u8; 32];
    out.copy_from_slice(&bytes);
    Ok(out)
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct DigestParseError;

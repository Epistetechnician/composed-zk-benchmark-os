use sha2::{Digest as _, Sha256};

pub const AUTHORITY_PACKAGE_DOMAIN: &[u8] = b"statebook:p7-authority-package:v1\0";
pub const PREFLIGHT_RECEIPT_DOMAIN: &[u8] = b"statebook:p7-preflight-receipt:v1\0";
pub const LOSS_BOUND_DOMAIN: &[u8] = b"statebook:p7-loss-bound:v1\0";
pub const NONCLAIM_SET_DOMAIN: &[u8] = b"statebook:p7-nonclaim-set:v1\0";

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

pub fn digest_to_hex(digest: [u8; 32]) -> String {
    hex::encode(digest)
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct DigestParseError;

pub fn parse_digest_hex(value: &str) -> Result<[u8; 32], DigestParseError> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    {
        return Err(DigestParseError);
    }
    let bytes = hex::decode(value).map_err(|_| DigestParseError)?;
    let mut out = [0_u8; 32];
    out.copy_from_slice(&bytes);
    Ok(out)
}

pub fn loss_bound_digest(numerator: &str, denominator: &str) -> [u8; 32] {
    let mut encoder = Canonical::new();
    encoder.field(1, numerator.as_bytes());
    encoder.field(2, denominator.as_bytes());
    digest(LOSS_BOUND_DOMAIN, &encoder.finish())
}

pub fn nonclaim_set_digest(nonclaims: &[String]) -> [u8; 32] {
    let mut encoder = Canonical::new();
    encoder.field(
        1,
        &encode_sequence(nonclaims.iter().map(|value| value.as_bytes().to_vec())),
    );
    digest(NONCLAIM_SET_DOMAIN, &encoder.finish())
}

#[allow(clippy::too_many_arguments)]
pub fn authority_package_digest(
    profile_id: &str,
    authority_owner: &str,
    loss_bound_digest_hex: &str,
    rollback: &str,
    pause: &str,
    retention: &str,
    legal_domain: &str,
    production_gate: &str,
    decision_record_digest: &str,
) -> [u8; 32] {
    let mut encoder = Canonical::new();
    encoder.field(1, profile_id.as_bytes());
    encoder.field(2, authority_owner.as_bytes());
    encoder.field(3, loss_bound_digest_hex.as_bytes());
    encoder.field(4, rollback.as_bytes());
    encoder.field(5, pause.as_bytes());
    encoder.field(6, retention.as_bytes());
    encoder.field(7, legal_domain.as_bytes());
    encoder.field(8, production_gate.as_bytes());
    encoder.field(9, decision_record_digest.as_bytes());
    digest(AUTHORITY_PACKAGE_DOMAIN, &encoder.finish())
}

pub fn preflight_receipt_digest(
    profile_id: &str,
    outcome: &str,
    package_digest: &str,
    loss_bound_digest_hex: &str,
    nonclaim_set_digest_hex: &str,
) -> [u8; 32] {
    let mut encoder = Canonical::new();
    encoder.field(1, profile_id.as_bytes());
    encoder.field(2, outcome.as_bytes());
    encoder.field(3, package_digest.as_bytes());
    encoder.field(4, loss_bound_digest_hex.as_bytes());
    encoder.field(5, nonclaim_set_digest_hex.as_bytes());
    encoder.field(6, b"false");
    digest(PREFLIGHT_RECEIPT_DOMAIN, &encoder.finish())
}

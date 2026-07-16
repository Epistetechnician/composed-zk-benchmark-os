use sha2::{Digest as _, Sha256};

pub const AUTHORITY_STATEMENT_DOMAIN: &[u8] = b"statebook:p7-authority-statement:v1\0";
pub const ATTACH_RECEIPT_DOMAIN: &[u8] = b"statebook:p7-attach-receipt:v1\0";
pub const CAPITAL_OVERLAY_DOMAIN: &[u8] = b"statebook:p7-capital-overlay:v1\0";
pub const AUTHORITY_REGISTRATION_DOMAIN: &[u8] = b"statebook:p7-authority-registration:v1\0";

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

pub fn digest_to_hex(digest: [u8; 32]) -> String {
    hex::encode(digest)
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct DigestParseError;

pub fn parse_digest_hex(value: &str) -> Result<[u8; 32], DigestParseError> {
    if value.len() != 64 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(DigestParseError);
    }
    if value.bytes().any(|byte| byte.is_ascii_uppercase()) {
        return Err(DigestParseError);
    }
    let bytes = hex::decode(value).map_err(|_| DigestParseError)?;
    let mut out = [0_u8; 32];
    out.copy_from_slice(&bytes);
    Ok(out)
}

#[allow(clippy::too_many_arguments)]
pub fn authority_statement_digest(
    profile_id: &str,
    authority_namespace: &str,
    authority_id: &str,
    statement_revision: &str,
    subject_terms_digest: &str,
    economic_residual_digest: &str,
    recognized_numerator: &str,
    recognized_denominator: &str,
    issued_at: i64,
    expires_at: i64,
) -> [u8; 32] {
    let mut encoder = Canonical::new();
    encoder.field(1, profile_id.as_bytes());
    encoder.field(2, authority_namespace.as_bytes());
    encoder.field(3, authority_id.as_bytes());
    encoder.field(4, statement_revision.as_bytes());
    encoder.field(5, subject_terms_digest.as_bytes());
    encoder.field(6, economic_residual_digest.as_bytes());
    encoder.field(7, recognized_numerator.as_bytes());
    encoder.field(8, recognized_denominator.as_bytes());
    encoder.field(9, &issued_at.to_be_bytes());
    encoder.field(10, &expires_at.to_be_bytes());
    encoder.field(11, &[0_u8]);
    digest(AUTHORITY_STATEMENT_DOMAIN, &encoder.finish())
}

pub fn registration_digest(
    authority_namespace: &str,
    authority_id: &str,
    statement_revision: &str,
    statement_digest: &str,
    status: &str,
) -> [u8; 32] {
    let mut encoder = Canonical::new();
    encoder.field(1, authority_namespace.as_bytes());
    encoder.field(2, authority_id.as_bytes());
    encoder.field(3, statement_revision.as_bytes());
    encoder.field(4, statement_digest.as_bytes());
    encoder.field(5, status.as_bytes());
    digest(AUTHORITY_REGISTRATION_DOMAIN, &encoder.finish())
}

#[allow(clippy::too_many_arguments)]
pub fn capital_overlay_digest(
    status: &str,
    authority_id: &str,
    eligible_account: &str,
    subject_terms_digest: &str,
    economic_residual_digest: &str,
    recognized_numerator: &str,
    recognized_denominator: &str,
    evaluated_at: i64,
) -> [u8; 32] {
    let mut encoder = Canonical::new();
    encoder.field(1, status.as_bytes());
    encoder.field(2, authority_id.as_bytes());
    encoder.field(3, eligible_account.as_bytes());
    encoder.field(4, subject_terms_digest.as_bytes());
    encoder.field(5, economic_residual_digest.as_bytes());
    encoder.field(6, recognized_numerator.as_bytes());
    encoder.field(7, recognized_denominator.as_bytes());
    encoder.field(8, &evaluated_at.to_be_bytes());
    digest(CAPITAL_OVERLAY_DOMAIN, &encoder.finish())
}

#[allow(clippy::too_many_arguments)]
pub fn attach_receipt_digest(
    profile_id: &str,
    authority_namespace: &str,
    authority_id: &str,
    statement_revision: &str,
    statement_digest: &str,
    registration_digest_hex: &str,
    overlay_digest: &str,
    economic_residual_digest: &str,
) -> [u8; 32] {
    let mut encoder = Canonical::new();
    encoder.field(1, profile_id.as_bytes());
    encoder.field(2, authority_namespace.as_bytes());
    encoder.field(3, authority_id.as_bytes());
    encoder.field(4, statement_revision.as_bytes());
    encoder.field(5, statement_digest.as_bytes());
    encoder.field(6, registration_digest_hex.as_bytes());
    encoder.field(7, overlay_digest.as_bytes());
    encoder.field(8, economic_residual_digest.as_bytes());
    encoder.field(9, &[0_u8]);
    digest(ATTACH_RECEIPT_DOMAIN, &encoder.finish())
}

use sha2::{Digest as _, Sha256};

pub const SOURCE_REGISTRATION_DOMAIN: &[u8] = b"statebook:p6-source-registration:v1\0";
pub const IMPORT_RECEIPT_DOMAIN: &[u8] = b"statebook:p6-import-receipt:v1\0";
pub const CAPTURED_ARTIFACT_DOMAIN: &[u8] = b"statebook:p6-captured-artifact:v1\0";
pub const PROVENANCE_SET_DOMAIN: &[u8] = b"statebook:p6-provenance-set:v1\0";

pub fn digest(domain: &[u8], payload: &[u8]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(domain);
    hasher.update(1_u16.to_be_bytes());
    hasher.update(payload);
    hasher.finalize().into()
}

pub fn raw_sha256(bytes: &[u8]) -> [u8; 32] {
    Sha256::digest(bytes).into()
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

pub fn captured_artifact_digest(
    profile_id: &str,
    venue_namespace: &str,
    content_sha256: &str,
    envelope_bytes: &[u8],
) -> [u8; 32] {
    let mut encoder = Canonical::new();
    encoder.field(1, profile_id.as_bytes());
    encoder.field(2, venue_namespace.as_bytes());
    encoder.field(3, content_sha256.as_bytes());
    encoder.field(4, envelope_bytes);
    digest(CAPTURED_ARTIFACT_DOMAIN, &encoder.finish())
}

pub fn registration_digest(
    venue_namespace: &str,
    source_contract_id: &str,
    source_revision: &str,
    content_sha256: &str,
    evidence_class: &str,
    status: &str,
) -> [u8; 32] {
    let mut encoder = Canonical::new();
    encoder.field(1, venue_namespace.as_bytes());
    encoder.field(2, source_contract_id.as_bytes());
    encoder.field(3, source_revision.as_bytes());
    encoder.field(4, content_sha256.as_bytes());
    encoder.field(5, evidence_class.as_bytes());
    encoder.field(6, status.as_bytes());
    digest(SOURCE_REGISTRATION_DOMAIN, &encoder.finish())
}

#[allow(clippy::too_many_arguments)]
pub fn import_receipt_digest(
    profile_id: &str,
    venue_namespace: &str,
    source_contract_id: &str,
    source_revision: &str,
    content_sha256: &str,
    artifact_digest: &str,
    registration_digest_hex: &str,
) -> [u8; 32] {
    let mut encoder = Canonical::new();
    encoder.field(1, profile_id.as_bytes());
    encoder.field(2, venue_namespace.as_bytes());
    encoder.field(3, source_contract_id.as_bytes());
    encoder.field(4, source_revision.as_bytes());
    encoder.field(5, content_sha256.as_bytes());
    encoder.field(6, artifact_digest.as_bytes());
    encoder.field(7, registration_digest_hex.as_bytes());
    digest(IMPORT_RECEIPT_DOMAIN, &encoder.finish())
}

pub fn provenance_set_digest(claims: &[String], limitations: &[String]) -> [u8; 32] {
    let mut encoder = Canonical::new();
    encoder.field(
        1,
        &encode_sequence(claims.iter().map(|value| value.as_bytes().to_vec())),
    );
    encoder.field(
        2,
        &encode_sequence(limitations.iter().map(|value| value.as_bytes().to_vec())),
    );
    digest(PROVENANCE_SET_DOMAIN, &encoder.finish())
}

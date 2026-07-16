use sha2::{Digest as _, Sha256};
use statebook_core::SignedRational;
use std::collections::BTreeSet;

use crate::DigestV1;

pub const INTENT_DOMAIN: &[u8] = b"statebook:p4-intent:v1\0";
pub const DECISION_CONTEXT_DOMAIN: &[u8] = b"statebook:p4-decision-context:v1\0";
pub const RELEASE_ATTEMPT_DOMAIN: &[u8] = b"statebook:p4-release-attempt:v1\0";
pub const EVIDENCE_SNAPSHOT_DOMAIN: &[u8] = b"statebook:p4-evidence-snapshot:v1\0";
pub const VALUATION_PROFILE_DOMAIN: &[u8] = b"statebook:p4-valuation-profile:v1\0";
pub const POLICY_DOMAIN: &[u8] = b"statebook:p4-policy:v1\0";
pub const LEDGER_TIP_DOMAIN: &[u8] = b"statebook:p4-ledger-tip:v1\0";
pub const SETTLEMENT_STATE_DOMAIN: &[u8] = b"statebook:p4-settlement-state:v1\0";
pub const DECISION_RECORD_DOMAIN: &[u8] = b"statebook:p4-decision-record:v1\0";

pub fn digest(domain: &[u8], payload: &[u8]) -> DigestV1 {
    let mut hasher = Sha256::new();
    hasher.update(domain);
    hasher.update(1_u16.to_be_bytes());
    hasher.update(payload);
    DigestV1::from_raw_bytes(hasher.finalize().into())
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

pub fn encode_string_set(values: &BTreeSet<String>) -> Vec<u8> {
    encode_sequence(values.iter().map(|value| value.as_bytes().to_vec()))
}

pub fn encode_rational(value: SignedRational) -> Vec<u8> {
    let mut out = Vec::with_capacity(32);
    out.extend_from_slice(&value.numerator().to_be_bytes());
    out.extend_from_slice(&value.denominator().to_be_bytes());
    out
}

pub fn encode_bool(value: bool) -> Vec<u8> {
    vec![u8::from(value)]
}

pub fn encode_i64(value: i64) -> Vec<u8> {
    value.to_be_bytes().to_vec()
}

pub fn encode_u32(value: u32) -> Vec<u8> {
    value.to_be_bytes().to_vec()
}

pub fn encode_u8(value: u8) -> Vec<u8> {
    vec![value]
}

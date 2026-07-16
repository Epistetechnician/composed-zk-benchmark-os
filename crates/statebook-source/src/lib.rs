#![forbid(unsafe_code)]

mod bounds;
mod canonical;
mod error;
mod import;
mod json_util;
mod registry;
mod types;

pub use bounds::{
    CLAIM_BOUNDARY_P6, MAX_ARTIFACT_BYTES_V1, MAX_CLAIM_OR_LIMITATION_COUNT_V1,
    MAX_OBSERVATIONS_V1, MAX_REGISTRATIONS_V1, STATE_SLICE_P6, SYNTHETIC_CLEARING_NAMESPACE_V1,
    SYNTHETIC_CLEARING_PROFILE_V1,
};
pub use canonical::{
    captured_artifact_digest, digest_to_hex, import_receipt_digest, parse_digest_hex,
    provenance_set_digest, raw_sha256, registration_digest, DigestParseError,
    CAPTURED_ARTIFACT_DOMAIN, IMPORT_RECEIPT_DOMAIN, PROVENANCE_SET_DOMAIN,
    SOURCE_REGISTRATION_DOMAIN,
};
pub use error::SourceErrorV1;
pub use import::import_captured_terms_v1;
pub use types::{
    EvidenceClassV1, ImportReceiptV1, RegistrationStatusV1, SourceRegistrationV1, SourceRegistryV1,
};

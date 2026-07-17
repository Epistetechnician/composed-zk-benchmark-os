#![forbid(unsafe_code)]

mod bounds;
mod canonical;
mod error;
mod json_util;
mod preflight;
mod types;

pub use bounds::{
    CLAIM_BOUNDARY_P7, HERMETIC_PROFILE_V1, MAX_CONTROLLER_NAMES_V1, MAX_NONCLAIMS_V1,
    MAX_PACKAGE_BYTES_V1, STATE_SLICE_P7,
};
pub use canonical::{
    authority_package_digest, digest_to_hex, loss_bound_digest, nonclaim_set_digest,
    parse_digest_hex, preflight_receipt_digest, DigestParseError, AUTHORITY_PACKAGE_DOMAIN,
    LOSS_BOUND_DOMAIN, NONCLAIM_SET_DOMAIN, PREFLIGHT_RECEIPT_DOMAIN,
};
pub use error::AuthorityErrorV1;
pub use preflight::evaluate_authority_preflight_v1;
pub use types::{
    AuditRetentionV1, AuthorityPackageV1, ExactRationalV1, HandoffBindingV1, PauseSemanticsV1,
    PreflightOutcomeV1, PreflightReceiptV1, ProductionGateV1, RollbackSemanticsV1,
};

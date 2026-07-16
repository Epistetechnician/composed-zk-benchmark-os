#![forbid(unsafe_code)]

mod attach;
mod bounds;
mod canonical;
mod error;
mod json_util;
mod registry;
mod types;

pub use attach::{attach_authority_statement_v1, evaluate_attached_statement_v1};
pub use bounds::{
    CLAIM_BOUNDARY_P7, LEGAL_OPS_GATE_AUTHORITY_OWNER_V1, LEGAL_OPS_GATE_LEGAL_REVIEW_V1,
    LEGAL_OPS_GATE_LIVE_PRODUCTS_DEFERRED_V1, LEGAL_OPS_GATE_LOSS_LIMITS_V1,
    LEGAL_OPS_GATE_OPERATIONAL_EVIDENCE_V1, LEGAL_OPS_GATE_THREAT_MODEL_V1,
    MAX_LIMITATION_OR_NONCLAIM_COUNT_V1, MAX_REGISTRATIONS_V1, MAX_STATEMENT_BYTES_V1,
    STATE_SLICE_P7, SYNTHETIC_AUTHORITY_NAMESPACE_V1, SYNTHETIC_AUTHORITY_PROFILE_V1,
};
pub use canonical::{
    attach_receipt_digest, authority_statement_digest, capital_overlay_digest, digest_to_hex,
    parse_digest_hex, registration_digest, DigestParseError, ATTACH_RECEIPT_DOMAIN,
    AUTHORITY_REGISTRATION_DOMAIN, AUTHORITY_STATEMENT_DOMAIN, CAPITAL_OVERLAY_DOMAIN,
};
pub use error::AuthorityErrorV1;
pub use types::{
    AttachReceiptV1, AuthorityRegistrationV1, AuthorityRegistryV1, CapitalOverlayStatusV1,
    CapitalOverlayV1, StatementStatusV1,
};

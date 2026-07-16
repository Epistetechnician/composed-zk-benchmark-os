#![forbid(unsafe_code)]

mod exact;
mod model;
mod normalization;
mod state_key;

pub use exact::{ExactError, ScaledInteger, SignedRational, MAX_DECIMAL_SCALE_V1};
pub use model::{
    Comparator, EndpointPolicy, LineageReceiptV1, NormalizedTerminalSemantics,
    ParsedSourceContractV1, RoundingMode, SemanticCompletenessReport, SemanticCompletenessStatus,
    SemanticField, Sha256Digest, StateKeyReceiptV1, StateKeyV1, UnsupportedTerm, ValidatedContract,
    ValidatedNormalizationProfileV1,
};
pub use normalization::{
    assess_semantic_completeness, parse_normalization_profile_v1, parse_source_contract_v1,
    validate_and_lower, LoweringError, ParseError, ProfileError,
};
pub use state_key::derive_state_key;

pub const STATE_SLICE: &str = "statebook-p1-core-semantic-fixtures";
pub const SOURCE_SCHEMA_V1: &str = "statebook-terminal-source:v1";
pub const NORMALIZATION_PROFILE_SCHEMA_V1: &str = "statebook-normalization-profile:v1";
pub const STATE_KEY_SCHEMA_V1: u16 = 1;
pub const STATE_KEY_DOMAIN_V1: &[u8] = b"statebook:state-key:v1\0";
pub const CLAIM_BOUNDARY: &str =
    "local fixture-backed semantic normalization and deterministic StateKeyV1 regression evidence only";

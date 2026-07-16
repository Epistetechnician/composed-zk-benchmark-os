#![forbid(unsafe_code)]

mod exact;
mod model;
mod normalization;
mod payoff;
mod state_key;

pub use exact::{quantize_exact, ExactError, ScaledInteger, SignedRational, MAX_DECIMAL_SCALE_V1};
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
pub use payoff::{
    analyze_terminal_residual_v1, AggregatedPositionReceiptV1, ContractPositionV1,
    DeclaredStateDomainV1, DeclaredTerminalStateV1, PayoffAnalysisError, PayoffAssumptionV1,
    PayoffCompletenessReportV1, PayoffCompletenessStatusV1, StateEvaluationStatusV1,
    StateResidualV1, UnmodeledResidualClassV1, UnsupportedStateReasonV1, WorstCaseAssetResidualV1,
    DECLARED_STATE_DOMAIN_V1, MAX_DECLARED_STATES_V1, MAX_PORTFOLIO_LEGS_V1,
};
pub use state_key::derive_state_key;

pub const STATE_SLICE: &str = "statebook-p1-core-semantic-fixtures";
pub const SOURCE_SCHEMA_V1: &str = "statebook-terminal-source:v1";
pub const NORMALIZATION_PROFILE_SCHEMA_V1: &str = "statebook-normalization-profile:v1";
pub const STATE_KEY_SCHEMA_V1: u16 = 1;
pub const STATE_KEY_DOMAIN_V1: &[u8] = b"statebook:state-key:v1\0";
pub const CLAIM_BOUNDARY: &str =
    "local fixture-backed semantic normalization and deterministic StateKeyV1 regression evidence only";
pub const PAYOFF_STATE_SLICE: &str = "statebook-p2-payoff-residual-engine";
pub const PAYOFF_CLAIM_BOUNDARY: &str =
    "local exact terminal indicator payoff and residual analysis over finite declared states only";

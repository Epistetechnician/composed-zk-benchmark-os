use thiserror::Error;

#[derive(Clone, Debug, Eq, Error, PartialEq)]
pub enum SettlementParseErrorV1 {
    #[error("fixture exceeds {max_fixture_bytes_v1} bytes")]
    FixtureTooLarge { max_fixture_bytes_v1: usize },
    #[error("invalid schema version: {0}")]
    InvalidSchemaVersion(String),
    #[error("duplicate JSON key: {0}")]
    DuplicateJsonKey(String),
    #[error("invalid JSON: {0}")]
    InvalidJson(String),
    #[error("invalid digest: {0}")]
    InvalidDigest(String),
    #[error("invalid identifier: {0}")]
    InvalidIdentifier(String),
    #[error("invalid rational: numerator={numerator} denominator={denominator}")]
    InvalidRational {
        numerator: String,
        denominator: String,
    },
    #[error("collection exceeds limit: {field}")]
    CollectionLimit { field: &'static str },
    #[error("unknown field: {0}")]
    UnknownField(String),
    #[error("missing required field: {0}")]
    MissingField(String),
}

#[derive(Clone, Debug, Eq, Error, PartialEq)]
pub enum SettlementTransitionErrorV1 {
    #[error("ledger tip compare-and-swap conflict")]
    LedgerCasConflict,
    #[error("exact arithmetic overflow")]
    ArithmeticOverflow,
    #[error("invalid breaker transition")]
    InvalidBreakerTransition,
    #[error("invalid queue transfer combination")]
    InvalidQueueTransferCombination,
    #[error("invalid breaker renewal request")]
    InvalidBreakerRenewal,
    #[error("breaker renewal rejected at ceiling")]
    BreakerRenewalRejected,
    #[error("challenge count exceeds max_challenges_v1")]
    ChallengeLimitExceeded,
}

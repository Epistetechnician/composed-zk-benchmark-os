use thiserror::Error;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum AuthorityErrorV1 {
    #[error("statement exceeds maximum byte size")]
    StatementTooLarge,
    #[error("malformed JSON")]
    MalformedJson,
    #[error("duplicate JSON key")]
    DuplicateJsonKey,
    #[error("unknown schema version")]
    UnknownSchemaVersion,
    #[error("unknown profile: {0}")]
    UnknownProfile(String),
    #[error("unknown field: {0}")]
    UnknownField(String),
    #[error("missing required field: {0}")]
    MissingField(String),
    #[error("noncanonical digest")]
    NoncanonicalDigest,
    #[error("noncanonical identifier")]
    NoncanonicalIdentifier,
    #[error("noncanonical rational")]
    NoncanonicalRational,
    #[error("authority namespace mismatch")]
    AuthorityNamespaceMismatch,
    #[error("invalid validity window")]
    InvalidValidityWindow,
    #[error("execution authority grant is forbidden in this phase")]
    ExecutionAuthorityGrantForbidden,
    #[error("registration count exceeds maximum")]
    TooManyRegistrations,
    #[error("limitation or nonclaim count exceeds maximum")]
    TooManyLimitationsOrNonclaims,
    #[error("statement already active with different digest")]
    ActiveRevisionConflict,
    #[error("authority statement not found")]
    StatementNotFound,
    #[error("statement already revoked")]
    AlreadyRevoked,
}

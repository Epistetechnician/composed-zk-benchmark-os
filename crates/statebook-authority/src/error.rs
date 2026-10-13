use thiserror::Error;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum AuthorityErrorV1 {
    #[error("package exceeds maximum byte size")]
    PackageTooLarge,
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
    #[error("malformed exact rational")]
    MalformedExactRational,
    #[error("unknown enum value: {0}")]
    UnknownEnum(String),
    #[error("authorized production gate rejected in this slice")]
    AuthorizedGateRejected,
    #[error("handoff grants_authority must be false")]
    HandoffGrantsAuthority,
    #[error("nonclaim count exceeds maximum")]
    TooManyNonclaims,
    #[error("controller name count exceeds maximum")]
    TooManyControllerNames,
}

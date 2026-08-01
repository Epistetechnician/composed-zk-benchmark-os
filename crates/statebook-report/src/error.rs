use thiserror::Error;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum BundleErrorV1 {
    #[error("bundle exceeds maximum byte size")]
    BundleTooLarge,
    #[error("member count exceeds maximum")]
    TooManyMembers,
    #[error("path exceeds maximum length")]
    PathTooLong,
    #[error("path traversal rejected: {0}")]
    PathTraversal(String),
    #[error("symlink rejected: {0}")]
    Symlink(String),
    #[error("missing required file: {0}")]
    MissingFile(String),
    #[error("undeclared extra file: {0}")]
    ExtraFile(String),
    #[error("stale manifest digest")]
    StaleManifestDigest,
    #[error("stale member digest for {0}")]
    StaleMemberDigest(String),
    #[error("malformed JSON in {0}")]
    MalformedJson(String),
    #[error("unknown schema version in {0}")]
    UnknownSchemaVersion(String),
    #[error("unknown enum value in {0}")]
    UnknownEnum(String),
    #[error("duplicate JSON key in {0}")]
    DuplicateJsonKey(String),
    #[error("noncanonical digest in {0}")]
    NoncanonicalDigest(String),
    #[error("noncanonical identifier in {0}")]
    NoncanonicalIdentifier(String),
    #[error("composition digest mismatch")]
    CompositionDigestMismatch,
    #[error("decision context digest mismatch")]
    DecisionContextDigestMismatch,
    #[error("tampered nonclaim set")]
    TamperedNonclaimSet,
    #[error("trace digest mismatch")]
    TraceDigestMismatch,
    #[error("secret or response-body retention rejected")]
    SecretRetention,
    #[error("nonclaim count exceeds maximum")]
    TooManyNonclaims,
    #[error("observation count exceeds maximum")]
    TooManyObservations,
    #[error("trace record count exceeds maximum")]
    TooManyTraceRecords,
    #[error("filesystem error: {0}")]
    Filesystem(String),
    #[error("invalid bundle input: {0}")]
    InvalidInput(String),
}

#[derive(Debug, Error, PartialEq, Eq)]
pub enum AdapterErrorV1 {
    #[error("fixture exceeds maximum byte size")]
    FixtureTooLarge,
    #[error("malformed JSON")]
    MalformedJson,
    #[error("unknown schema version")]
    UnknownSchemaVersion,
    #[error("unknown field: {0}")]
    UnknownField(String),
    #[error("duplicate JSON key")]
    DuplicateJsonKey,
    #[error("unknown profile: {0}")]
    UnknownProfile(String),
    #[error("noncanonical digest")]
    NoncanonicalDigest,
    #[error("noncanonical identifier")]
    NoncanonicalIdentifier,
    #[error("nonclaim count exceeds maximum")]
    TooManyNonclaims,
    #[error("observation count exceeds maximum")]
    TooManyObservations,
    #[error("missing required field: {0}")]
    MissingField(String),
    #[error("invalid handoff input: {0}")]
    InvalidHandoff(String),
}

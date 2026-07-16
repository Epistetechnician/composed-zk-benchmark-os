use thiserror::Error;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum SourceErrorV1 {
    #[error("artifact exceeds maximum byte size")]
    ArtifactTooLarge,
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
    #[error("content digest mismatch")]
    ContentDigestMismatch,
    #[error("unknown evidence class: {0}")]
    UnknownEvidenceClass(String),
    #[error("illustrative narrative cannot enter assurance paths")]
    IllustrativeNarrativeRejected,
    #[error("registration count exceeds maximum")]
    TooManyRegistrations,
    #[error("claim or limitation count exceeds maximum")]
    TooManyClaimsOrLimitations,
    #[error("observation count exceeds maximum")]
    TooManyObservations,
    #[error("source already active with different digest")]
    ActiveRevisionConflict,
    #[error("source revision not found")]
    RevisionNotFound,
    #[error("terms parse rejected by statebook-core")]
    TermsParseRejected,
    #[error("venue namespace mismatch")]
    VenueNamespaceMismatch,
}

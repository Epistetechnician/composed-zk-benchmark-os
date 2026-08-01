use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EvidenceClassV1 {
    VenueDocumentation,
    DirectArtifact,
    CapturedReplay,
    IllustrativeNarrative,
}

impl EvidenceClassV1 {
    pub fn parse(value: &str) -> Option<Self> {
        match value {
            "venue_documentation" => Some(Self::VenueDocumentation),
            "direct_artifact" => Some(Self::DirectArtifact),
            "captured_replay" => Some(Self::CapturedReplay),
            "illustrative_narrative" => Some(Self::IllustrativeNarrative),
            _ => None,
        }
    }

    pub const fn as_str(self) -> &'static str {
        match self {
            Self::VenueDocumentation => "venue_documentation",
            Self::DirectArtifact => "direct_artifact",
            Self::CapturedReplay => "captured_replay",
            Self::IllustrativeNarrative => "illustrative_narrative",
        }
    }

    pub const fn may_enter_assurance(self) -> bool {
        !matches!(self, Self::IllustrativeNarrative)
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct SourceRegistrationV1 {
    pub schema_version: String,
    pub venue_namespace: String,
    pub source_contract_id: String,
    pub source_revision: String,
    pub published_at: i64,
    pub retrieved_at: i64,
    pub evidence_class: EvidenceClassV1,
    pub content_sha256: String,
    pub supported_claims: Vec<String>,
    pub limitations: Vec<String>,
    pub status: RegistrationStatusV1,
    pub registration_digest: String,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RegistrationStatusV1 {
    Active,
    Superseded,
    Revoked,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ImportReceiptV1 {
    pub schema_version: String,
    pub profile_id: String,
    pub venue_namespace: String,
    pub source_contract_id: String,
    pub source_revision: String,
    pub evidence_class: EvidenceClassV1,
    pub content_sha256: String,
    pub artifact_digest: String,
    pub registration_digest: String,
    pub import_receipt_digest: String,
    pub unknown_facts: Vec<String>,
    pub adapter_nonclaims: Vec<String>,
}

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct SourceRegistryV1 {
    pub(crate) registrations: BTreeMap<String, SourceRegistrationV1>,
}

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum StatementStatusV1 {
    Active,
    Revoked,
    Expired,
}

impl StatementStatusV1 {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Active => "active",
            Self::Revoked => "revoked",
            Self::Expired => "expired",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum CapitalOverlayStatusV1 {
    RecognizedInFixture,
    PartiallyRecognizedInFixture,
    NotRecognizedInFixture,
    NotEvaluated,
}

impl CapitalOverlayStatusV1 {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::RecognizedInFixture => "recognized_in_fixture",
            Self::PartiallyRecognizedInFixture => "partially_recognized_in_fixture",
            Self::NotRecognizedInFixture => "not_recognized_in_fixture",
            Self::NotEvaluated => "not_evaluated",
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct AuthorityRegistrationV1 {
    pub schema_version: String,
    pub profile_id: String,
    pub authority_namespace: String,
    pub authority_id: String,
    pub statement_revision: String,
    pub eligible_account: String,
    pub model_id: String,
    pub model_version: String,
    pub model_digest: String,
    pub margin_rule_id: String,
    pub jurisdiction: String,
    pub subject_terms_digest: String,
    pub economic_residual_digest: String,
    pub recognized_numerator: String,
    pub recognized_denominator: String,
    pub issued_at: i64,
    pub expires_at: i64,
    pub grants_execution_authority: bool,
    pub status: StatementStatusV1,
    pub statement_digest: String,
    pub registration_digest: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct CapitalOverlayV1 {
    pub schema_version: String,
    pub status: CapitalOverlayStatusV1,
    pub authority_id: String,
    pub eligible_account: String,
    pub subject_terms_digest: String,
    pub economic_residual_digest: String,
    pub recognized_numerator: String,
    pub recognized_denominator: String,
    pub evaluated_at: i64,
    pub overlay_digest: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct AttachReceiptV1 {
    pub schema_version: String,
    pub profile_id: String,
    pub authority_namespace: String,
    pub authority_id: String,
    pub statement_revision: String,
    pub subject_terms_digest: String,
    pub economic_residual_digest: String,
    pub statement_digest: String,
    pub registration_digest: String,
    pub attach_receipt_digest: String,
    pub grants_execution_authority: bool,
    pub capital_overlay: CapitalOverlayV1,
    pub adapter_nonclaims: Vec<String>,
    pub legal_ops_gate_deferred: Vec<String>,
}

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct AuthorityRegistryV1 {
    pub(crate) registrations: BTreeMap<String, AuthorityRegistrationV1>,
}

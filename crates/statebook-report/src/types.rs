use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

use crate::bounds::{
    BUNDLE_SCHEMA_VERSION_V1, HANDOFF_SCHEMA_VERSION_V1, NONCLAIMS_SCHEMA_VERSION_V1,
    TRACE_SCHEMA_VERSION_V1,
};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct AuditBundleV1 {
    pub bundle_id: String,
    pub terms_digest: String,
    pub state_key_digest: String,
    pub residual_digest: String,
    pub composition_digest: String,
    pub decision_context_digest: String,
    pub decision_record: DecisionRecordSectionV1,
    pub completeness: CompletenessSectionV1,
    pub evidence: EvidenceSectionV1,
    pub policy: PolicySectionV1,
    pub valuation: ValuationSectionV1,
    pub budget: BudgetSectionV1,
    pub queue: QueueSectionV1,
    pub nonclaims: NonclaimsSectionV1,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct DecisionRecordSectionV1 {
    pub schema_version: u16,
    pub outcome: String,
    pub intent_digest: String,
    pub decision_context_digest: String,
    pub instant_release_amount: ExactRationalV1,
    pub ledger_tip_before: String,
    pub ledger_tip_after: String,
    pub reasons: Vec<String>,
    pub evaluated_at: i64,
    pub record_digest: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExactRationalV1 {
    pub numerator: String,
    pub denominator: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct CompletenessSectionV1 {
    pub schema_version: String,
    pub composition_digest: String,
    pub dimension_digests: BTreeMap<String, String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceSectionV1 {
    pub schema_version: String,
    pub snapshot_digest: String,
    pub observation_count: u32,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct PolicySectionV1 {
    pub schema_version: String,
    pub policy_digest: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ValuationSectionV1 {
    pub schema_version: String,
    pub valuation_digest: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct BudgetSectionV1 {
    pub schema_version: String,
    pub ledger_tip_before: String,
    pub ledger_tip_after: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct QueueSectionV1 {
    pub schema_version: String,
    pub queue_status: String,
    pub transfer_status: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct NonclaimsSectionV1 {
    pub schema_version: String,
    pub nonclaims: Vec<String>,
    pub nonclaim_set_digest: String,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MaterializationReceiptV1 {
    pub bundle_id: String,
    pub manifest_digest: String,
    pub audit_trace_digest: String,
    pub nonclaim_set_digest: String,
    pub member_digests: BTreeMap<String, String>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ValidatedAuditBundleV1 {
    pub bundle_id: String,
    pub manifest_digest: String,
    pub audit_trace_digest: String,
    pub nonclaim_set_digest: String,
    pub member_digests: BTreeMap<String, String>,
    pub trace: TraceSectionV1,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct TraceSectionV1 {
    pub schema_version: String,
    pub trace_id: String,
    pub terms_digest: String,
    pub state_key_digest: String,
    pub residual_digest: String,
    pub composition_digest: String,
    pub decision_context_digest: String,
    pub decision_record_digest: String,
    pub audit_trace_digest: String,
    pub member_digests: BTreeMap<String, String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ManifestV1 {
    pub schema_version: String,
    pub bundle_id: String,
    pub members: BTreeMap<String, String>,
    pub manifest_digest: String,
    pub audit_trace_digest: String,
    pub nonclaim_set_digest: String,
}

impl ManifestV1 {
    pub fn schema_version() -> &'static str {
        BUNDLE_SCHEMA_VERSION_V1
    }
}

impl TraceSectionV1 {
    pub fn schema_version() -> &'static str {
        TRACE_SCHEMA_VERSION_V1
    }
}

impl NonclaimsSectionV1 {
    pub fn schema_version() -> &'static str {
        NONCLAIMS_SCHEMA_VERSION_V1
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct FixtureAdapterInputV1 {
    pub schema_version: String,
    pub profile_id: String,
    pub issuer: String,
    pub subject: String,
    pub property: String,
    pub scope: String,
    pub nonce: String,
    pub issue_at: i64,
    pub expiry_at: Option<i64>,
    pub trust_roots: Vec<String>,
    pub policy_version: String,
    pub source_refs: Vec<String>,
    pub dependency_roots: Vec<String>,
    pub unknown_facts: Vec<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct MappedObservationV1 {
    pub issuer: String,
    pub subject: String,
    pub property: String,
    pub scope: String,
    pub nonce: String,
    pub issue_at: i64,
    pub expiry_at: Option<i64>,
    pub trust_roots: Vec<String>,
    pub policy_version: String,
    pub source_refs: Vec<String>,
    pub dependency_roots: Vec<String>,
    pub unknown_facts: Vec<String>,
    pub evidence_maturity: String,
    pub adapter_nonclaims: Vec<String>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum DecisionHandoffInputV1<'a> {
    DecisionJson(&'a str),
    DigestBound {
        decision_record_digest: &'a str,
        intent_digest: &'a str,
        decision_context_digest: &'a str,
        outcome: &'a str,
    },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct HandoffEnvelopeV1 {
    pub schema_version: String,
    pub grants_authority: bool,
    pub decision_record_digest: String,
    pub intent_digest: String,
    pub decision_context_digest: String,
    pub outcome: String,
    pub adapter_nonclaims: Vec<String>,
}

impl HandoffEnvelopeV1 {
    pub fn schema_version() -> &'static str {
        HANDOFF_SCHEMA_VERSION_V1
    }
}

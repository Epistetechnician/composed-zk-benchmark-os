use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvaluationReceiptV1 {
    pub schema_version: String,
    pub profile_id: String,
    pub source_import_digest: String,
    pub state_key: String,
    pub validated_contract_digest: String,
    pub payoff_domain_digest: String,
    pub payoff_status: String,
    pub capital_status: String,
    pub decision_outcome: String,
    pub decision_record_digest: String,
    pub handoff_grants_authority: bool,
    pub bundle_manifest_digest: String,
    pub authority_attach_digest: String,
    pub authority_overlay_status: String,
    pub grants_execution_authority: bool,
    pub nonclaims: Vec<String>,
}

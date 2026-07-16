pub const STATE_SLICE_P7: &str = "statebook-p7-authority-integration";
pub const CLAIM_BOUNDARY_P7: &str =
    "local hermetic synthetic authority-statement attach without live authority or value movement";

pub const AUTHORITY_STATEMENT_SCHEMA_V1: &str = "statebook-p7-authority-statement:v1";
pub const REGISTRATION_SCHEMA_V1: &str = "statebook-p7-authority-registration:v1";
pub const ATTACH_RECEIPT_SCHEMA_V1: &str = "statebook-p7-attach-receipt:v1";
pub const CAPITAL_OVERLAY_SCHEMA_V1: &str = "statebook-p7-capital-overlay:v1";

pub const SYNTHETIC_AUTHORITY_PROFILE_V1: &str = "synthetic-clearing-authority-v1";
pub const SYNTHETIC_AUTHORITY_NAMESPACE_V1: &str = "synthetic.clearing.authority.v1";

pub const LEGAL_OPS_GATE_THREAT_MODEL_V1: &str = "required-named-threat-model-owner";
pub const LEGAL_OPS_GATE_LEGAL_REVIEW_V1: &str = "required-named-legal-or-compliance-signoff";
pub const LEGAL_OPS_GATE_OPERATIONAL_EVIDENCE_V1: &str =
    "required-named-runbook-and-loss-limit-evidence";
pub const LEGAL_OPS_GATE_LOSS_LIMITS_V1: &str = "required-quantitative-loss-budget-owner";
pub const LEGAL_OPS_GATE_AUTHORITY_OWNER_V1: &str = "required-named-authority-owner";
pub const LEGAL_OPS_GATE_LIVE_PRODUCTS_DEFERRED_V1: &str =
    "live-execution-custody-signing-pause-margin-settlement-deferred";

pub const MAX_STATEMENT_BYTES_V1: usize = 1_048_576;
pub const MAX_REGISTRATIONS_V1: usize = 256;
pub const MAX_FIELD_BYTES_V1: usize = 512;
pub const MAX_LIMITATION_OR_NONCLAIM_COUNT_V1: usize = 32;
pub const MAX_IDENTIFIER_BYTES_V1: usize = 128;

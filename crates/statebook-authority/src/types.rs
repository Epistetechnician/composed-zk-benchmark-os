use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RollbackSemanticsV1 {
    RejectAndJournal,
    HoldAndEscalate,
}

impl RollbackSemanticsV1 {
    pub fn parse(value: &str) -> Option<Self> {
        match value {
            "reject_and_journal" => Some(Self::RejectAndJournal),
            "hold_and_escalate" => Some(Self::HoldAndEscalate),
            _ => None,
        }
    }

    pub const fn as_str(self) -> &'static str {
        match self {
            Self::RejectAndJournal => "reject_and_journal",
            Self::HoldAndEscalate => "hold_and_escalate",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PauseSemanticsV1 {
    ScopedHalt,
    GlobalHaltRequired,
}

impl PauseSemanticsV1 {
    pub fn parse(value: &str) -> Option<Self> {
        match value {
            "scoped_halt" => Some(Self::ScopedHalt),
            "global_halt_required" => Some(Self::GlobalHaltRequired),
            _ => None,
        }
    }

    pub const fn as_str(self) -> &'static str {
        match self {
            Self::ScopedHalt => "scoped_halt",
            Self::GlobalHaltRequired => "global_halt_required",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AuditRetentionV1 {
    Days30,
    Days90,
    Days365,
}

impl AuditRetentionV1 {
    pub fn parse(value: &str) -> Option<Self> {
        match value {
            "days_30" => Some(Self::Days30),
            "days_90" => Some(Self::Days90),
            "days_365" => Some(Self::Days365),
            _ => None,
        }
    }

    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Days30 => "days_30",
            Self::Days90 => "days_90",
            Self::Days365 => "days_365",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ProductionGateV1 {
    Incomplete,
    Denied,
}

impl ProductionGateV1 {
    pub fn parse(value: &str) -> Option<Self> {
        match value {
            "incomplete" => Some(Self::Incomplete),
            "denied" => Some(Self::Denied),
            _ => None,
        }
    }

    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Incomplete => "incomplete",
            Self::Denied => "denied",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PreflightOutcomeV1 {
    Incomplete,
    Denied,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExactRationalV1 {
    pub numerator: String,
    pub denominator: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct HandoffBindingV1 {
    pub decision_record_digest: String,
    pub intent_digest: String,
    pub decision_context_digest: String,
    pub outcome: String,
    pub grants_authority: bool,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct AuthorityPackageV1 {
    pub schema_version: String,
    pub profile_id: String,
    pub authority_owner: String,
    pub maximum_loss: ExactRationalV1,
    pub rollback_semantics: RollbackSemanticsV1,
    pub pause_semantics: PauseSemanticsV1,
    pub audit_retention: AuditRetentionV1,
    pub legal_domain: String,
    pub production_gate: ProductionGateV1,
    pub controller_names: Vec<String>,
    pub handoff: HandoffBindingV1,
    pub package_digest: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct PreflightReceiptV1 {
    pub schema_version: String,
    pub profile_id: String,
    pub outcome: PreflightOutcomeV1,
    pub grants_authority: bool,
    pub package_digest: String,
    pub preflight_receipt_digest: String,
    pub loss_bound_digest: String,
    pub nonclaim_set_digest: String,
    pub adapter_nonclaims: Vec<String>,
}

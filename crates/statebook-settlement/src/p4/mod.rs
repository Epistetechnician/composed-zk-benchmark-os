pub use bounds::MAX_REFILL_PER_EPOCH_V1;
pub use breaker::{attempt_breaker_renewal_v1, validate_breaker_transition};
pub use budget::{
    apply_budget_refill_v1, apply_destination_finality_v1, apply_proven_no_outflow_v1,
    apply_transfer_submit_v1, available_capacity, TransferBudgetResultV1,
};
pub use cancel::apply_cancel_v1;
pub use challenge::apply_challenge_v1;
pub use hysteresis::{attempt_policy_transition_v1, evaluate_policy_transition_v1};
pub use recovery::{
    apply_recovery_canary_v1, apply_recovery_halt_all_v1, apply_recovery_reconciliation_v1,
    apply_recovery_reopen_v1, RecoveryApplyResultV1,
};

mod amounts;
mod assurance;
mod bounds;
mod breaker;
mod budget;
mod cancel;
mod canonical;
mod challenge;
mod classify;
mod digest;
mod error;
mod gates;
mod hysteresis;
mod kernel;
mod linked_plan;
mod obligation;
mod parse;
mod recovery;
mod types;
mod valuation;

#[allow(unused_imports)]
pub use bounds::{
    MAX_BREAKER_SCOPES_V1, MAX_BUDGET_AXES_V1, MAX_CHALLENGES_V1, MAX_EVIDENCE_OBSERVATIONS_V1,
    MAX_EVIDENCE_ROOTS_V1, MAX_FIXTURE_BYTES_V1, MAX_IN_FLIGHT_TRANSFERS_V1,
    MAX_LEDGER_JOURNAL_ENTRIES_V1, MAX_LINKED_PLAN_LEGS_V1, MAX_QUEUE_DEPTH_V1, MAX_QUEUE_PARTS_V1,
    MAX_SCENARIO_STEPS_V1, MAX_VALUATION_OBSERVATIONS_V1,
};
pub use digest::{
    decision_context_digest, evidence_snapshot_digest, intent_digest, intent_payload,
    policy_digest, valuation_profile_digest,
};
pub use error::{SettlementParseErrorV1, SettlementTransitionErrorV1};
pub use hysteresis::PolicyTransitionResultV1;
pub use kernel::decide_and_transition;
pub use parse::parse_settlement_scenario_v1;
pub use types::{
    AssuranceTierV1, AtomicLinkedExchangePlanV1, BreakerScopeV1, BreakerStateV1,
    CancelApplyResultV1, ChallengeApplyResultV1, ChallengeKindV1, ChallengeSubmissionV1, ClockV1,
    DecisionMissingFactV1, DecisionNonclaimV1, DecisionOutcomeV1, DecisionReasonV1,
    DecisionRecordV1, DirectionV1, ExternalRiskReducingObligationV1, ExternalizationRequestV1,
    FinancialBasisKindV1, FinancialBasisV1, QueueStatusV1, ReleaseClassV1, SettlementPolicyV1,
    SettlementScenarioV1, SettlementStateV1, TransferStatusV1,
};

pub const STATE_SLICE_P4: &str = "statebook-p4-settlement-simulator";
pub const CLAIM_BOUNDARY_P4: &str =
    "local hermetic fixture regression only; no value moves; decision records are non-authoritative";

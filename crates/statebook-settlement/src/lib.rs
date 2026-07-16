#![forbid(unsafe_code)]

mod completeness;
mod p4;

pub use completeness::{
    compose_completeness_reports_v1, derive_analysis_subject_v1, parse_completeness_fixture_v1,
    AnalysisSubjectV1, AssuranceCompletenessReportV1, AssuranceCompletenessStatusV1,
    AssuranceContextV1, AssurancePropertyObservationV1, AssurancePropertyV1, AssuranceRootV1,
    AssuranceVerdictV1, CapitalCompletenessReportV1, CapitalCompletenessStatusV1, CapitalContextV1,
    CapitalFixtureVerdictV1, CapitalReceiptResultV1, CompletenessAssumptionV1,
    CompletenessDimensionV1, CompletenessEvaluationErrorV1, CompletenessMissingFactV1,
    CompletenessReasonV1, DependencyDisclosureV1, DigestV1, EvidenceClassV1,
    ExecutionCompletenessReportV1, ExecutionCompletenessStatusV1, ExecutionContextV1,
    ExecutionLegResultV1, ExecutionSideV1, FixtureParseErrorV1, FixtureSupportV1,
    InFlightReconciliationV1, RecoveryCapabilityV1, RecoveryCompletenessReportV1,
    RecoveryCompletenessStatusV1, RecoveryContextV1, RecoveryPathObservationV1,
    RecoveryPathProfileV1, RootClassV1, SettlementCompletenessReportV1,
    SettlementCompletenessStatusV1, SettlementContextV1, SettlementStageObservationV1,
    SettlementStageV1, SevenCompletenessReportsV1, StageVerdictV1, ValidatedCompletenessFixtureV1,
    ASSURANCE_PROPERTY_COUNT_V1, MAX_ASSURANCE_OBSERVATIONS_V1, MAX_BOOK_LEVELS_PER_LEG_V1,
    MAX_CANARY_STAGES_V1, MAX_CAPITAL_RECEIPTS_V1, MAX_CURRENT_OR_DEPENDENCY_ROOTS_V1,
    MAX_EXECUTION_LEGS_V1, MAX_FIXTURE_BYTES_V1, MAX_IN_FLIGHT_RECOVERY_ITEMS_V1,
    MAX_RECOVERY_PATHS_V1, MAX_SETTLEMENT_OBLIGATIONS_V1, MAX_SOURCE_EVIDENCE_DIGESTS_V1,
    RECOVERY_CAPABILITY_COUNT_V1, RECOVERY_PATH_COUNT_V1,
};

pub use p4::{
    apply_cancel_v1, apply_challenge_v1, apply_destination_finality_v1, apply_proven_no_outflow_v1,
    apply_recovery_canary_v1, apply_recovery_halt_all_v1, apply_recovery_reconciliation_v1,
    apply_recovery_reopen_v1, apply_transfer_submit_v1, attempt_breaker_renewal_v1,
    attempt_policy_transition_v1, available_capacity, decide_and_transition,
    decision_context_digest, evaluate_policy_transition_v1, evidence_snapshot_digest,
    intent_digest, intent_payload, parse_settlement_scenario_v1, policy_digest,
    validate_breaker_transition, valuation_profile_digest, AssuranceTierV1,
    AtomicLinkedExchangePlanV1, BreakerScopeV1, BreakerStateV1, CancelApplyResultV1,
    ChallengeApplyResultV1, ChallengeKindV1, ChallengeSubmissionV1, ClockV1, DecisionMissingFactV1,
    DecisionNonclaimV1, DecisionOutcomeV1, DecisionReasonV1, DecisionRecordV1, DirectionV1,
    ExternalRiskReducingObligationV1, ExternalizationRequestV1, FinancialBasisKindV1,
    FinancialBasisV1, PolicyTransitionResultV1, QueueStatusV1, RecoveryApplyResultV1,
    ReleaseClassV1, SettlementParseErrorV1, SettlementPolicyV1, SettlementScenarioV1,
    SettlementStateV1, SettlementTransitionErrorV1, TransferBudgetResultV1, TransferStatusV1,
    CLAIM_BOUNDARY_P4, MAX_BREAKER_SCOPES_V1, MAX_BUDGET_AXES_V1, MAX_CHALLENGES_V1,
    MAX_EVIDENCE_OBSERVATIONS_V1, MAX_EVIDENCE_ROOTS_V1, MAX_IN_FLIGHT_TRANSFERS_V1,
    MAX_LEDGER_JOURNAL_ENTRIES_V1, MAX_LINKED_PLAN_LEGS_V1, MAX_QUEUE_DEPTH_V1, MAX_QUEUE_PARTS_V1,
    MAX_SCENARIO_STEPS_V1, MAX_VALUATION_OBSERVATIONS_V1, STATE_SLICE_P4,
};

pub const STATE_SLICE: &str = "statebook-p3-seven-completeness-reports";
pub const CLAIM_BOUNDARY: &str =
    "local hermetic fixture-qualified completeness reporting without aggregate authority";

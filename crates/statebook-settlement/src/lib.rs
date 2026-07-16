#![forbid(unsafe_code)]

mod completeness;

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

pub const STATE_SLICE: &str = "statebook-p3-seven-completeness-reports";
pub const CLAIM_BOUNDARY: &str =
    "local hermetic fixture-qualified completeness reporting without aggregate authority";

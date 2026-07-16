pub const STATE_SLICE_P5: &str = "statebook-p5-evidence-adapters-and-report-bundles";
pub const CLAIM_BOUNDARY_P5: &str =
    "local hermetic digest-bound audit bundles without authority or value movement";

pub const BUNDLE_SCHEMA_VERSION_V1: &str = "statebook-p5-audit-bundle:v1";
pub const TRACE_SCHEMA_VERSION_V1: &str = "statebook-p5-audit-trace:v1";
pub const NONCLAIMS_SCHEMA_VERSION_V1: &str = "statebook-p5-nonclaims:v1";
pub const FIXTURE_ADAPTER_SCHEMA_VERSION_V1: &str = "statebook-p5-fixture-adapter:v1";
pub const HSAI_FIXTURE_SCHEMA_VERSION_V1: &str = "statebook-p5-hsai-fixture-envelope:v1";
pub const HANDOFF_SCHEMA_VERSION_V1: &str = "statebook-p5-decision-handoff:v1";

pub const MANIFEST_PATH: &str = "manifest.json";
pub const MANIFEST_DIGEST_PATH: &str = "digests/manifest.sha256";
pub const RECORD_DECISION_PATH: &str = "records/decision.json";
pub const RECORD_COMPLETENESS_PATH: &str = "records/completeness.json";
pub const RECORD_EVIDENCE_PATH: &str = "records/evidence.json";
pub const RECORD_POLICY_PATH: &str = "records/policy.json";
pub const RECORD_VALUATION_PATH: &str = "records/valuation.json";
pub const RECORD_BUDGET_PATH: &str = "records/budget.json";
pub const RECORD_QUEUE_PATH: &str = "records/queue.json";
pub const RECORD_NONCLAIMS_PATH: &str = "records/nonclaims.json";
pub const RECORD_TRACE_PATH: &str = "records/trace.json";

pub const REQUIRED_MEMBER_PATHS: &[&str] = &[
    RECORD_DECISION_PATH,
    RECORD_COMPLETENESS_PATH,
    RECORD_EVIDENCE_PATH,
    RECORD_POLICY_PATH,
    RECORD_VALUATION_PATH,
    RECORD_BUDGET_PATH,
    RECORD_QUEUE_PATH,
    RECORD_NONCLAIMS_PATH,
    RECORD_TRACE_PATH,
];

/// Record members bound into the audit trace digest (excludes self-referential trace.json).
pub const TRACE_BOUND_MEMBER_PATHS: &[&str] = &[
    RECORD_DECISION_PATH,
    RECORD_COMPLETENESS_PATH,
    RECORD_EVIDENCE_PATH,
    RECORD_POLICY_PATH,
    RECORD_VALUATION_PATH,
    RECORD_BUDGET_PATH,
    RECORD_QUEUE_PATH,
    RECORD_NONCLAIMS_PATH,
];

pub const MAX_BUNDLE_BYTES_V1: usize = 1_048_576;
pub const MAX_BUNDLE_MEMBER_COUNT_V1: usize = 9;
pub const MAX_BUNDLE_PATH_LENGTH_V1: usize = 256;
pub const MAX_OBSERVATIONS_V1: usize = 128;
pub const MAX_NONCLAIMS_V1: usize = 64;
pub const MAX_TRACE_RECORDS_V1: usize = 16;
pub const MAX_IDENTIFIER_BYTES_V1: usize = 128;
pub const MAX_FIXTURE_BYTES_V1: usize = 65_536;

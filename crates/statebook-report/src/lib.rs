#![forbid(unsafe_code)]

mod adapter;
mod bounds;
mod bundle;
mod canonical;
mod error;
mod json_util;
mod types;

pub use adapter::{
    handoff_decision_record_v1, map_fixture_observation_v1, map_hsai_fixture_envelope_v1,
    parse_fixture_adapter_input_v1,
};
pub use bounds::{
    BUNDLE_SCHEMA_VERSION_V1, CLAIM_BOUNDARY_P5, MAX_BUNDLE_BYTES_V1, MAX_BUNDLE_MEMBER_COUNT_V1,
    MAX_BUNDLE_PATH_LENGTH_V1, MAX_FIXTURE_BYTES_V1, MAX_NONCLAIMS_V1, MAX_OBSERVATIONS_V1,
    MAX_TRACE_RECORDS_V1, REQUIRED_MEMBER_PATHS, STATE_SLICE_P5,
};
pub use bundle::{
    build_golden_bundle_from_decision, composition_binding_digest, materialize_audit_bundle_v1,
    readback_validate_audit_bundle_v1,
};
pub use canonical::{
    audit_trace_digest, digest_to_hex, manifest_digest, member_digest, nonclaim_set_digest,
    parse_digest_hex, DigestParseError, AUDIT_TRACE_DOMAIN, BUNDLE_MANIFEST_DOMAIN,
    BUNDLE_MEMBER_DOMAIN, NONCLAIM_SET_DOMAIN,
};
pub use error::{AdapterErrorV1, BundleErrorV1};
pub use types::{
    AuditBundleV1, BudgetSectionV1, CompletenessSectionV1, DecisionHandoffInputV1,
    DecisionRecordSectionV1, EvidenceSectionV1, ExactRationalV1, FixtureAdapterInputV1,
    HandoffEnvelopeV1, ManifestV1, MappedObservationV1, MaterializationReceiptV1,
    NonclaimsSectionV1, PolicySectionV1, QueueSectionV1, TraceSectionV1, ValidatedAuditBundleV1,
    ValuationSectionV1,
};

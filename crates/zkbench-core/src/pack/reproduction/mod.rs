//! Reproduction metadata and inert external replay plan attachments.
//!
//! Phase M slice 1 attaches Level0DesignNote reproduction metadata and inert
//! external replay plans to Level1 local packs. It does not promote packs or
//! ledgers to Level2 evidence.

pub mod attachment;
pub mod eligibility;
pub mod export;
pub mod metadata;
pub mod validation;

pub use attachment::attach_reproduction_bundle_to_pack;
pub use eligibility::{
    evaluate_level2_eligibility, Level2EligibilityBlockingReason, Level2EligibilityReport,
    Level2EligibilityReportVersion, Level2EligibilityStatus,
};
pub use export::{
    deserialize_benchmark_pack_reproduction_metadata_json,
    serialize_benchmark_pack_reproduction_metadata_json,
};
pub use metadata::{
    BenchmarkPackReproductionMetadata, BenchmarkPackReproductionMetadataVersion,
    ExternalReplayPlanAttachment, ExternalReplayPlanKind,
};
pub use validation::validate_benchmark_pack_reproduction_metadata;

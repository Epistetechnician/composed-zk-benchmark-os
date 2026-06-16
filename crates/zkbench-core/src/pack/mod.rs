//! Benchmark pack skeleton for deterministic local replay artifacts.
//!
//! Packs are local JSON bundles only. They do not represent official benchmark
//! evidence, cross-backend reproduction, or formal proof.

pub mod manifest;
pub mod reader;
pub mod report_bundle_review;
pub mod reproduction;
pub mod validation;
pub mod writer;

pub use manifest::{
    BenchmarkPackFile, BenchmarkPackFileRole, BenchmarkPackId, BenchmarkPackManifest,
    BenchmarkPackSummary, BenchmarkPackVersion,
};
pub use reader::BenchmarkPackReader;
pub use report_bundle_review::{
    deserialize_report_bundle_review_report_json, review_report_bundle,
    review_sampled_report_bundles, review_soak_report_bundles,
    serialize_report_bundle_review_report_json, ReportBundleReviewFinding,
    ReportBundleReviewFindingSeverity, ReportBundleReviewPlan, ReportBundleReviewReport,
    ReportBundleReviewReportVersion, ReportBundleSampleStrategy,
};
pub use reproduction::{
    attach_reproduction_bundle_to_pack, deserialize_benchmark_pack_reproduction_metadata_json,
    evaluate_level2_eligibility, serialize_benchmark_pack_reproduction_metadata_json,
    validate_benchmark_pack_reproduction_metadata, BenchmarkPackReproductionMetadata,
    BenchmarkPackReproductionMetadataVersion, ExternalReplayPlanAttachment,
    ExternalReplayPlanKind, Level2EligibilityBlockingReason, Level2EligibilityReport,
    Level2EligibilityReportVersion, Level2EligibilityStatus,
};
pub use validation::{BenchmarkPackValidation, BenchmarkPackValidationError};
pub use writer::BenchmarkPackWriter;

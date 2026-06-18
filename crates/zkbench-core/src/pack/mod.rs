//! Benchmark pack skeleton for deterministic local replay artifacts.
//!
//! Packs are local JSON bundles only. They do not represent official benchmark
//! evidence, cross-backend reproduction, or formal proof.

pub mod manifest;
pub mod reader;
pub mod readiness;
pub mod validation;
pub mod writer;

pub use manifest::{
    BenchmarkPackFile, BenchmarkPackFileRole, BenchmarkPackId, BenchmarkPackManifest,
    BenchmarkPackSummary, BenchmarkPackVersion,
};
pub use reader::BenchmarkPackReader;
pub use readiness::{
    compute_pack_readiness_report_digest, deserialize_pack_readiness_report_json,
    serialize_pack_readiness_report_json, validate_pack_readiness_report, PackReadinessCheck,
    PackReadinessCheckKind, PackReadinessInputKind, PackReadinessInputRef,
    PackReadinessReplayCommandMetadata, PackReadinessReport, PackReadinessValidation,
    PackReadinessValidationIssue, PackReadinessValidationIssueKind, PackReadinessVersion,
};
pub use validation::{BenchmarkPackValidation, BenchmarkPackValidationError};
pub use writer::BenchmarkPackWriter;

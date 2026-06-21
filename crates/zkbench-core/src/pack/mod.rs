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
    build_pack_readiness_report_from_reader, compute_pack_readiness_report_digest,
    deserialize_pack_readiness_report_json, read_pack_readiness_report,
    read_pack_readiness_validation, serialize_pack_readiness_report_json,
    validate_pack_readiness_report, write_pack_readiness_outputs_for_pack, PackReadinessCheck,
    PackReadinessCheckKind, PackReadinessInputKind, PackReadinessInputRef, PackReadinessOutput,
    PackReadinessReplayCommandMetadata, PackReadinessReport, PackReadinessValidation,
    PackReadinessValidationIssue, PackReadinessValidationIssueKind, PackReadinessVersion,
    PACK_READINESS_REPORT_PATH, PACK_READINESS_VALIDATION_PATH, PACK_VALIDATION_REPORT_PATH,
};
pub use validation::{BenchmarkPackValidation, BenchmarkPackValidationError};
pub use writer::BenchmarkPackWriter;

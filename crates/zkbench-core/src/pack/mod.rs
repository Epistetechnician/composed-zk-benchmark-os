//! Benchmark pack skeleton for deterministic local replay artifacts.
//!
//! Packs are local JSON bundles only. They do not represent official benchmark
//! evidence, cross-backend reproduction, or formal proof.

pub mod manifest;
pub mod reader;
pub mod validation;
pub mod writer;

pub use manifest::{
    BenchmarkPackFile, BenchmarkPackFileRole, BenchmarkPackId, BenchmarkPackManifest,
    BenchmarkPackSummary, BenchmarkPackVersion,
};
pub use reader::BenchmarkPackReader;
pub use validation::{BenchmarkPackValidation, BenchmarkPackValidationError};
pub use writer::BenchmarkPackWriter;

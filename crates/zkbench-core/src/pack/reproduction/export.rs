//! Serialization helpers for reproduction metadata.

use crate::error::{Result, ZkBenchError};

use super::metadata::BenchmarkPackReproductionMetadata;

/// Serialize reproduction metadata to pretty JSON.
pub fn serialize_benchmark_pack_reproduction_metadata_json(
    metadata: &BenchmarkPackReproductionMetadata,
) -> Result<String> {
    serde_json::to_string_pretty(metadata).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_benchmark_pack_reproduction_metadata_json",
            error.to_string(),
        )
    })
}

/// Deserialize reproduction metadata from JSON.
pub fn deserialize_benchmark_pack_reproduction_metadata_json(
    json: &str,
) -> Result<BenchmarkPackReproductionMetadata> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_benchmark_pack_reproduction_metadata_json",
            error.to_string(),
        )
    })
}

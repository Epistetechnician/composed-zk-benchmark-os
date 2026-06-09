//! Deterministic JSON serialization for replay artifacts.

use crate::error::{Result, ZkBenchError};

use super::{ReplayManifest, ReplayResult};

/// Serialize a replay manifest to pretty JSON.
pub fn serialize_replay_manifest_json(manifest: &ReplayManifest) -> Result<String> {
    serde_json::to_string_pretty(manifest).map_err(|error| {
        ZkBenchError::serialization("serialize_replay_manifest_json", error.to_string())
    })
}

/// Deserialize a replay manifest from JSON.
pub fn deserialize_replay_manifest_json(json: &str) -> Result<ReplayManifest> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("deserialize_replay_manifest_json", error.to_string())
    })
}

/// Serialize a replay result to pretty JSON.
pub fn serialize_replay_result_json(result: &ReplayResult) -> Result<String> {
    serde_json::to_string_pretty(result).map_err(|error| {
        ZkBenchError::serialization("serialize_replay_result_json", error.to_string())
    })
}

/// Deserialize a replay result from JSON.
pub fn deserialize_replay_result_json(json: &str) -> Result<ReplayResult> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("deserialize_replay_result_json", error.to_string())
    })
}

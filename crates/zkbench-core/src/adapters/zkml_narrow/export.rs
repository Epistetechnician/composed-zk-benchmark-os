//! Serialization and export helpers for narrow zkML workload plans.

use crate::error::{Result, ZkBenchError};

use super::manifest::{build_default_zkml_narrow_adapter_manifest, ZkmlNarrowAdapterManifest};
use super::validation::validate_zkml_narrow_workload_plan;
use super::workload::{build_default_zkml_narrow_workload_plan, ZkmlNarrowWorkloadPlan};

/// Build a narrow zkML workload plan from the default manifest.
pub fn build_zkml_narrow_workload_plan() -> Result<ZkmlNarrowWorkloadPlan> {
    let manifest = build_default_zkml_narrow_adapter_manifest();
    build_zkml_narrow_workload_plan_from_manifest(&manifest)
}

/// Build a narrow zkML workload plan from a manifest.
pub fn build_zkml_narrow_workload_plan_from_manifest(
    manifest: &ZkmlNarrowAdapterManifest,
) -> Result<ZkmlNarrowWorkloadPlan> {
    let plan = build_default_zkml_narrow_workload_plan(manifest);
    let validation = validate_zkml_narrow_workload_plan(&plan);
    if !validation.valid {
        return Err(ZkBenchError::zkml_narrow(
            "zkml_narrow.workload_plan.validation",
            format!("workload plan validation failed: {:?}", validation.errors),
        ));
    }
    Ok(plan)
}

/// Serialize narrow zkML adapter manifest JSON.
pub fn serialize_zkml_narrow_manifest_json(manifest: &ZkmlNarrowAdapterManifest) -> Result<String> {
    serde_json::to_string_pretty(manifest).map_err(|error| {
        ZkBenchError::serialization("serialize_zkml_narrow_manifest_json", error.to_string())
    })
}

/// Deserialize narrow zkML adapter manifest JSON.
pub fn deserialize_zkml_narrow_manifest_json(json: &str) -> Result<ZkmlNarrowAdapterManifest> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("deserialize_zkml_narrow_manifest_json", error.to_string())
    })
}

/// Serialize narrow zkML workload plan JSON.
pub fn serialize_zkml_narrow_workload_plan_json(plan: &ZkmlNarrowWorkloadPlan) -> Result<String> {
    serde_json::to_string_pretty(plan).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_zkml_narrow_workload_plan_json",
            error.to_string(),
        )
    })
}

/// Deserialize narrow zkML workload plan JSON.
pub fn deserialize_zkml_narrow_workload_plan_json(json: &str) -> Result<ZkmlNarrowWorkloadPlan> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_zkml_narrow_workload_plan_json",
            error.to_string(),
        )
    })
}

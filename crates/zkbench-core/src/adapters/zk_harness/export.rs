//! Serialization and export helpers for zk-Harness dry-run plans.

use crate::error::{Result, ZkBenchError};
use crate::pack::BenchmarkPackReader;

use super::dry_run::{ZkHarnessDryRunPlan, ZkHarnessDryRunPlanner};
use super::manifest::{build_default_zk_harness_adapter_manifest, ZkHarnessAdapterManifest};
use super::validation::validate_zk_harness_dry_run_plan;

/// Build a zk-Harness dry-run plan from a local benchmark pack reader.
pub fn build_zk_harness_dry_run_plan_from_pack(
    pack: &BenchmarkPackReader,
) -> Result<ZkHarnessDryRunPlan> {
    export_pack_to_zk_harness_dry_run_plan(pack)
}

/// Export a local benchmark pack into a zk-Harness dry-run plan.
pub fn export_pack_to_zk_harness_dry_run_plan(
    pack: &BenchmarkPackReader,
) -> Result<ZkHarnessDryRunPlan> {
    let manifest = build_default_zk_harness_adapter_manifest();
    let plan = ZkHarnessDryRunPlanner::new(manifest)
        .map_pack(pack)?
        .build()?;
    let validation = validate_zk_harness_dry_run_plan(&plan);
    if !validation.valid {
        return Err(ZkBenchError::zk_harness(
            "zk_harness.dry_run_plan.validation",
            format!("dry-run plan validation failed: {:?}", validation.errors),
        ));
    }
    Ok(plan)
}

/// Serialize zk-Harness adapter manifest JSON.
pub fn serialize_zk_harness_manifest_json(manifest: &ZkHarnessAdapterManifest) -> Result<String> {
    serde_json::to_string_pretty(manifest).map_err(|error| {
        ZkBenchError::serialization("serialize_zk_harness_manifest_json", error.to_string())
    })
}

/// Deserialize zk-Harness adapter manifest JSON.
pub fn deserialize_zk_harness_manifest_json(json: &str) -> Result<ZkHarnessAdapterManifest> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("deserialize_zk_harness_manifest_json", error.to_string())
    })
}

/// Serialize zk-Harness dry-run plan JSON.
pub fn serialize_zk_harness_dry_run_plan_json(plan: &ZkHarnessDryRunPlan) -> Result<String> {
    serde_json::to_string_pretty(plan).map_err(|error| {
        ZkBenchError::serialization("serialize_zk_harness_dry_run_plan_json", error.to_string())
    })
}

/// Deserialize zk-Harness dry-run plan JSON.
pub fn deserialize_zk_harness_dry_run_plan_json(json: &str) -> Result<ZkHarnessDryRunPlan> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_zk_harness_dry_run_plan_json",
            error.to_string(),
        )
    })
}

//! Serialization and export helpers for gnark recursion envelope plans.

use crate::error::{Result, ZkBenchError};

use super::envelope::{build_default_gnark_recursion_envelope_plan, GnarkRecursionEnvelopePlan};
use super::manifest::{
    build_default_gnark_recursion_adapter_manifest, GnarkRecursionAdapterManifest,
};
use super::validation::validate_gnark_recursion_envelope_plan;

/// Build a gnark recursion envelope plan from the default manifest.
pub fn build_gnark_recursion_envelope_plan() -> Result<GnarkRecursionEnvelopePlan> {
    let manifest = build_default_gnark_recursion_adapter_manifest();
    build_gnark_recursion_envelope_plan_from_manifest(&manifest)
}

/// Build a gnark recursion envelope plan from a manifest.
pub fn build_gnark_recursion_envelope_plan_from_manifest(
    manifest: &GnarkRecursionAdapterManifest,
) -> Result<GnarkRecursionEnvelopePlan> {
    let plan = build_default_gnark_recursion_envelope_plan(manifest);
    let validation = validate_gnark_recursion_envelope_plan(&plan);
    if !validation.valid {
        return Err(ZkBenchError::gnark_recursion(
            "gnark_recursion.envelope_plan.validation",
            format!("envelope plan validation failed: {:?}", validation.errors),
        ));
    }
    Ok(plan)
}

/// Serialize gnark recursion adapter manifest JSON.
pub fn serialize_gnark_recursion_manifest_json(
    manifest: &GnarkRecursionAdapterManifest,
) -> Result<String> {
    serde_json::to_string_pretty(manifest).map_err(|error| {
        ZkBenchError::serialization("serialize_gnark_recursion_manifest_json", error.to_string())
    })
}

/// Deserialize gnark recursion adapter manifest JSON.
pub fn deserialize_gnark_recursion_manifest_json(
    json: &str,
) -> Result<GnarkRecursionAdapterManifest> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_gnark_recursion_manifest_json",
            error.to_string(),
        )
    })
}

/// Serialize gnark recursion envelope plan JSON.
pub fn serialize_gnark_recursion_envelope_plan_json(
    plan: &GnarkRecursionEnvelopePlan,
) -> Result<String> {
    serde_json::to_string_pretty(plan).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_gnark_recursion_envelope_plan_json",
            error.to_string(),
        )
    })
}

/// Deserialize gnark recursion envelope plan JSON.
pub fn deserialize_gnark_recursion_envelope_plan_json(
    json: &str,
) -> Result<GnarkRecursionEnvelopePlan> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_gnark_recursion_envelope_plan_json",
            error.to_string(),
        )
    })
}

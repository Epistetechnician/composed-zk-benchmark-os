//! Static registry metadata primitives for future phases.

use serde::{Deserialize, Serialize};

use crate::adapters::{
    build_default_gnark_recursion_adapter_manifest, build_default_zk_harness_adapter_manifest,
    build_default_zkml_narrow_adapter_manifest, local_json_capabilities,
    zk_harness_dry_run_capabilities, BackendTarget, GnarkRecursionAdapterRegistryEntry,
    GnarkRecursionEnvelopePlanRegistryEntry, GnarkRecursionEnvelopePlanVersion,
    ZkHarnessAdapterRegistryEntry, ZkHarnessDryRunPlanRegistryEntry, ZkHarnessDryRunPlanVersion,
    ZkmlNarrowAdapterRegistryEntry, ZkmlNarrowWorkloadPlanRegistryEntry,
    ZkmlNarrowWorkloadPlanVersion, LOCAL_JSON_ADAPTER_ID,
};
use crate::generator::templates::{all_family_templates, family_template};
use crate::generator::{FamilyKind, FamilyTemplate};
use crate::pack::BenchmarkPackVersion;

/// Registry entry metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RegistryEntry {
    /// Entry id.
    pub id: String,
    /// Entry kind.
    pub kind: String,
    /// Description.
    #[serde(default)]
    pub description: Option<String>,
}

/// In-memory local generator registry. It does not load external plugins or
/// execute dynamic code.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LocalGeneratorRegistry {
    /// Registered family templates.
    pub templates: Vec<FamilyTemplate>,
}

impl Default for LocalGeneratorRegistry {
    fn default() -> Self {
        Self {
            templates: all_family_templates(),
        }
    }
}

impl LocalGeneratorRegistry {
    /// List available local generator templates.
    pub fn list_templates(&self) -> &[FamilyTemplate] {
        &self.templates
    }

    /// Resolve a family template by kind.
    pub fn resolve(&self, kind: FamilyKind) -> Option<&FamilyTemplate> {
        self.templates.iter().find(|template| template.kind == kind)
    }
}

/// List available local generators.
pub fn list_available_local_generators() -> Vec<FamilyTemplate> {
    all_family_templates()
}

/// Resolve a local generator family template.
pub fn resolve_local_generator(kind: FamilyKind) -> FamilyTemplate {
    family_template(kind)
}

/// List local-only backend adapter targets.
pub fn list_local_adapter_targets() -> Vec<BackendTarget> {
    vec![
        BackendTarget {
            id: LOCAL_JSON_ADAPTER_ID.to_string(),
            kind: "local_json".to_string(),
            version: Some("phase-f-local-json-v0".to_string()),
            capabilities: local_json_capabilities(),
        },
        BackendTarget {
            id: "zk_harness_dry_run_adapter_v0".to_string(),
            kind: "zk_harness_dry_run_preparation".to_string(),
            version: Some("phase-g-zk-harness-dry-run-v0".to_string()),
            capabilities: zk_harness_dry_run_capabilities(),
        },
    ]
}

/// Register the local benchmark pack schema version.
pub fn local_benchmark_pack_schema() -> RegistryEntry {
    RegistryEntry {
        id: BenchmarkPackVersion::default().value,
        kind: "benchmark_pack_schema".to_string(),
        description: Some(
            "Local JSON benchmark pack schema; local replay is not official benchmark evidence."
                .to_string(),
        ),
    }
}

/// Register the Phase K gnark recursion adapter preparation metadata.
pub fn gnark_recursion_adapter_registry_entry() -> GnarkRecursionAdapterRegistryEntry {
    let manifest = build_default_gnark_recursion_adapter_manifest();
    GnarkRecursionAdapterRegistryEntry {
        id: "gnark_recursion_envelope_adapter_phase_k".to_string(),
        adapter_manifest_id: manifest.id,
        notes: vec![
            "Adapter preparation only; external execution is disabled by default.".to_string(),
            "Recursion proof is not semantic proof.".to_string(),
        ],
    }
}

/// Register the Phase K gnark recursion envelope plan schema.
pub fn gnark_recursion_envelope_plan_registry_entry() -> GnarkRecursionEnvelopePlanRegistryEntry {
    GnarkRecursionEnvelopePlanRegistryEntry {
        id: "gnark_recursion_envelope_plan_phase_k".to_string(),
        plan_version: GnarkRecursionEnvelopePlanVersion::default().value,
        notes: vec!["gnark recursion envelope plans are not benchmark results.".to_string()],
    }
}

/// Register the Phase L narrow zkML adapter preparation metadata.
pub fn zkml_narrow_adapter_registry_entry() -> ZkmlNarrowAdapterRegistryEntry {
    let manifest = build_default_zkml_narrow_adapter_manifest();
    ZkmlNarrowAdapterRegistryEntry {
        id: "zkml_narrow_workload_adapter_phase_l".to_string(),
        adapter_manifest_id: manifest.id,
        notes: vec![
            "Adapter preparation only; external execution is disabled by default.".to_string(),
            "zkML metrics do not prove semantic soundness.".to_string(),
        ],
    }
}

/// Register the Phase L narrow zkML workload plan schema.
pub fn zkml_narrow_workload_plan_registry_entry() -> ZkmlNarrowWorkloadPlanRegistryEntry {
    ZkmlNarrowWorkloadPlanRegistryEntry {
        id: "zkml_narrow_workload_plan_phase_l".to_string(),
        plan_version: ZkmlNarrowWorkloadPlanVersion::default().value,
        notes: vec!["Narrow zkML workload plans are not benchmark results.".to_string()],
    }
}

/// Register the Phase G zk-Harness adapter preparation metadata.
pub fn zk_harness_adapter_registry_entry() -> ZkHarnessAdapterRegistryEntry {
    let manifest = build_default_zk_harness_adapter_manifest();
    ZkHarnessAdapterRegistryEntry {
        id: "zk_harness_dry_run_adapter_phase_g".to_string(),
        adapter_manifest_id: manifest.id,
        notes: vec![
            "Adapter preparation only; external execution is disabled by default.".to_string(),
        ],
    }
}

/// Register the Phase G zk-Harness dry-run plan schema.
pub fn zk_harness_dry_run_plan_registry_entry() -> ZkHarnessDryRunPlanRegistryEntry {
    ZkHarnessDryRunPlanRegistryEntry {
        id: "zk_harness_dry_run_plan_phase_g".to_string(),
        plan_version: ZkHarnessDryRunPlanVersion::default().value,
        notes: vec!["zk-Harness dry-run plans are not benchmark results.".to_string()],
    }
}

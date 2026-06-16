//! gnark recursion adapter preparation.
//!
//! Phase K is inert manifest and envelope-planning only. It does not invoke
//! gnark, Go tooling, external commands, or produce recursion proof evidence.

use serde::{Deserialize, Serialize};

pub mod capabilities;
pub mod envelope;
pub mod evidence;
pub mod export;
pub mod manifest;
pub mod mapping;
pub mod validation;

pub use capabilities::{
    default_gnark_recursion_capability_declaration, gnark_recursion_capabilities,
    GnarkRecursionAdapterCapabilityDeclaration,
};
pub use envelope::{
    build_default_gnark_recursion_envelope_plan, GnarkRecursionEnvelopePlan,
    GnarkRecursionEnvelopePlanId, GnarkRecursionEnvelopePlanVersion, GnarkRecursionEnvelopeStep,
    GnarkRecursionEnvelopeStepKind, GnarkRecursionExecutionPolicy, GnarkRecursionPlannedCommand,
    GnarkRecursionToolRef,
};
pub use evidence::{
    GnarkRecursionClaimBoundaryPolicy, GnarkRecursionEvidenceMapping, GnarkRecursionEvidencePolicy,
};
pub use export::{
    build_gnark_recursion_envelope_plan, build_gnark_recursion_envelope_plan_from_manifest,
    deserialize_gnark_recursion_envelope_plan_json, deserialize_gnark_recursion_manifest_json,
    serialize_gnark_recursion_envelope_plan_json, serialize_gnark_recursion_manifest_json,
};
pub use manifest::{
    build_default_gnark_recursion_adapter_manifest, GnarkRecursionAdapterManifest,
    GnarkRecursionAdapterManifestId, GnarkRecursionAdapterManifestVersion,
    GnarkRecursionAdapterScope, GnarkRecursionAdapterStatus, GnarkRecursionCompatibilityTarget,
    GnarkRecursionIntegrationPhase, GnarkRecursionReviewStatus, GnarkRecursionSchemaAssumption,
    GnarkRecursionSourcePolicy,
};
pub use mapping::{
    default_gnark_recursion_fixture_scope, GnarkRecursionEnvelopeScope, GnarkRecursionFixtureRef,
    GnarkRecursionUnsupportedFeature,
};
pub use validation::{
    validate_gnark_recursion_envelope_plan, GnarkRecursionEnvelopeValidation,
    GnarkRecursionEnvelopeValidationIssue,
};

/// Registry entry for the Phase K gnark recursion adapter preparation layer.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionAdapterRegistryEntry {
    /// Registry id.
    pub id: String,
    /// Adapter manifest id.
    pub adapter_manifest_id: String,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Registry entry for a gnark recursion envelope plan schema.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionEnvelopePlanRegistryEntry {
    /// Registry id.
    pub id: String,
    /// Plan version.
    pub plan_version: String,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

//! Narrow zkML workload scope and fixture mapping.

use serde::{Deserialize, Serialize};

use crate::evidence::{
    compute_artifact_digest_bytes, ArtifactDigest, ArtifactKind, ArtifactRole, ClaimBoundary,
};
use crate::mutation::MutationClass;

/// Unsupported feature declaration.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowUnsupportedFeature {
    /// Feature id.
    pub id: String,
    /// Reason the feature is unsupported.
    pub reason: String,
}

impl ZkmlNarrowUnsupportedFeature {
    /// Build an unsupported feature entry.
    pub fn new(id: impl Into<String>, reason: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            reason: reason.into(),
        }
    }
}

/// Reference to a semantic zkML/control-flow mixed fixture.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowFixtureRef {
    /// Semantic machine id.
    pub machine_id: String,
    /// Relative fixture path.
    pub relative_fixture_path: String,
    /// Fixture digest.
    pub fixture_digest: ArtifactDigest,
    /// Claim boundary for the fixture metadata.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Scope for the default narrow zkML workload lane.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ZkmlNarrowWorkloadScope {
    /// Semantic machine id.
    pub machine_id: String,
    /// Relative fixture path.
    pub relative_fixture_path: String,
    /// Fixture digest.
    pub fixture_digest: ArtifactDigest,
    /// Public input field ids from the fixture.
    pub public_input_fields: Vec<String>,
    /// Private witness field ids from the fixture.
    pub private_witness_fields: Vec<String>,
    /// Supported mutation classes.
    pub supported_mutation_classes: Vec<MutationClass>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Default narrow zkML scope anchored to the repository fixture.
pub fn default_zkml_narrow_fixture_scope() -> ZkmlNarrowWorkloadScope {
    let fixture_bytes = include_bytes!("../../../tests/fixtures/zkml_control_flow_mixed.yaml");
    ZkmlNarrowWorkloadScope {
        machine_id: "zkml_control_flow_mixed".to_string(),
        relative_fixture_path: "tests/fixtures/zkml_control_flow_mixed.yaml".to_string(),
        fixture_digest: compute_artifact_digest_bytes(
            fixture_bytes,
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Input),
        ),
        public_input_fields: vec![
            "confidence".to_string(),
            "threshold".to_string(),
            "label".to_string(),
        ],
        private_witness_fields: Vec::new(),
        supported_mutation_classes: vec![
            MutationClass::ObservationOmission,
            MutationClass::PublicPrivateBoundaryMismatch,
            MutationClass::WitnessAliasing,
        ],
        notes: vec![
            "Metadata-rich control-flow fixture only; no real zkML benchmark result.".to_string(),
            "Fixture is a semantic subject, not a model artifact.".to_string(),
        ],
    }
}

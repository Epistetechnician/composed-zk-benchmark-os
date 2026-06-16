//! gnark recursion envelope scope and fixture mapping.

use serde::{Deserialize, Serialize};

use crate::evidence::{
    compute_artifact_digest_bytes, ArtifactDigest, ArtifactKind, ArtifactRole, ClaimBoundary,
};
use crate::mutation::MutationClass;

/// Unsupported feature declaration.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionUnsupportedFeature {
    /// Feature id.
    pub id: String,
    /// Reason the feature is unsupported.
    pub reason: String,
}

impl GnarkRecursionUnsupportedFeature {
    /// Build an unsupported feature entry.
    pub fn new(id: impl Into<String>, reason: impl Into<String>) -> Self {
        Self {
            id: id.into(),
            reason: reason.into(),
        }
    }
}

/// Reference to a semantic recursion-envelope fixture.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionFixtureRef {
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

/// Scope for the default recursion envelope lane.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GnarkRecursionEnvelopeScope {
    /// Semantic machine id.
    pub machine_id: String,
    /// Relative fixture path.
    pub relative_fixture_path: String,
    /// Fixture digest.
    pub fixture_digest: ArtifactDigest,
    /// Supported mutation classes.
    pub supported_mutation_classes: Vec<MutationClass>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Default recursion envelope scope anchored to the repository fixture.
pub fn default_gnark_recursion_fixture_scope() -> GnarkRecursionEnvelopeScope {
    let fixture_bytes = include_bytes!("../../../tests/fixtures/recursive_loop_envelope.yaml");
    GnarkRecursionEnvelopeScope {
        machine_id: "recursive_loop_envelope".to_string(),
        relative_fixture_path: "tests/fixtures/recursive_loop_envelope.yaml".to_string(),
        fixture_digest: compute_artifact_digest_bytes(
            fixture_bytes,
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Input),
        ),
        supported_mutation_classes: vec![MutationClass::RecursionEnvelopeMismatch],
        notes: vec![
            "Recursion metadata only; no recursion proof evidence.".to_string(),
            "Fixture is a semantic envelope subject, not a gnark circuit.".to_string(),
        ],
    }
}

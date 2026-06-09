//! Deterministic local artifact digest helpers.

use serde::Serialize;
use sha2::{Digest, Sha256};

use crate::error::{Result, ZkBenchError};

use super::artifact::{ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole};

/// Serialize deterministic structs to JSON bytes for hashing.
pub fn canonical_json_bytes<T: Serialize>(value: &T) -> Result<Vec<u8>> {
    serde_json::to_vec(value)
        .map_err(|error| ZkBenchError::serialization("canonical_json_bytes", error.to_string()))
}

/// Compute SHA-256 over raw bytes.
pub fn compute_artifact_digest_bytes(
    bytes: &[u8],
    kind: Option<ArtifactKind>,
    role: Option<ArtifactRole>,
) -> ArtifactDigest {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    let digest = hasher.finalize();
    ArtifactDigest {
        algorithm: ArtifactDigestAlgorithm::Sha256,
        hex_digest: hex::encode(digest),
        byte_len: bytes.len(),
        kind,
        role,
    }
}

/// Compute SHA-256 over deterministic JSON bytes.
pub fn compute_artifact_digest<T: Serialize>(
    value: &T,
    kind: Option<ArtifactKind>,
    role: Option<ArtifactRole>,
) -> Result<ArtifactDigest> {
    let bytes = canonical_json_bytes(value)?;
    Ok(compute_artifact_digest_bytes(&bytes, kind, role))
}

/// Compute SHA-256 over pretty JSON text or compact JSON text bytes.
pub fn compute_artifact_digest_for_json(
    json: &str,
    kind: Option<ArtifactKind>,
    role: Option<ArtifactRole>,
) -> ArtifactDigest {
    compute_artifact_digest_bytes(json.as_bytes(), kind, role)
}

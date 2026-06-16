//! Deterministic local artifact digest helpers.
//!
//! # Digest stability policy (version-locked)
//!
//! Digest input bytes are produced by `serde_json::to_vec`, which emits struct
//! fields in **declaration order**. This is deterministic for a fixed version
//! of this crate, but it is NOT canonical JSON: renaming, reordering, adding,
//! or removing a serialized field on any digested type changes the byte
//! stream and therefore invalidates every previously computed digest and
//! ledger chain.
//!
//! Policy: digests are version-locked to the schema version strings carried by
//! the ledgers (e.g. `EvidenceLedgerVersion`). Any change to a digested type's
//! serialized shape MUST bump the corresponding schema version string, and
//! ledgers from older versions must be treated as read-only historical
//! artifacts (re-validate with the code version that wrote them) rather than
//! appended to. Do not mix entries produced by different schema versions in
//! one chain.

use serde::Serialize;
use sha2::{Digest, Sha256};

use crate::error::{Result, ZkBenchError};

use super::artifact::{ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole};

/// Serialize deterministic structs to JSON bytes for hashing.
///
/// Deterministic for a fixed crate version only; see the module-level digest
/// stability policy before changing any serialized type that gets digested.
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

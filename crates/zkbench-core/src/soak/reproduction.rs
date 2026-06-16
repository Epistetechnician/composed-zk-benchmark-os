//! Reproduction bundle attachment for local failure packs.
//!
//! A reproduction bundle is a sidecar artifact written inside an already
//! written local benchmark pack. It carries the failure corpus entries that
//! produced the pack so a failure can be replayed locally from the pack alone.
//! Bundles are reproduction aids only and never evidence.

use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{
    compute_artifact_digest, ArtifactDigest, ArtifactKind, ArtifactRole, ClaimBoundary,
};
use crate::pack::BenchmarkPackReader;

use super::artifact_layout::write_json;
use super::failure_corpus::FailureCorpusEntry;

/// Relative path of the bundle inside a pack.
pub const REPRODUCTION_BUNDLE_RELATIVE_PATH: &str = "reproduction/reproduction_bundle.json";

/// Reproduction bundle stored inside a local pack.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReproductionBundle {
    /// Bundle id.
    pub bundle_id: String,
    /// Bundle version.
    pub bundle_version: String,
    /// Pack id the bundle is attached to.
    pub pack_id: String,
    /// Failure corpus entries.
    pub entries: Vec<FailureCorpusEntry>,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Attachment metadata returned after writing a bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReproductionBundleAttachment {
    /// Bundle id.
    pub bundle_id: String,
    /// Pack id.
    pub pack_id: String,
    /// Relative path inside the pack.
    pub relative_path: String,
    /// Bundle digest.
    pub digest: ArtifactDigest,
    /// Entry count.
    pub entry_count: usize,
    /// Claim boundary.
    pub claim_boundary: ClaimBoundary,
}

/// Validate a reproduction bundle.
pub fn validate_reproduction_bundle(bundle: &ReproductionBundle) -> Result<()> {
    if bundle.claim_boundary != ClaimBoundary::Level0DesignNote {
        return Err(ZkBenchError::soak(
            "soak.reproduction_bundle.claim_boundary",
            "reproduction bundles must remain Level0DesignNote",
        ));
    }
    if bundle.entries.is_empty() {
        return Err(ZkBenchError::soak(
            "soak.reproduction_bundle.entries",
            "reproduction bundles must carry at least one failure corpus entry",
        ));
    }
    for (entry_index, entry) in bundle.entries.iter().enumerate() {
        if entry.claim_boundary != ClaimBoundary::Level0DesignNote
            || entry.reproduction_manifest.claim_boundary != ClaimBoundary::Level0DesignNote
        {
            return Err(ZkBenchError::soak(
                format!("soak.reproduction_bundle.entries[{entry_index}].claim_boundary"),
                "reproduction bundle entries must remain Level0DesignNote",
            ));
        }
    }
    Ok(())
}

/// Attach a reproduction bundle to an already written local pack.
///
/// The bundle is written as a sidecar file under the pack root; the pack
/// manifest is left untouched so existing digests remain valid.
pub fn attach_reproduction_bundle_to_pack(
    pack_root: impl AsRef<Path>,
    entries: &[FailureCorpusEntry],
) -> Result<ReproductionBundleAttachment> {
    let pack_root = pack_root.as_ref();
    let reader = BenchmarkPackReader::read(pack_root)?;
    let pack_id = reader.manifest().id.clone();
    let bundle = ReproductionBundle {
        bundle_id: format!("reproduction_bundle_{pack_id}"),
        bundle_version: "phase-l-reproduction-bundle-v0".to_string(),
        pack_id: pack_id.clone(),
        entries: entries.to_vec(),
        claim_boundary: ClaimBoundary::Level0DesignNote,
        notes: vec![
            "Reproduction bundles are local reproduction aids, not accepted evidence.".to_string(),
            "No external backend was invoked to produce this bundle.".to_string(),
        ],
    };
    validate_reproduction_bundle(&bundle)?;
    write_json(pack_root.join(REPRODUCTION_BUNDLE_RELATIVE_PATH), &bundle)?;
    let validation = BenchmarkPackReader::read(pack_root)?.validate();
    if !validation.valid {
        return Err(ZkBenchError::soak(
            "soak.reproduction_bundle.pack_validation",
            format!(
                "pack validation failed after bundle attachment: {:?}",
                validation.errors
            ),
        ));
    }
    let digest = compute_artifact_digest(
        &bundle,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    )?;
    Ok(ReproductionBundleAttachment {
        bundle_id: bundle.bundle_id,
        pack_id,
        relative_path: REPRODUCTION_BUNDLE_RELATIVE_PATH.to_string(),
        digest,
        entry_count: entries.len(),
        claim_boundary: ClaimBoundary::Level0DesignNote,
    })
}

/// Read a reproduction bundle back from a pack.
pub fn read_reproduction_bundle_from_pack(
    pack_root: impl AsRef<Path>,
) -> Result<ReproductionBundle> {
    let path = pack_root.as_ref().join(REPRODUCTION_BUNDLE_RELATIVE_PATH);
    let bytes = fs::read(&path)
        .map_err(|error| ZkBenchError::soak(path.display().to_string(), error.to_string()))?;
    let bundle: ReproductionBundle = serde_json::from_slice(&bytes).map_err(|error| {
        ZkBenchError::deserialization("read_reproduction_bundle_from_pack", error.to_string())
    })?;
    validate_reproduction_bundle(&bundle)?;
    Ok(bundle)
}

//! Fail-closed custody handoff preflight for a future fresh Astral actor.
//!
//! This contract records only typed custody metadata. It does not load a
//! model, open an assessment, capture telemetry, or authorize execution.

use serde::{Deserialize, Serialize};

use crate::evidence::{ArtifactDigest, ArtifactDigestAlgorithm, ClaimBoundary};

/// State slice governed by this contract.
pub const ASTRAL_FRESH_ACTOR_CUSTODY_HANDOFF_STATE_SLICE: &str =
    "astral-fresh-actor-custody-handoff-v34";

/// Maximum claim boundary for a custody handoff preflight.
pub const ASTRAL_FRESH_ACTOR_CUSTODY_HANDOFF_CLAIM_BOUNDARY: ClaimBoundary =
    ClaimBoundary::Level0DesignNote;

/// Actor identities reserved by prior Astral protocols.
pub const RESERVED_ASTRAL_ACTOR_IDS: &[&str] = &["V22", "V23", "V24", "V25"];

/// Materials that must never be retained in a custody handoff.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ForbiddenCustodyMaterial {
    /// Raw reasoning or activation trace.
    RawTrace,
    /// Credential, token, or secret.
    Credential,
    /// Personally identifying information.
    Pii,
    /// Opaque provider signature or envelope.
    OpaqueSignature,
    /// Provider artifact not reduced to typed metadata.
    ProviderArtifact,
}

/// Typed custody metadata for a prospective fresh actor.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct FreshActorCustodyHandoff {
    /// Stable handoff identifier.
    pub id: String,
    /// Required state slice.
    pub state_slice: String,
    /// Fresh actor identifier.
    pub actor_id: String,
    /// Digest of the actor/checkpoint bytes.
    pub actor_digest: ArtifactDigest,
    /// Digest of the source/archive bytes.
    pub source_archive_digest: ArtifactDigest,
    /// Digest of the runtime bytes.
    pub runtime_digest: ArtifactDigest,
    /// Digest of the launcher bytes.
    pub launcher_digest: ArtifactDigest,
    /// Digest of the launcher argument plan.
    pub launcher_argv_digest: ArtifactDigest,
    /// Digest of the frozen fit/tune/assessment split manifest.
    pub split_manifest_digest: ArtifactDigest,
    /// Validator identity or version, not a credential.
    pub validator_id: String,
    /// Digest of the planned artifact root.
    pub artifact_root: ArtifactDigest,
    /// Claim boundary of this preflight record.
    pub claim_boundary: ClaimBoundary,
    /// Whether custody metadata is complete.
    pub custody_complete: bool,
    /// Assessment execution must remain unopened at this boundary.
    pub assessment_opened: bool,
    /// Explicitly rejected material markers.
    #[serde(default)]
    pub forbidden_materials: Vec<ForbiddenCustodyMaterial>,
}

/// Validation issue for a custody handoff.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FreshActorCustodyValidationIssue {
    /// Field path.
    pub path: String,
    /// Human-readable failure.
    pub message: String,
}

/// Validation result for a custody handoff.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FreshActorCustodyValidation {
    /// True only when all fail-closed checks pass.
    pub valid: bool,
    /// Deterministic validation issues.
    pub issues: Vec<FreshActorCustodyValidationIssue>,
}

/// Validate a prospective fresh-actor custody handoff.
pub fn validate_fresh_actor_custody_handoff(
    handoff: &FreshActorCustodyHandoff,
) -> FreshActorCustodyValidation {
    let mut issues = Vec::new();
    require_nonempty(&handoff.id, "id", &mut issues);
    require_nonempty(&handoff.actor_id, "actor_id", &mut issues);
    require_nonempty(&handoff.validator_id, "validator_id", &mut issues);

    if handoff.state_slice != ASTRAL_FRESH_ACTOR_CUSTODY_HANDOFF_STATE_SLICE {
        issues.push(issue(
            "state_slice",
            "handoff state slice does not match the V34 contract",
        ));
    }
    if RESERVED_ASTRAL_ACTOR_IDS.contains(&handoff.actor_id.as_str()) {
        issues.push(issue(
            "actor_id",
            "actor identity is reserved by an earlier Astral protocol",
        ));
    }
    if handoff.claim_boundary != ASTRAL_FRESH_ACTOR_CUSTODY_HANDOFF_CLAIM_BOUNDARY {
        issues.push(issue(
            "claim_boundary",
            "custody handoffs are design-only and must remain Level0DesignNote",
        ));
    }
    if !handoff.custody_complete {
        issues.push(issue(
            "custody_complete",
            "all source, runtime, launcher, split, validator, and artifact-root metadata is required",
        ));
    }
    if handoff.assessment_opened {
        issues.push(issue(
            "assessment_opened",
            "custody preflight cannot open model execution or assessment",
        ));
    }
    if !handoff.forbidden_materials.is_empty() {
        issues.push(issue(
            "forbidden_materials",
            "raw traces, credentials, PII, opaque signatures, and provider artifacts are forbidden",
        ));
    }

    for (path, digest) in [
        ("actor_digest", &handoff.actor_digest),
        ("source_archive_digest", &handoff.source_archive_digest),
        ("runtime_digest", &handoff.runtime_digest),
        ("launcher_digest", &handoff.launcher_digest),
        ("launcher_argv_digest", &handoff.launcher_argv_digest),
        ("split_manifest_digest", &handoff.split_manifest_digest),
        ("artifact_root", &handoff.artifact_root),
    ] {
        validate_digest(path, digest, &mut issues);
    }

    FreshActorCustodyValidation {
        valid: issues.is_empty(),
        issues,
    }
}

fn require_nonempty(value: &str, path: &str, issues: &mut Vec<FreshActorCustodyValidationIssue>) {
    if value.trim().is_empty() {
        issues.push(issue(path, "required value is empty"));
    }
}

fn validate_digest(
    path: &str,
    digest: &ArtifactDigest,
    issues: &mut Vec<FreshActorCustodyValidationIssue>,
) {
    if digest.algorithm != ArtifactDigestAlgorithm::Sha256 {
        issues.push(issue(path, "custody digests must use SHA-256"));
    }
    if digest.byte_len == 0 {
        issues.push(issue(path, "custody digest byte length must be positive"));
    }
    let valid_hex = digest.hex_digest.len() == 64
        && digest
            .hex_digest
            .chars()
            .all(|character| character.is_ascii_digit() || ('a'..='f').contains(&character));
    if !valid_hex {
        issues.push(issue(
            path,
            "custody digest must be exactly 64 lowercase hexadecimal characters",
        ));
    }
}

fn issue(path: &str, message: &str) -> FreshActorCustodyValidationIssue {
    FreshActorCustodyValidationIssue {
        path: path.to_string(),
        message: message.to_string(),
    }
}

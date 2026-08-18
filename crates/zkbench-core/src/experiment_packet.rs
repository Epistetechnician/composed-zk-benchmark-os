//! Durable local materialization for one validated experiment composition packet.
//!
//! State slice: `benchmark-os-experiment-packet-materialization-readback-v1`.
//! Write-safety extension: `benchmark-os-experiment-packet-write-symlink-preflight-v1`.
//! Integrity extension: `benchmark-os-experiment-packet-canonical-digest-sidecar-v1`.
//! Generic transport extension: `benchmark-os-plugin-agnostic-packet-materialization-readback-v1`.
//! Output handoff validation slice: `benchmark-os-plugin-composition-output-handoff-validation-v1`.
//! Packet output handoff validation slice: `benchmark-os-experiment-packet-output-handoff-validation-v1`.
//! Canonical typed transport slice: `benchmark-os-experiment-packet-canonical-typed-transport-v1`.
//!
//! This module writes only a caller-owned, declared-file packet containing the
//! canonical inner experiment bundle, composition config, outer observability
//! bundle, and their integrity sidecars. It does not execute experiments,
//! invoke external processes, mutate the accepted Evidence Ledger, or raise
//! the local claim ceiling.

use std::collections::BTreeSet;
use std::fs;
use std::path::{Component, Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{
    compute_artifact_digest_bytes, ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind,
    ArtifactRole, ClaimBoundary,
};
use crate::experiment::{
    compute_experiment_bundle_digest, serialize_experiment_bundle_json, validate_experiment_bundle,
    ExperimentBundle,
};
use crate::experiment_observability::{
    compute_experiment_artifact_bundle_digest, deserialize_experiment_artifact_bundle_json,
    serialize_experiment_artifact_bundle_json, serialize_local_json_composition_config_json,
    validate_local_json_artifact_projection, validate_serialized_local_json_composition_transport,
    ExperimentArtifactBundle, LocalJsonCompositionConfig,
};
use crate::experiment_plugin_composition::{
    deserialize_plugin_composition_config_json, serialize_plugin_composition_config_json,
    PluginCompositionConfig, PluginCompositionOutput, ValidatedPluginCompositionOutput,
};

/// Packet schema version.
pub const EXPERIMENT_PACKET_SCHEMA_VERSION: &str = "benchmark-os-experiment-packet-v1";

/// Packet manifest path below the caller-owned output root.
pub const EXPERIMENT_PACKET_MANIFEST_PATH: &str = "packet-manifest.json";

/// Canonical inner experiment bundle path below the caller-owned output root.
pub const EXPERIMENT_PACKET_INNER_BUNDLE_PATH: &str = "artifacts/inner-experiment-bundle.json";

/// Canonical composition config path below the caller-owned output root.
pub const EXPERIMENT_PACKET_COMPOSITION_CONFIG_PATH: &str = "artifacts/composition-config.json";

/// Canonical outer observability bundle path below the caller-owned output root.
pub const EXPERIMENT_PACKET_OUTER_BUNDLE_PATH: &str = "artifacts/outer-observability-bundle.json";

/// Packet manifest digest sidecar path.
pub const EXPERIMENT_PACKET_MANIFEST_DIGEST_PATH: &str = "digests/packet-manifest-json.sha256";

/// Inner bundle digest sidecar path.
pub const EXPERIMENT_PACKET_INNER_BUNDLE_DIGEST_PATH: &str =
    "digests/inner-experiment-bundle-json.sha256";

/// Composition config digest sidecar path.
pub const EXPERIMENT_PACKET_COMPOSITION_CONFIG_DIGEST_PATH: &str =
    "digests/composition-config-json.sha256";

/// Outer observability bundle digest sidecar path.
pub const EXPERIMENT_PACKET_OUTER_BUNDLE_DIGEST_PATH: &str =
    "digests/outer-observability-bundle-json.sha256";

/// One canonical JSON file declared by the packet manifest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentPacketFileRef {
    /// Portable path relative to the packet output root.
    pub relative_path: String,
    /// Digest over the exact file bytes.
    pub digest: ArtifactDigest,
}

/// The interface implemented by every composition adapter that can be durably
/// materialized as an experiment packet.
///
/// Implementations own their canonical config serializer and semantic
/// cross-artifact validator. The packet module owns the shared manifest,
/// sidecars, path safety, overwrite policy, and filesystem readback.
pub trait ExperimentPacketComposition: Clone + PartialEq + Eq {
    /// Serialize the adapter's canonical composition config.
    fn serialize_config_json(&self) -> Result<String>;

    /// Deserialize one adapter config without trusting it until transport
    /// and cross-artifact validation complete.
    fn deserialize_config_json(json: &str) -> Result<Self>;

    /// Validate canonical inner/config/outer transport bytes as one packet.
    fn validate_serialized_transport(
        inner_json: &str,
        config_json: &str,
        outer_json: &str,
    ) -> Result<(ExperimentBundle, Self, ExperimentArtifactBundle)>;

    /// Validate typed config identity and all adapter-specific bindings.
    fn validate_against_outer(
        &self,
        inner: &ExperimentBundle,
        outer: &ExperimentArtifactBundle,
    ) -> Result<()>;

    /// Return the outer experiment identity bound into the config.
    fn experiment_id(&self) -> &str;

    /// Return the outer run identity bound into the config.
    fn run_id(&self) -> &str;
}

/// The three typed transport artifacts that form one composition packet.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExperimentPacket<C = LocalJsonCompositionConfig>
where
    C: ExperimentPacketComposition,
{
    /// Validated inner experiment bundle.
    pub inner: ExperimentBundle,
    /// Validated canonical composition config.
    pub composition_config: C,
    /// Validated outer observability bundle.
    pub outer: ExperimentArtifactBundle,
}

/// Generic packet specialized to the plugin-agnostic composition adapter.
pub type PluginCompositionPacket = ExperimentPacket<PluginCompositionConfig>;

/// Local JSON compatibility packet specialized to its historical adapter.
pub type LocalJsonExperimentPacket = ExperimentPacket<LocalJsonCompositionConfig>;

/// Durable manifest for one local experiment composition packet.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExperimentPacketManifest {
    /// Packet schema version.
    pub schema_version: String,
    /// Outer experiment identity.
    pub experiment_id: String,
    /// Outer run identity.
    pub run_id: String,
    /// Inner bundle identity.
    pub inner_bundle_id: String,
    /// Inner bundle file and digest.
    pub inner_bundle: ExperimentPacketFileRef,
    /// Composition config file and digest.
    pub composition_config: ExperimentPacketFileRef,
    /// Outer observability bundle file and digest.
    pub outer_bundle: ExperimentPacketFileRef,
    /// Packet claim ceiling.
    pub claim_boundary: ClaimBoundary,
    /// Required non-claims for durable local packaging.
    pub limitations: Vec<String>,
}

/// Typed result returned after materialization or strict readback.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExperimentPacketOutput<C = LocalJsonCompositionConfig>
where
    C: ExperimentPacketComposition,
{
    /// Validated packet manifest.
    pub manifest: ExperimentPacketManifest,
    /// Digest over the packet manifest JSON bytes.
    pub manifest_digest: ArtifactDigest,
    /// Validated typed packet.
    pub packet: ExperimentPacket<C>,
}

/// Invariant-bearing packet output handoff.
///
/// The fields remain private so manifest, digest, and packet identity cannot
/// be separated after the packet module has validated their consistency.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValidatedExperimentPacketOutput<C = LocalJsonCompositionConfig>
where
    C: ExperimentPacketComposition,
{
    output: ExperimentPacketOutput<C>,
}

/// Generic plugin-composition packet output handoff.
pub type ValidatedPluginCompositionPacketOutput =
    ValidatedExperimentPacketOutput<PluginCompositionConfig>;

/// Local JSON compatibility packet output handoff.
pub type ValidatedLocalJsonExperimentPacketOutput =
    ValidatedExperimentPacketOutput<LocalJsonCompositionConfig>;

impl<C: ExperimentPacketComposition> ExperimentPacketOutput<C> {
    /// Validate the public compatibility shape before entering a typed seam.
    pub fn into_validated(self) -> Result<ValidatedExperimentPacketOutput<C>> {
        ValidatedExperimentPacketOutput::new(self.manifest, self.manifest_digest, self.packet)
    }
}

impl<C: ExperimentPacketComposition> ValidatedExperimentPacketOutput<C> {
    /// Validate and bind one complete packet output handoff.
    pub fn new(
        manifest: ExperimentPacketManifest,
        manifest_digest: ArtifactDigest,
        packet: ExperimentPacket<C>,
    ) -> Result<Self> {
        Self::from_output(ExperimentPacketOutput {
            manifest,
            manifest_digest,
            packet,
        })
    }

    /// Validate and bind one historical public packet output shape.
    pub fn from_output(output: ExperimentPacketOutput<C>) -> Result<Self> {
        validate_packet_output_parts(&output.manifest, &output.manifest_digest, &output.packet)?;
        Ok(Self { output })
    }

    /// Borrow the complete validated output for read-only compatibility APIs.
    pub fn as_output(&self) -> &ExperimentPacketOutput<C> {
        &self.output
    }

    /// Borrow the validated packet manifest.
    pub fn manifest(&self) -> &ExperimentPacketManifest {
        &self.output.manifest
    }

    /// Borrow the digest over the validated manifest bytes.
    pub fn manifest_digest(&self) -> &ArtifactDigest {
        &self.output.manifest_digest
    }

    /// Borrow the validated typed packet.
    pub fn packet(&self) -> &ExperimentPacket<C> {
        &self.output.packet
    }

    /// Decompose the validated handoff after validation has already occurred.
    pub fn into_parts(
        self,
    ) -> (
        ExperimentPacketManifest,
        ArtifactDigest,
        ExperimentPacket<C>,
    ) {
        let output = self.output;
        (output.manifest, output.manifest_digest, output.packet)
    }

    /// Return the historical public packet output shape.
    pub fn into_legacy(self) -> ExperimentPacketOutput<C> {
        self.output
    }

    /// Return the historical public packet output shape.
    pub fn into_output(self) -> ExperimentPacketOutput<C> {
        self.output
    }
}

/// Generic plugin-composition packet output.
pub type PluginCompositionPacketOutput = ExperimentPacketOutput<PluginCompositionConfig>;

/// Local JSON compatibility packet output.
pub type LocalJsonExperimentPacketOutput = ExperimentPacketOutput<LocalJsonCompositionConfig>;

/// Convert one generic in-memory composition run into a durable packet value.
impl From<PluginCompositionOutput> for PluginCompositionPacket {
    fn from(output: PluginCompositionOutput) -> Self {
        Self {
            inner: output.inner,
            composition_config: output.config,
            outer: output.outer,
        }
    }
}

impl From<ValidatedPluginCompositionOutput> for PluginCompositionPacket {
    fn from(output: ValidatedPluginCompositionOutput) -> Self {
        let (inner, composition_config, outer) = output.into_parts();
        Self {
            inner,
            composition_config,
            outer,
        }
    }
}

impl ValidatedPluginCompositionOutput {
    /// Convert the invariant-bearing handoff into a packet without rechecking.
    pub fn into_packet(self) -> PluginCompositionPacket {
        self.into()
    }
}

impl PluginCompositionOutput {
    /// Convert a composition output after revalidating its complete handoff.
    ///
    /// The infallible `From` implementation remains for source compatibility;
    /// active packet-job orchestration uses this fallible Interface so public
    /// field drift cannot cross into packet materialization silently.
    pub fn try_into_packet(self) -> Result<PluginCompositionPacket> {
        Ok(self.into_validated()?.into_packet())
    }
}

impl ExperimentPacketComposition for LocalJsonCompositionConfig {
    fn serialize_config_json(&self) -> Result<String> {
        serialize_local_json_composition_config_json(self)
    }

    fn deserialize_config_json(json: &str) -> Result<Self> {
        crate::experiment_observability::deserialize_local_json_composition_config_json(json)
    }

    fn validate_serialized_transport(
        inner_json: &str,
        config_json: &str,
        outer_json: &str,
    ) -> Result<(ExperimentBundle, Self, ExperimentArtifactBundle)> {
        validate_serialized_local_json_composition_transport(inner_json, config_json, outer_json)
    }

    fn validate_against_outer(
        &self,
        inner: &ExperimentBundle,
        outer: &ExperimentArtifactBundle,
    ) -> Result<()> {
        validate_local_json_artifact_projection(inner, outer, self)
    }

    fn experiment_id(&self) -> &str {
        &self.experiment_id
    }

    fn run_id(&self) -> &str {
        &self.run_id
    }
}

impl ExperimentPacketComposition for PluginCompositionConfig {
    fn serialize_config_json(&self) -> Result<String> {
        serialize_plugin_composition_config_json(self)
    }

    fn deserialize_config_json(json: &str) -> Result<Self> {
        deserialize_plugin_composition_config_json(json)
    }

    fn validate_serialized_transport(
        inner_json: &str,
        config_json: &str,
        outer_json: &str,
    ) -> Result<(ExperimentBundle, Self, ExperimentArtifactBundle)> {
        let inner = crate::experiment::deserialize_experiment_bundle_json(inner_json)?;
        let inner_validation = validate_experiment_bundle(&inner);
        if !inner_validation.valid {
            return Err(ZkBenchError::validation(
                "plugin_composition_packet.inner_bundle",
                format!("inner bundle is invalid: {:?}", inner_validation.issues),
            ));
        }
        if serialize_experiment_bundle_json(&inner)? != inner_json {
            return Err(ZkBenchError::validation(
                "plugin_composition_packet.inner_bytes",
                "inner bundle bytes are not the canonical serialization",
            ));
        }
        let outer = deserialize_experiment_artifact_bundle_json(outer_json)?;
        if serialize_experiment_artifact_bundle_json(&outer)? != outer_json {
            return Err(ZkBenchError::validation(
                "plugin_composition_packet.outer_bytes",
                "outer bundle bytes are not the canonical serialization",
            ));
        }
        let config = deserialize_plugin_composition_config_json(config_json)?;
        if config.serialize_config_json()? != config_json {
            return Err(ZkBenchError::validation(
                "plugin_composition_packet.config_bytes",
                "composition config bytes are not the canonical serialization",
            ));
        }
        config.validate_against_outer(&inner, &outer)?;
        Ok((inner, config, outer))
    }

    fn validate_against_outer(
        &self,
        inner: &ExperimentBundle,
        outer: &ExperimentArtifactBundle,
    ) -> Result<()> {
        PluginCompositionConfig::validate_against_outer(self, inner, outer)
    }

    fn experiment_id(&self) -> &str {
        &self.experiment_id
    }

    fn run_id(&self) -> &str {
        &self.run_id
    }
}

/// Required limitations for a local experiment packet.
pub fn required_experiment_packet_limitations() -> Vec<&'static str> {
    vec![
        "Local experiment packets are durable metadata packaging, not official benchmark evidence.",
        "Local experiment packets do not mutate the accepted Evidence Ledger.",
        "Local experiment packets do not authorize external replay or runtime execution.",
        "Local experiment packets do not establish ZK backend performance.",
        "Local experiment packets do not create Level2+ evidence.",
        "Local experiment packets do not establish interpretability, causal validity, or introspection.",
    ]
}

/// Serialize the packet manifest using deterministic compact JSON.
pub fn serialize_experiment_packet_manifest_json(
    manifest: &ExperimentPacketManifest,
) -> Result<String> {
    validate_experiment_packet_manifest(manifest)?;
    serde_json::to_string(manifest).map_err(|error| {
        ZkBenchError::serialization("experiment_packet.manifest", error.to_string())
    })
}

/// Deserialize and validate one packet manifest.
pub fn deserialize_experiment_packet_manifest_json(json: &str) -> Result<ExperimentPacketManifest> {
    let manifest: ExperimentPacketManifest = serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("experiment_packet.manifest", error.to_string())
    })?;
    validate_experiment_packet_manifest(&manifest)?;
    Ok(manifest)
}

/// Compute the digest over canonical packet manifest bytes.
pub fn compute_experiment_packet_manifest_digest(
    manifest: &ExperimentPacketManifest,
) -> Result<ArtifactDigest> {
    let json = serialize_experiment_packet_manifest_json(manifest)?;
    Ok(packet_digest(json.as_bytes()))
}

/// Validate the packet manifest's fixed schema, paths, digests, and claim ceiling.
pub fn validate_experiment_packet_manifest(manifest: &ExperimentPacketManifest) -> Result<()> {
    require_text(&manifest.schema_version, "packet_manifest.schema_version")?;
    if manifest.schema_version != EXPERIMENT_PACKET_SCHEMA_VERSION {
        return Err(ZkBenchError::validation(
            "packet_manifest.schema_version",
            format!(
                "expected {EXPERIMENT_PACKET_SCHEMA_VERSION}, got {}",
                manifest.schema_version
            ),
        ));
    }
    require_text(&manifest.experiment_id, "packet_manifest.experiment_id")?;
    require_text(&manifest.run_id, "packet_manifest.run_id")?;
    require_text(&manifest.inner_bundle_id, "packet_manifest.inner_bundle_id")?;
    if manifest.claim_boundary != ClaimBoundary::Level0DesignNote {
        return Err(ZkBenchError::ClaimBoundary {
            message: "experiment packet materialization remains Level0DesignNote".to_string(),
        });
    }
    let expected = [
        (
            "packet_manifest.inner_bundle.relative_path",
            &manifest.inner_bundle,
            EXPERIMENT_PACKET_INNER_BUNDLE_PATH,
        ),
        (
            "packet_manifest.composition_config.relative_path",
            &manifest.composition_config,
            EXPERIMENT_PACKET_COMPOSITION_CONFIG_PATH,
        ),
        (
            "packet_manifest.outer_bundle.relative_path",
            &manifest.outer_bundle,
            EXPERIMENT_PACKET_OUTER_BUNDLE_PATH,
        ),
    ];
    let mut paths = BTreeSet::new();
    for (path, file, expected_path) in expected {
        if file.relative_path != expected_path {
            return Err(ZkBenchError::validation(
                path,
                format!("expected {expected_path}, got {}", file.relative_path),
            ));
        }
        validate_relative_path(&file.relative_path)?;
        if !paths.insert(file.relative_path.clone()) {
            return Err(ZkBenchError::validation(
                path,
                "packet file path is duplicated",
            ));
        }
        validate_packet_digest(&file.digest, path.replace("relative_path", "digest"))?;
    }
    for required in required_experiment_packet_limitations() {
        if !manifest
            .limitations
            .iter()
            .any(|limitation| limitation == required)
        {
            return Err(ZkBenchError::validation(
                "packet_manifest.limitations",
                format!("missing required limitation: {required}"),
            ));
        }
    }
    Ok(())
}

/// Materialize a validated local JSON packet through the invariant-bearing
/// typed transport path.
pub fn write_experiment_packet_outputs_validated(
    output_root: impl AsRef<Path>,
    packet: &LocalJsonExperimentPacket,
    overwrite: bool,
    protected_paths: &[PathBuf],
) -> Result<ValidatedLocalJsonExperimentPacketOutput> {
    write_experiment_packet_outputs_typed(output_root, packet, overwrite, protected_paths)
}

/// Materialize a generic plugin-composition packet through the
/// invariant-bearing typed transport path.
pub fn write_plugin_composition_packet_outputs_validated(
    output_root: impl AsRef<Path>,
    packet: &PluginCompositionPacket,
    overwrite: bool,
    protected_paths: &[PathBuf],
) -> Result<ValidatedPluginCompositionPacketOutput> {
    write_experiment_packet_outputs_typed(output_root, packet, overwrite, protected_paths)
}

/// Materialize a validated three-artifact packet under a caller-owned root.
///
/// This historical API remains a compatibility Adapter over the canonical
/// typed transport path.
pub fn write_experiment_packet_outputs(
    output_root: impl AsRef<Path>,
    packet: &ExperimentPacket,
    overwrite: bool,
    protected_paths: &[PathBuf],
) -> Result<ExperimentPacketOutput> {
    write_experiment_packet_outputs_validated(output_root, packet, overwrite, protected_paths)
        .map(ValidatedExperimentPacketOutput::into_legacy)
}

/// Materialize a generic plugin-composition packet under a caller-owned root.
pub fn write_plugin_composition_packet_outputs(
    output_root: impl AsRef<Path>,
    packet: &PluginCompositionPacket,
    overwrite: bool,
    protected_paths: &[PathBuf],
) -> Result<ExperimentPacketOutput<PluginCompositionConfig>> {
    write_plugin_composition_packet_outputs_validated(
        output_root,
        packet,
        overwrite,
        protected_paths,
    )
    .map(ValidatedExperimentPacketOutput::into_legacy)
}

/// Build the canonical typed output for a generic plugin-composition packet
/// without publishing it to a filesystem.
pub(crate) fn build_plugin_composition_packet_output(
    packet: &PluginCompositionPacket,
) -> Result<ValidatedPluginCompositionPacketOutput> {
    build_experiment_packet_output_typed(packet)
}

fn write_experiment_packet_outputs_typed<C: ExperimentPacketComposition>(
    output_root: impl AsRef<Path>,
    packet: &ExperimentPacket<C>,
    overwrite: bool,
    protected_paths: &[PathBuf],
) -> Result<ValidatedExperimentPacketOutput<C>> {
    let output = build_experiment_packet_output_typed(packet)?;
    let (inner_json, config_json, outer_json) = serialize_packet(packet)?;
    write_experiment_packet_bytes_typed(
        output_root,
        &inner_json,
        &config_json,
        &outer_json,
        output,
        overwrite,
        protected_paths,
    )
}

fn build_experiment_packet_output_typed<C: ExperimentPacketComposition>(
    packet: &ExperimentPacket<C>,
) -> Result<ValidatedExperimentPacketOutput<C>> {
    let (inner_json, config_json, outer_json) = serialize_packet(packet)?;
    let manifest = build_packet_manifest(
        &packet.inner,
        &packet.composition_config,
        &inner_json,
        &config_json,
        &outer_json,
    )?;
    let manifest_json = serialize_experiment_packet_manifest_json(&manifest)?;
    let manifest_digest = packet_digest(manifest_json.as_bytes());
    ValidatedExperimentPacketOutput::new(manifest, manifest_digest, packet.clone())
}

fn write_experiment_packet_bytes_typed<C: ExperimentPacketComposition>(
    output_root: impl AsRef<Path>,
    inner_json: &str,
    config_json: &str,
    outer_json: &str,
    output: ValidatedExperimentPacketOutput<C>,
    overwrite: bool,
    protected_paths: &[PathBuf],
) -> Result<ValidatedExperimentPacketOutput<C>> {
    let output_root = output_root.as_ref();
    validate_output_root(output_root, protected_paths)?;
    let manifest_json = serialize_experiment_packet_manifest_json(output.manifest())?;

    if output_root.exists() {
        reject_symlink(output_root)?;
        if !output_root.is_dir() {
            return Err(packet_io_error(
                output_root.display().to_string(),
                "packet output root is an existing file",
            ));
        }
        if directory_has_entries(output_root)? {
            if !overwrite {
                return Err(packet_io_error(
                    output_root.display().to_string(),
                    "packet output root is not empty; explicit overwrite is required",
                ));
            }
            let existing = read_experiment_packet_outputs_typed::<C>(output_root, protected_paths)?;
            if existing.packet() != output.packet() {
                return Err(packet_io_error(
                    output_root.display().to_string(),
                    "existing packet does not match supplied canonical artifacts; refusing repair overwrite",
                ));
            }
        }
    }

    fs::create_dir_all(output_root)
        .map_err(|error| packet_io_error(output_root.display().to_string(), error.to_string()))?;
    write_relative_bytes(
        output_root,
        EXPERIMENT_PACKET_INNER_BUNDLE_PATH,
        inner_json.as_bytes(),
    )?;
    write_relative_bytes(
        output_root,
        EXPERIMENT_PACKET_COMPOSITION_CONFIG_PATH,
        config_json.as_bytes(),
    )?;
    write_relative_bytes(
        output_root,
        EXPERIMENT_PACKET_OUTER_BUNDLE_PATH,
        outer_json.as_bytes(),
    )?;
    write_relative_bytes(
        output_root,
        EXPERIMENT_PACKET_MANIFEST_PATH,
        manifest_json.as_bytes(),
    )?;
    write_digest_sidecar(
        output_root,
        EXPERIMENT_PACKET_INNER_BUNDLE_DIGEST_PATH,
        &output.manifest().inner_bundle.digest,
    )?;
    write_digest_sidecar(
        output_root,
        EXPERIMENT_PACKET_COMPOSITION_CONFIG_DIGEST_PATH,
        &output.manifest().composition_config.digest,
    )?;
    write_digest_sidecar(
        output_root,
        EXPERIMENT_PACKET_OUTER_BUNDLE_DIGEST_PATH,
        &output.manifest().outer_bundle.digest,
    )?;
    let manifest_digest = packet_digest(manifest_json.as_bytes());
    if manifest_digest != *output.manifest_digest() {
        return Err(packet_io_error(
            EXPERIMENT_PACKET_MANIFEST_PATH,
            "canonical packet manifest digest changed before filesystem materialization",
        ));
    }
    write_digest_sidecar(
        output_root,
        EXPERIMENT_PACKET_MANIFEST_DIGEST_PATH,
        &manifest_digest,
    )?;

    Ok(output)
}

/// Read, integrity-check, and semantically validate one local JSON packet
/// through the invariant-bearing typed transport path.
pub fn read_experiment_packet_outputs_validated(
    output_root: impl AsRef<Path>,
    protected_paths: &[PathBuf],
) -> Result<ValidatedLocalJsonExperimentPacketOutput> {
    read_experiment_packet_outputs_typed::<LocalJsonCompositionConfig>(output_root, protected_paths)
}

/// Read, integrity-check, and semantically validate one generic
/// plugin-composition packet through the invariant-bearing typed transport
/// path.
pub fn read_plugin_composition_packet_outputs_validated(
    output_root: impl AsRef<Path>,
    protected_paths: &[PathBuf],
) -> Result<ValidatedPluginCompositionPacketOutput> {
    read_experiment_packet_outputs_typed::<PluginCompositionConfig>(output_root, protected_paths)
}

/// Read, integrity-check, and semantically validate one materialized packet.
///
/// This historical API remains a compatibility Adapter over the canonical
/// typed transport path.
pub fn read_experiment_packet_outputs(
    output_root: impl AsRef<Path>,
    protected_paths: &[PathBuf],
) -> Result<ExperimentPacketOutput> {
    read_experiment_packet_outputs_validated(output_root, protected_paths)
        .map(ValidatedExperimentPacketOutput::into_legacy)
}

/// Read, integrity-check, and semantically validate a generic
/// plugin-composition packet.
pub fn read_plugin_composition_packet_outputs(
    output_root: impl AsRef<Path>,
    protected_paths: &[PathBuf],
) -> Result<ExperimentPacketOutput<PluginCompositionConfig>> {
    read_plugin_composition_packet_outputs_validated(output_root, protected_paths)
        .map(ValidatedExperimentPacketOutput::into_legacy)
}

fn read_experiment_packet_outputs_typed<C: ExperimentPacketComposition>(
    output_root: impl AsRef<Path>,
    protected_paths: &[PathBuf],
) -> Result<ValidatedExperimentPacketOutput<C>> {
    let output_root = output_root.as_ref();
    validate_output_root(output_root, protected_paths)?;
    reject_symlink(output_root)?;
    if !output_root.is_dir() {
        return Err(packet_io_error(
            output_root.display().to_string(),
            "packet output root must be a directory",
        ));
    }
    reject_unexpected_existing_paths(output_root)?;

    let manifest_json = read_utf8(output_root, EXPERIMENT_PACKET_MANIFEST_PATH)?;
    let manifest = deserialize_experiment_packet_manifest_json(&manifest_json)?;
    if serialize_experiment_packet_manifest_json(&manifest)? != manifest_json {
        return Err(packet_io_error(
            EXPERIMENT_PACKET_MANIFEST_PATH,
            "packet manifest is not the canonical serialization",
        ));
    }
    let manifest_digest = packet_digest(manifest_json.as_bytes());
    validate_digest_sidecar(
        output_root,
        EXPERIMENT_PACKET_MANIFEST_DIGEST_PATH,
        &manifest_digest,
    )?;

    let inner_json = read_utf8(output_root, EXPERIMENT_PACKET_INNER_BUNDLE_PATH)?;
    let config_json = read_utf8(output_root, EXPERIMENT_PACKET_COMPOSITION_CONFIG_PATH)?;
    let outer_json = read_utf8(output_root, EXPERIMENT_PACKET_OUTER_BUNDLE_PATH)?;
    validate_payload_digest(
        output_root,
        EXPERIMENT_PACKET_INNER_BUNDLE_PATH,
        EXPERIMENT_PACKET_INNER_BUNDLE_DIGEST_PATH,
        inner_json.as_bytes(),
        &manifest.inner_bundle.digest,
    )?;
    validate_payload_digest(
        output_root,
        EXPERIMENT_PACKET_COMPOSITION_CONFIG_PATH,
        EXPERIMENT_PACKET_COMPOSITION_CONFIG_DIGEST_PATH,
        config_json.as_bytes(),
        &manifest.composition_config.digest,
    )?;
    validate_payload_digest(
        output_root,
        EXPERIMENT_PACKET_OUTER_BUNDLE_PATH,
        EXPERIMENT_PACKET_OUTER_BUNDLE_DIGEST_PATH,
        outer_json.as_bytes(),
        &manifest.outer_bundle.digest,
    )?;

    let (inner_bundle, composition_config, outer_bundle) =
        C::validate_serialized_transport(&inner_json, &config_json, &outer_json)?;
    let canonical_config_json = composition_config.serialize_config_json()?;
    if canonical_config_json != config_json {
        return Err(packet_io_error(
            EXPERIMENT_PACKET_COMPOSITION_CONFIG_PATH,
            "composition config is not the canonical serialization",
        ));
    }
    let expected_manifest = build_packet_manifest(
        &inner_bundle,
        &composition_config,
        &inner_json,
        &config_json,
        &outer_json,
    )?;
    if manifest != expected_manifest {
        return Err(packet_io_error(
            EXPERIMENT_PACKET_MANIFEST_PATH,
            "packet manifest does not match canonical artifact bytes",
        ));
    }
    ValidatedExperimentPacketOutput::new(
        manifest,
        manifest_digest,
        ExperimentPacket {
            inner: inner_bundle,
            composition_config,
            outer: outer_bundle,
        },
    )
}

fn serialize_packet<C: ExperimentPacketComposition>(
    packet: &ExperimentPacket<C>,
) -> Result<(String, String, String)> {
    let inner_validation = validate_experiment_bundle(&packet.inner);
    if !inner_validation.valid {
        return Err(ZkBenchError::validation(
            "experiment_packet.inner_bundle",
            format!(
                "inner local bundle is invalid: {:?}",
                inner_validation.issues
            ),
        ));
    }
    let inner_json = serialize_experiment_bundle_json(&packet.inner)?;
    let config_json = packet.composition_config.serialize_config_json()?;
    let outer_json = serialize_experiment_artifact_bundle_json(&packet.outer)?;
    let (inner, config, outer) =
        C::validate_serialized_transport(&inner_json, &config_json, &outer_json)?;
    if inner != packet.inner || config != packet.composition_config || outer != packet.outer {
        return Err(packet_io_error(
            "experiment_packet",
            "typed packet does not satisfy its canonical cross-artifact transport contract",
        ));
    }
    Ok((inner_json, config_json, outer_json))
}

fn validate_packet_output_parts<C: ExperimentPacketComposition>(
    manifest: &ExperimentPacketManifest,
    manifest_digest: &ArtifactDigest,
    packet: &ExperimentPacket<C>,
) -> Result<()> {
    let (inner_json, config_json, outer_json) = serialize_packet(packet)?;
    let expected_manifest = build_packet_manifest(
        &packet.inner,
        &packet.composition_config,
        &inner_json,
        &config_json,
        &outer_json,
    )?;
    if manifest != &expected_manifest {
        return Err(packet_io_error(
            "experiment_packet_output.manifest",
            "packet output manifest does not match canonical artifact bytes",
        ));
    }
    let expected_manifest_json = serialize_experiment_packet_manifest_json(&expected_manifest)?;
    let expected_manifest_digest = packet_digest(expected_manifest_json.as_bytes());
    if manifest_digest != &expected_manifest_digest {
        return Err(packet_io_error(
            "experiment_packet_output.manifest_digest",
            "packet output manifest digest does not match canonical manifest bytes",
        ));
    }
    Ok(())
}

fn build_packet_manifest(
    inner_bundle: &ExperimentBundle,
    composition_config: &impl ExperimentPacketComposition,
    inner_json: &str,
    config_json: &str,
    outer_json: &str,
) -> Result<ExperimentPacketManifest> {
    let inner_digest = packet_digest(inner_json.as_bytes());
    let config_digest = packet_digest(config_json.as_bytes());
    let outer_digest = packet_digest(outer_json.as_bytes());
    if inner_digest != compute_experiment_bundle_digest(inner_bundle)? {
        return Err(packet_io_error(
            EXPERIMENT_PACKET_INNER_BUNDLE_PATH,
            "inner packet bytes do not match the typed inner bundle digest",
        ));
    }
    let outer_bundle = deserialize_experiment_artifact_bundle_json(outer_json)?;
    if outer_digest != compute_experiment_artifact_bundle_digest(&outer_bundle)? {
        return Err(packet_io_error(
            EXPERIMENT_PACKET_OUTER_BUNDLE_PATH,
            "outer packet bytes do not match the typed outer bundle digest",
        ));
    }
    if composition_config.serialize_config_json()? != config_json {
        return Err(packet_io_error(
            EXPERIMENT_PACKET_COMPOSITION_CONFIG_PATH,
            "composition config bytes do not match the typed config serialization",
        ));
    }
    let manifest = ExperimentPacketManifest {
        schema_version: EXPERIMENT_PACKET_SCHEMA_VERSION.to_string(),
        experiment_id: composition_config.experiment_id().to_string(),
        run_id: composition_config.run_id().to_string(),
        inner_bundle_id: inner_bundle.bundle_id.clone(),
        inner_bundle: ExperimentPacketFileRef {
            relative_path: EXPERIMENT_PACKET_INNER_BUNDLE_PATH.to_string(),
            digest: inner_digest,
        },
        composition_config: ExperimentPacketFileRef {
            relative_path: EXPERIMENT_PACKET_COMPOSITION_CONFIG_PATH.to_string(),
            digest: config_digest,
        },
        outer_bundle: ExperimentPacketFileRef {
            relative_path: EXPERIMENT_PACKET_OUTER_BUNDLE_PATH.to_string(),
            digest: outer_digest,
        },
        claim_boundary: ClaimBoundary::Level0DesignNote,
        limitations: required_experiment_packet_limitations()
            .into_iter()
            .map(str::to_string)
            .collect(),
    };
    validate_experiment_packet_manifest(&manifest)?;
    Ok(manifest)
}

fn packet_digest(bytes: &[u8]) -> ArtifactDigest {
    compute_artifact_digest_bytes(
        bytes,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    )
}

fn validate_packet_digest(digest: &ArtifactDigest, path: String) -> Result<()> {
    if digest.algorithm != ArtifactDigestAlgorithm::Sha256
        || digest.kind != Some(ArtifactKind::Other)
        || digest.role != Some(ArtifactRole::Manifest)
        || digest.hex_digest.len() != 64
        || !digest
            .hex_digest
            .chars()
            .all(|character| character.is_ascii_hexdigit() && !character.is_ascii_uppercase())
        || digest.byte_len == 0
    {
        return Err(ZkBenchError::validation(
            path,
            "packet file digest must be non-empty lowercase SHA-256 manifest metadata",
        ));
    }
    Ok(())
}

fn validate_output_root(output_root: &Path, protected_paths: &[PathBuf]) -> Result<()> {
    if output_root.as_os_str().is_empty() {
        return Err(packet_io_error(
            "output_root",
            "packet output root must be non-empty",
        ));
    }
    let normalized_output = normalize_path(output_root)?;
    let resolved_output = resolve_existing_prefix(output_root)?;
    for protected in protected_paths {
        let normalized_protected = normalize_path(protected)?;
        let resolved_protected = resolve_existing_prefix(protected)?;
        if paths_overlap(&normalized_output, &normalized_protected)
            || paths_overlap(&resolved_output, &resolved_protected)
        {
            return Err(packet_io_error(
                output_root.display().to_string(),
                format!(
                    "packet output root overlaps protected path {}",
                    protected.display()
                ),
            ));
        }
    }
    Ok(())
}

fn reject_unexpected_existing_paths(root: &Path) -> Result<()> {
    let expected = expected_paths();
    let mut seen = BTreeSet::new();
    collect_existing_paths(root, root, &mut seen)?;
    for path in &seen {
        if !expected.contains(path) {
            return Err(packet_io_error(
                path,
                "unexpected file in packet output root",
            ));
        }
    }
    for path in &expected {
        if !seen.contains(path) {
            return Err(packet_io_error(path, "missing required packet output file"));
        }
    }
    Ok(())
}

fn expected_paths() -> BTreeSet<String> {
    [
        EXPERIMENT_PACKET_MANIFEST_PATH,
        EXPERIMENT_PACKET_INNER_BUNDLE_PATH,
        EXPERIMENT_PACKET_COMPOSITION_CONFIG_PATH,
        EXPERIMENT_PACKET_OUTER_BUNDLE_PATH,
        EXPERIMENT_PACKET_MANIFEST_DIGEST_PATH,
        EXPERIMENT_PACKET_INNER_BUNDLE_DIGEST_PATH,
        EXPERIMENT_PACKET_COMPOSITION_CONFIG_DIGEST_PATH,
        EXPERIMENT_PACKET_OUTER_BUNDLE_DIGEST_PATH,
    ]
    .into_iter()
    .map(str::to_string)
    .collect()
}

fn collect_existing_paths(root: &Path, current: &Path, seen: &mut BTreeSet<String>) -> Result<()> {
    for entry in fs::read_dir(current)
        .map_err(|error| packet_io_error(current.display().to_string(), error.to_string()))?
    {
        let entry = entry
            .map_err(|error| packet_io_error(current.display().to_string(), error.to_string()))?;
        let path = entry.path();
        reject_symlink(&path)?;
        if path.is_dir() {
            collect_existing_paths(root, &path, seen)?;
        } else {
            let relative = path.strip_prefix(root).map_err(|error| {
                packet_io_error(
                    path.display().to_string(),
                    format!("could not compute packet-relative path: {error}"),
                )
            })?;
            seen.insert(relative.to_string_lossy().replace('\\', "/"));
        }
    }
    Ok(())
}

fn write_digest_sidecar(root: &Path, relative_path: &str, digest: &ArtifactDigest) -> Result<()> {
    write_relative_bytes(
        root,
        relative_path,
        format!("{}\n", digest.hex_digest).as_bytes(),
    )
}

fn validate_digest_sidecar(
    root: &Path,
    relative_path: &str,
    expected: &ArtifactDigest,
) -> Result<()> {
    let sidecar = read_utf8(root, relative_path)?;
    let canonical_sidecar = format!("{}\n", expected.hex_digest);
    if sidecar != canonical_sidecar {
        return Err(packet_io_error(
            relative_path,
            "digest sidecar does not match canonical packet bytes",
        ));
    }
    Ok(())
}

fn validate_payload_digest(
    root: &Path,
    payload_path: &str,
    sidecar_path: &str,
    bytes: &[u8],
    expected: &ArtifactDigest,
) -> Result<()> {
    if packet_digest(bytes) != *expected {
        return Err(packet_io_error(
            payload_path,
            "packet payload bytes do not match manifest digest",
        ));
    }
    validate_digest_sidecar(root, sidecar_path, expected)
}

fn read_utf8(root: &Path, relative_path: &str) -> Result<String> {
    validate_relative_path(relative_path)?;
    let bytes = fs::read(root.join(relative_path))
        .map_err(|error| packet_io_error(relative_path, error.to_string()))?;
    String::from_utf8(bytes).map_err(|error| {
        packet_io_error(relative_path, format!("packet file is not UTF-8: {error}"))
    })
}

fn write_relative_bytes(root: &Path, relative_path: &str, bytes: &[u8]) -> Result<()> {
    let path = validate_write_path(root, relative_path)?;
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|error| packet_io_error(parent.display().to_string(), error.to_string()))?;
        reject_symlink(parent)?;
    }
    fs::write(&path, bytes)
        .map_err(|error| packet_io_error(path.display().to_string(), error.to_string()))
}

fn validate_write_path(root: &Path, relative_path: &str) -> Result<PathBuf> {
    validate_relative_path(relative_path)?;
    reject_existing_path(root)?;
    let mut cursor = root.to_path_buf();
    for component in Path::new(relative_path).components() {
        if let Component::Normal(segment) = component {
            cursor.push(segment);
            reject_existing_path(&cursor)?;
        }
    }
    Ok(root.join(relative_path))
}

fn reject_existing_path(path: &Path) -> Result<()> {
    match fs::symlink_metadata(path) {
        Ok(metadata) => {
            if metadata.file_type().is_symlink() {
                return Err(packet_io_error(
                    path.display().to_string(),
                    "symlinks are not allowed in experiment packet outputs",
                ));
            }
            Ok(())
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(()),
        Err(error) => Err(packet_io_error(
            path.display().to_string(),
            error.to_string(),
        )),
    }
}

fn validate_relative_path(relative_path: &str) -> Result<()> {
    let path = Path::new(relative_path);
    if relative_path.trim().is_empty()
        || path.is_absolute()
        || relative_path.contains("..")
        || relative_path.contains('\\')
        || relative_path.contains("://")
        || relative_path.contains('|')
        || relative_path.contains(';')
        || relative_path.contains('$')
    {
        return Err(packet_io_error(
            relative_path,
            "packet path must be a portable relative path",
        ));
    }
    Ok(())
}

fn reject_symlink(path: &Path) -> Result<()> {
    let metadata = fs::symlink_metadata(path)
        .map_err(|error| packet_io_error(path.display().to_string(), error.to_string()))?;
    if metadata.file_type().is_symlink() {
        return Err(packet_io_error(
            path.display().to_string(),
            "symlinks are not allowed in experiment packet outputs",
        ));
    }
    Ok(())
}

fn directory_has_entries(path: &Path) -> Result<bool> {
    Ok(fs::read_dir(path)
        .map_err(|error| packet_io_error(path.display().to_string(), error.to_string()))?
        .next()
        .is_some())
}

fn normalize_path(path: &Path) -> Result<PathBuf> {
    let mut normalized = if path.is_absolute() {
        PathBuf::new()
    } else {
        std::env::current_dir().map_err(|error| packet_io_error("cwd", error.to_string()))?
    };
    for component in path.components() {
        match component {
            Component::Prefix(prefix) => normalized.push(prefix.as_os_str()),
            Component::RootDir => normalized.push(component.as_os_str()),
            Component::CurDir => {}
            Component::ParentDir => {
                normalized.pop();
            }
            Component::Normal(segment) => normalized.push(segment),
        }
    }
    Ok(normalized)
}

fn resolve_existing_prefix(path: &Path) -> Result<PathBuf> {
    let normalized = normalize_path(path)?;
    let mut missing = Vec::new();
    let mut cursor = normalized.as_path();
    loop {
        match fs::canonicalize(cursor) {
            Ok(mut resolved) => {
                for segment in missing.iter().rev() {
                    resolved.push(segment);
                }
                return Ok(resolved);
            }
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                let Some(segment) = cursor.file_name() else {
                    return Ok(normalized);
                };
                missing.push(segment.to_os_string());
                let Some(parent) = cursor.parent() else {
                    return Ok(normalized);
                };
                cursor = parent;
            }
            Err(error) => {
                return Err(packet_io_error(
                    cursor.display().to_string(),
                    error.to_string(),
                ));
            }
        }
    }
}

fn paths_overlap(left: &Path, right: &Path) -> bool {
    left == right || left.starts_with(right) || right.starts_with(left)
}

fn require_text(value: &str, path: &str) -> Result<()> {
    if value.trim().is_empty() {
        return Err(ZkBenchError::validation(path, "value must not be empty"));
    }
    Ok(())
}

fn packet_io_error(path: impl Into<String>, message: impl Into<String>) -> ZkBenchError {
    ZkBenchError::artifact(path, message)
}

#[cfg(all(test, unix))]
mod tests {
    use std::fs;
    use std::os::unix::fs::symlink;

    use tempfile::tempdir;

    use super::{write_relative_bytes, EXPERIMENT_PACKET_INNER_BUNDLE_PATH};

    #[test]
    fn write_rejects_dangling_leaf_symlink_before_following_it() {
        let dir = tempdir().expect("temporary output parent should exist");
        let root = dir.path().join("dangling-write");
        fs::create_dir_all(root.join("artifacts")).expect("artifact directory should exist");
        let outside = dir.path().join("outside.json");
        symlink(&outside, root.join(EXPERIMENT_PACKET_INNER_BUNDLE_PATH))
            .expect("dangling payload symlink should install");

        let error = write_relative_bytes(
            &root,
            EXPERIMENT_PACKET_INNER_BUNDLE_PATH,
            b"must not follow",
        )
        .expect_err("dangling payload symlinks must fail closed");
        assert!(error.to_string().contains("symlink"));
        assert!(
            !outside.exists(),
            "write must not create the symlink target"
        );
    }

    #[test]
    fn write_rejects_symlinked_intermediate_directory() {
        let dir = tempdir().expect("temporary output parent should exist");
        let root = dir.path().join("intermediate-write");
        fs::create_dir_all(&root).expect("packet root should exist");
        let outside = dir.path().join("outside-artifacts");
        fs::create_dir_all(&outside).expect("outside directory should exist");
        symlink(&outside, root.join("artifacts")).expect("intermediate symlink should install");

        let error = write_relative_bytes(
            &root,
            EXPERIMENT_PACKET_INNER_BUNDLE_PATH,
            b"must not follow",
        )
        .expect_err("symlinked intermediate directories must fail closed");
        assert!(error.to_string().contains("symlink"));
        assert!(!outside.join("inner-experiment-bundle.json").exists());
    }

    #[test]
    fn write_rejects_existing_leaf_symlink_without_mutating_target() {
        let dir = tempdir().expect("temporary output parent should exist");
        let root = dir.path().join("existing-leaf-write");
        fs::create_dir_all(root.join("artifacts")).expect("artifact directory should exist");
        let outside = dir.path().join("outside.json");
        fs::write(&outside, b"original").expect("outside target should exist");
        symlink(&outside, root.join(EXPERIMENT_PACKET_INNER_BUNDLE_PATH))
            .expect("leaf symlink should install");

        let error = write_relative_bytes(
            &root,
            EXPERIMENT_PACKET_INNER_BUNDLE_PATH,
            b"must not follow",
        )
        .expect_err("existing leaf symlinks must fail closed");
        assert!(error.to_string().contains("symlink"));
        assert_eq!(
            fs::read(&outside).expect("outside target should remain"),
            b"original"
        );
    }
}

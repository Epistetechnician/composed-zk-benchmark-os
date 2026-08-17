//! Generic nine-slot composition for any validated experiment plugin.
//!
//! State slice: `benchmark-os-experiment-plugin-agnostic-composition-v1`.
//! Binding access slice: `benchmark-os-plugin-composition-binding-access-v1`.
//! Identity extension: `benchmark-os-plugin-composition-identity-value-v1`.
//! Source binding integrity slice: `benchmark-os-plugin-composition-source-binding-integrity-v1`.
//! Ordered binding access slice: `benchmark-os-plugin-composition-ordered-binding-access-v1`.
//! Canonical order slice: `benchmark-os-plugin-composition-canonical-order-v1`.
//! Projection adapter slice: `benchmark-os-plugin-composition-projection-adapter-v1`.
//! Projector provenance slice: `benchmark-os-plugin-composition-projector-provenance-v1`.
//! Packet-job projector injection slice: `benchmark-os-plugin-composition-packet-job-projector-injection-v1`.
//! Durable projector attribution slice: `benchmark-os-plugin-composition-projector-durable-attribution-v1`.
//! Identity constructor locality slice: `benchmark-os-plugin-composition-identity-constructor-locality-v1`.
//! Identity descriptor binding slice: `benchmark-os-plugin-composition-identity-descriptor-binding-v1`.
//! Artifact-reference policy locality slice: `benchmark-os-plugin-composition-artifact-reference-policy-locality-v1`.
//! Output handoff validation slice: `benchmark-os-plugin-composition-output-handoff-validation-v1`.
//! Durable composition-adapter attribution slice:
//! `benchmark-os-plugin-composition-adapter-durable-attribution-v1`.
//!
//! This module is the generic outer seam. It consumes a validated
//! `ExperimentBundle`, creates explicit source-kind bindings for the fixed
//! nine-slot observability bundle, and validates every identity and digest.
//! It does not materialize files, execute a model, invoke a process, access the
//! network, mutate evidence, or grant runtime authority.

use std::collections::BTreeSet;

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::{
    compute_artifact_digest, compute_artifact_digest_bytes, ArtifactDigest, ArtifactKind,
    ArtifactRole, ClaimBoundary,
};
use crate::experiment::{
    compute_experiment_bundle_digest, validate_experiment_bundle,
    ExperimentArtifactKind as InnerKind, ExperimentBundle, ExperimentPlugin,
    ExperimentPluginDescriptor,
};
use crate::experiment_identity::PluginCompositionIdentity;
use crate::experiment_observability::{
    assemble_experiment_artifact_bundle, validate_experiment_artifact_bundle,
    ExperimentArtifactBundle, ExperimentArtifactKind as OuterKind,
    ExperimentArtifactReferencePolicy, ExperimentProvenance, ModuleDescriptor,
};

/// Schema version for generic plugin-to-observability composition.
pub const PLUGIN_COMPOSITION_SCHEMA_VERSION: &str = "experiment-plugin-composition-v1";

/// Adapter identity for the generic composition seam.
pub const PLUGIN_COMPOSITION_ADAPTER_ID: &str = "typed-experiment-plugin-composition-v1";

/// Stable logical module id for the generic composition Adapter itself.
pub const PLUGIN_COMPOSITION_ADAPTER_MODULE_ID: &str = "plugin-composition-adapter";

/// Source revision marker for newly emitted generic composition descriptors.
pub const PLUGIN_COMPOSITION_ADAPTER_SOURCE_REVISION: &str =
    "benchmark-os-plugin-composition-adapter-durable-attribution-v1";

/// Stable logical module id for all generic source projectors.
pub const PLUGIN_COMPOSITION_PROJECTOR_MODULE_ID: &str = "plugin-composition-projector";

/// Explicit source reference from an inner bundle artifact.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PluginCompositionSource {
    /// Inner artifact category selected by the composition contract.
    pub inner_kind: InnerKind,
    /// Inner artifact URI retained as metadata.
    pub inner_uri: String,
    /// Exact digest of the selected inner artifact payload.
    pub inner_digest: ArtifactDigest,
}

/// Explicit mapping from one outer slot to one or more inner artifact kinds.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PluginCompositionBinding {
    /// Outer fixed slot.
    pub outer_kind: OuterKind,
    /// Canonical outer URI.
    pub outer_uri: String,
    /// Explicit inner sources; no filename or import inference is permitted.
    pub sources: Vec<PluginCompositionSource>,
}

impl PluginCompositionBinding {
    /// Return exactly one source of the requested inner kind.
    pub fn source(&self, kind: InnerKind) -> Result<&PluginCompositionSource> {
        let mut matches = self
            .sources
            .iter()
            .filter(|source| source.inner_kind == kind);
        let source = matches.next().ok_or_else(|| {
            ZkBenchError::validation(
                "plugin_composition_binding.sources",
                format!("missing source for inner kind {kind:?}"),
            )
        })?;
        if matches.next().is_some() {
            return Err(ZkBenchError::validation(
                "plugin_composition_binding.sources",
                format!("source for inner kind {kind:?} is duplicated"),
            ));
        }
        Ok(source)
    }

    fn validate_sources(&self, inner: &ExperimentBundle, path: &str) -> Result<()> {
        if self.sources.is_empty() {
            return Err(ZkBenchError::validation(
                format!("{path}.sources"),
                "every outer slot requires at least one explicit inner source",
            ));
        }
        let mut inner_kinds = BTreeSet::new();
        for (source_index, source) in self.sources.iter().enumerate() {
            let source_path = format!("{path}.sources[{source_index}]");
            if !inner_kinds.insert(source.inner_kind) {
                return Err(ZkBenchError::validation(
                    format!("{source_path}.inner_kind"),
                    "inner source kind is duplicated within the binding",
                ));
            }
            let inner_artifact = inner.artifact(source.inner_kind)?;
            if inner_artifact.uri != source.inner_uri
                || inner_artifact.digest != source.inner_digest
            {
                return Err(ZkBenchError::validation(
                    source_path,
                    "binding source URI or digest does not match the inner bundle",
                ));
            }
        }
        Ok(())
    }
}

/// Canonical config for one generic plugin composition.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PluginCompositionConfig {
    /// Composition schema version.
    pub schema_version: String,
    /// Composition adapter identity.
    pub adapter_id: String,
    /// Descriptor of the Adapter that emitted this config.
    ///
    /// New configs always carry this identity. `None` is accepted only for
    /// legacy v1 JSON that predates durable composition-adapter attribution.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub adapter_descriptor: Option<ModuleDescriptor>,
    /// Outer experiment identity.
    pub experiment_id: String,
    /// Outer run identity.
    pub run_id: String,
    /// Descriptor of the plugin that produced the inner bundle.
    pub plugin_descriptor: ExperimentPluginDescriptor,
    /// Descriptor of the projector that produced the explicit outer bindings.
    ///
    /// New configs always carry this identity. `None` is accepted only for
    /// legacy v1 JSON that predates durable projector attribution; callers
    /// must not treat such configs as fully attributed.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub projector_descriptor: Option<ModuleDescriptor>,
    /// Inner bundle identity.
    pub inner_bundle_id: String,
    /// Digest over the exact inner bundle.
    pub inner_bundle_digest: ArtifactDigest,
    /// Explicit nine-slot source projection.
    pub bindings: Vec<PluginCompositionBinding>,
    /// Generic composition claim ceiling.
    pub claim_boundary: ClaimBoundary,
}

/// Replaceable source projection seam for generic plugin composition.
///
/// Implementations return the existing typed binding values; the config and
/// packet modules retain ownership of serialization, validation, digests, and
/// the fixed outer nine-slot shape. Projector identity is validated at the
/// runtime seam and copied into newly emitted configs. Projectors are pure-data
/// adapters and do not authorize execution, publication, evidence mutation, or
/// network access.
pub trait PluginCompositionProjector: Send + Sync {
    /// Return the implementation identity used for runtime provenance checks.
    fn descriptor(&self) -> Result<ModuleDescriptor> {
        Err(ZkBenchError::validation(
            "plugin_composition.projector.descriptor",
            "projector descriptor is required",
        ))
    }
    /// Project one validated inner bundle into explicit outer-slot bindings.
    fn project(&self, inner: &ExperimentBundle) -> Result<Vec<PluginCompositionBinding>>;
}

/// Validate one runtime projector descriptor before any plugin run.
pub(crate) fn validate_plugin_composition_projector(
    projector: &dyn PluginCompositionProjector,
) -> Result<ModuleDescriptor> {
    let descriptor = projector.descriptor()?;
    validate_plugin_composition_projector_descriptor(&descriptor, "plugin_composition.projector")?;
    Ok(descriptor)
}

fn validate_plugin_composition_projector_descriptor(
    descriptor: &ModuleDescriptor,
    path: &str,
) -> Result<()> {
    descriptor.validate(path)?;
    if descriptor.module_id != PLUGIN_COMPOSITION_PROJECTOR_MODULE_ID {
        return Err(ZkBenchError::validation(
            format!("{path}.module_id"),
            "projector descriptor has an unsupported module id",
        ));
    }
    Ok(())
}

/// Reference projector for the standardized experiment-bundle artifact kinds.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct StandardPluginCompositionProjector;

impl PluginCompositionProjector for StandardPluginCompositionProjector {
    fn descriptor(&self) -> Result<ModuleDescriptor> {
        Ok(ModuleDescriptor {
            module_id: PLUGIN_COMPOSITION_PROJECTOR_MODULE_ID.to_string(),
            implementation_id: "standard-plugin-composition-projector-v1".to_string(),
            version: "1".to_string(),
            source_revision: "benchmark-os-plugin-composition-projection-adapter-v1".to_string(),
        })
    }

    fn project(&self, inner: &ExperimentBundle) -> Result<Vec<PluginCompositionBinding>> {
        standard_bindings(inner)
    }
}

impl PluginCompositionConfig {
    /// Return the durably retained projector identity, if present.
    pub fn projector_descriptor(&self) -> Option<&ModuleDescriptor> {
        self.projector_descriptor.as_ref()
    }

    /// Report whether this config carries durable projector attribution.
    pub fn has_durable_projector_attribution(&self) -> bool {
        self.projector_descriptor.is_some()
    }

    /// Return the typed identity represented by this composition config.
    pub fn identity(&self) -> Result<PluginCompositionIdentity> {
        PluginCompositionIdentity::new_at(
            self.plugin_descriptor.plugin_id.clone(),
            self.experiment_id.clone(),
            self.run_id.clone(),
            "plugin_composition_config.identity",
        )
    }

    /// Return exactly one explicit binding for an outer slot.
    pub fn binding(&self, kind: OuterKind) -> Result<&PluginCompositionBinding> {
        let mut matches = self
            .bindings
            .iter()
            .filter(|binding| binding.outer_kind == kind);
        let binding = matches.next().ok_or_else(|| {
            ZkBenchError::validation(
                "plugin_composition_config.bindings",
                format!("missing binding for outer slot {kind:?}"),
            )
        })?;
        if matches.next().is_some() {
            return Err(ZkBenchError::validation(
                "plugin_composition_config.bindings",
                format!("binding for outer slot {kind:?} is duplicated"),
            ));
        }
        Ok(binding)
    }

    /// Return all bindings in the canonical fixed-slot order.
    pub fn bindings_in_order(&self) -> Result<Vec<&PluginCompositionBinding>> {
        OuterKind::ALL
            .into_iter()
            .map(|kind| self.binding(kind))
            .collect()
    }

    /// Validate config identity and every explicit inner source binding.
    pub fn validate(&self, inner: &ExperimentBundle) -> Result<()> {
        if self.schema_version != PLUGIN_COMPOSITION_SCHEMA_VERSION {
            return Err(ZkBenchError::validation(
                "plugin_composition_config.schema_version",
                "unsupported generic composition schema version",
            ));
        }
        if self.adapter_id != PLUGIN_COMPOSITION_ADAPTER_ID {
            return Err(ZkBenchError::validation(
                "plugin_composition_config.adapter_id",
                "unsupported generic composition adapter",
            ));
        }
        if let Some(adapter_descriptor) = &self.adapter_descriptor {
            validate_plugin_composition_adapter_descriptor(
                adapter_descriptor,
                "plugin_composition_config.adapter_descriptor",
            )?;
        }
        self.identity()?;
        self.plugin_descriptor
            .validate("plugin_composition_config.plugin_descriptor")?;
        if let Some(projector_descriptor) = &self.projector_descriptor {
            validate_plugin_composition_projector_descriptor(
                projector_descriptor,
                "plugin_composition_config.projector_descriptor",
            )?;
        }
        if self.inner_bundle_id != inner.bundle_id
            || self.inner_bundle_digest != compute_experiment_bundle_digest(inner)?
        {
            return Err(ZkBenchError::validation(
                "plugin_composition_config.inner_bundle",
                "composition config is not bound to the supplied inner bundle",
            ));
        }
        if self.claim_boundary != ClaimBoundary::Level0DesignNote {
            return Err(ZkBenchError::ClaimBoundary {
                message: "generic plugin composition remains Level0DesignNote".to_string(),
            });
        }
        if self.bindings.len() != OuterKind::SLOT_COUNT {
            return Err(ZkBenchError::validation(
                "plugin_composition_config.bindings",
                "generic composition requires exactly nine explicit slot bindings",
            ));
        }
        let mut outer_kinds = BTreeSet::new();
        let mut outer_uris = BTreeSet::new();
        for (index, binding) in self.bindings.iter().enumerate() {
            let path = format!("plugin_composition_config.bindings[{index}]");
            if binding.outer_kind != OuterKind::ALL[index] {
                return Err(ZkBenchError::validation(
                    format!("{path}.outer_kind"),
                    "bindings must follow canonical OuterKind::ALL order",
                ));
            }
            if !outer_kinds.insert(binding.outer_kind)
                || !outer_uris.insert(binding.outer_uri.clone())
            {
                return Err(ZkBenchError::validation(
                    format!("{path}.outer_kind"),
                    "outer slot kind and URI must be unique",
                ));
            }
            require_text(&binding.outer_uri, format!("{path}.outer_uri"))?;
            if binding.outer_uri.starts_with('/') || binding.outer_uri.contains("..") {
                return Err(ZkBenchError::validation(
                    format!("{path}.outer_uri"),
                    "outer URI must be a portable relative path",
                ));
            }
            binding.validate_sources(inner, &path)?;
        }
        for kind in OuterKind::ALL {
            if !outer_kinds.contains(&kind) {
                return Err(ZkBenchError::validation(
                    "plugin_composition_config.bindings",
                    format!("missing explicit binding for outer slot {kind:?}"),
                ));
            }
        }
        Ok(())
    }

    /// Validate the config against the materialized outer nine-slot bundle.
    pub fn validate_against_outer(
        &self,
        inner: &ExperimentBundle,
        outer: &ExperimentArtifactBundle,
    ) -> Result<()> {
        validate_experiment_bundle(inner)
            .valid
            .then_some(())
            .ok_or_else(|| {
                ZkBenchError::validation(
                    "plugin_composition.inner_bundle",
                    "inner bundle failed experiment validation",
                )
            })?;
        self.validate(inner)?;
        validate_experiment_artifact_bundle(outer)?;
        if outer.experiment_id != self.experiment_id || outer.run_id != self.run_id {
            return Err(ZkBenchError::validation(
                "plugin_composition.outer_identity",
                "outer identity does not match the composition config",
            ));
        }
        if outer.bundle_id
            != expected_outer_bundle_id(
                &self.plugin_descriptor.plugin_id,
                &self.inner_bundle_id,
                &self.experiment_id,
                &self.run_id,
            )?
        {
            return Err(ZkBenchError::validation(
                "plugin_composition.outer_bundle_id",
                "outer bundle id is not bound to the plugin, inner bundle, and run",
            ));
        }
        let expected_config_digest = compute_artifact_digest(
            self,
            Some(ArtifactKind::Other),
            Some(ArtifactRole::Manifest),
        )?;
        if outer.config.digest != expected_config_digest {
            return Err(ZkBenchError::validation(
                "plugin_composition.outer_config_digest",
                "outer config digest does not match the canonical composition config",
            ));
        }
        for binding in self.bindings_in_order()? {
            let target = outer.artifact(binding.outer_kind);
            target.validate_for(
                "plugin_composition.outer_artifact",
                &self.experiment_id,
                &self.run_id,
            )?;
            if target.uri != binding.outer_uri {
                return Err(ZkBenchError::validation(
                    "plugin_composition.outer_uri",
                    "outer URI does not match its explicit binding",
                ));
            }
            if binding.outer_kind != OuterKind::Config {
                let expected_payload =
                    PluginCompositionArtifactPayload::from_binding(self, binding);
                let expected_digest = compute_artifact_digest(
                    &expected_payload,
                    Some(ArtifactKind::Other),
                    Some(ArtifactRole::Manifest),
                )?;
                if target.digest != expected_digest {
                    return Err(ZkBenchError::validation(
                        "plugin_composition.outer_digest",
                        "outer artifact digest does not match its explicit binding payload",
                    ));
                }
            }
        }
        Ok(())
    }
}

/// Output of one generic plugin composition run.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PluginCompositionOutput {
    /// Validated inner plugin bundle.
    pub inner: ExperimentBundle,
    /// Canonical generic composition config.
    pub config: PluginCompositionConfig,
    /// Validated outer nine-slot bundle.
    pub outer: ExperimentArtifactBundle,
}

impl PluginCompositionOutput {
    /// Revalidate the complete inner/config/outer handoff contract.
    ///
    /// The runner already returns a validated value. This explicit Interface
    /// keeps downstream Adapters from treating the three public fields as
    /// independently trustworthy after cloning or transformation.
    pub fn validate(&self) -> Result<()> {
        self.config.validate_against_outer(&self.inner, &self.outer)
    }

    /// Repackage this public compatibility value as an invariant-bearing
    /// handoff for downstream Adapters.
    pub fn into_validated(self) -> Result<ValidatedPluginCompositionOutput> {
        ValidatedPluginCompositionOutput::new(self.inner, self.config, self.outer)
    }
}

/// Invariant-bearing generic composition output for downstream Adapters.
///
/// Fields remain private so a caller cannot construct a trusted handoff by
/// assembling an unchecked inner/config/outer triplet. Use `new` or the
/// runner's `run_validated_output` Interface; the existing public output value
/// remains available through `into_output` for source compatibility.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValidatedPluginCompositionOutput {
    inner: ExperimentBundle,
    config: PluginCompositionConfig,
    outer: ExperimentArtifactBundle,
}

impl ValidatedPluginCompositionOutput {
    /// Construct a validated handoff from the three composition artifacts.
    pub fn new(
        inner: ExperimentBundle,
        config: PluginCompositionConfig,
        outer: ExperimentArtifactBundle,
    ) -> Result<Self> {
        let output = PluginCompositionOutput {
            inner,
            config,
            outer,
        };
        output.validate()?;
        Ok(Self {
            inner: output.inner,
            config: output.config,
            outer: output.outer,
        })
    }

    /// Borrow the validated inner experiment bundle.
    pub fn inner(&self) -> &ExperimentBundle {
        &self.inner
    }

    /// Borrow the validated generic composition config.
    pub fn config(&self) -> &PluginCompositionConfig {
        &self.config
    }

    /// Borrow the validated outer observability bundle.
    pub fn outer(&self) -> &ExperimentArtifactBundle {
        &self.outer
    }

    /// Return the validated artifacts for an Adapter that owns the next step.
    pub fn into_parts(
        self,
    ) -> (
        ExperimentBundle,
        PluginCompositionConfig,
        ExperimentArtifactBundle,
    ) {
        (self.inner, self.config, self.outer)
    }

    /// Return the historical public output shape without changing its bytes.
    pub fn into_output(self) -> PluginCompositionOutput {
        let (inner, config, outer) = self.into_parts();
        PluginCompositionOutput {
            inner,
            config,
            outer,
        }
    }
}

/// Generic composition runner for any typed experiment plugin.
pub struct PluginCompositionRunner {
    plugin: Box<dyn ExperimentPlugin>,
    projector: Box<dyn PluginCompositionProjector>,
    projector_descriptor: ModuleDescriptor,
    identity: PluginCompositionIdentity,
    provenance: ExperimentProvenance,
}

impl PluginCompositionRunner {
    /// Construct a runner around one typed plugin and explicit outer identity.
    pub fn new(
        plugin: Box<dyn ExperimentPlugin>,
        experiment_id: impl Into<String>,
        run_id: impl Into<String>,
        provenance: ExperimentProvenance,
    ) -> Result<Self> {
        Self::new_with_projector(
            plugin,
            experiment_id,
            run_id,
            provenance,
            Box::new(StandardPluginCompositionProjector),
        )
    }

    /// Construct a runner with an explicit runtime source projector adapter.
    pub fn new_with_projector(
        plugin: Box<dyn ExperimentPlugin>,
        experiment_id: impl Into<String>,
        run_id: impl Into<String>,
        provenance: ExperimentProvenance,
        projector: Box<dyn PluginCompositionProjector>,
    ) -> Result<Self> {
        let identity = PluginCompositionIdentity::new(
            plugin.descriptor().plugin_id.clone(),
            experiment_id,
            run_id,
        )?;
        Self::new_with_identity_and_projector(plugin, identity, provenance, projector)
    }

    /// Construct a runner from the shared typed plugin-composition identity.
    pub fn new_with_identity(
        plugin: Box<dyn ExperimentPlugin>,
        identity: PluginCompositionIdentity,
        provenance: ExperimentProvenance,
    ) -> Result<Self> {
        Self::new_with_identity_and_projector(
            plugin,
            identity,
            provenance,
            Box::new(StandardPluginCompositionProjector),
        )
    }

    /// Construct a runner from shared identity and an explicit projector.
    pub fn new_with_identity_and_projector(
        plugin: Box<dyn ExperimentPlugin>,
        identity: PluginCompositionIdentity,
        provenance: ExperimentProvenance,
        projector: Box<dyn PluginCompositionProjector>,
    ) -> Result<Self> {
        identity.validate_at("plugin_composition.identity")?;
        provenance.validate("plugin_composition.provenance")?;
        let descriptor = plugin.descriptor();
        descriptor.validate("plugin_composition.plugin")?;
        let projector_descriptor = validate_plugin_composition_projector(projector.as_ref())?;
        if descriptor.plugin_id != identity.plugin_id {
            return Err(ZkBenchError::validation(
                "plugin_composition.identity.plugin_id",
                "identity plugin id does not match plugin descriptor",
            ));
        }
        Ok(Self {
            plugin,
            projector,
            projector_descriptor,
            identity,
            provenance,
        })
    }

    /// Return the validated projector identity used by this runner.
    pub fn projector_descriptor(&self) -> &ModuleDescriptor {
        &self.projector_descriptor
    }

    /// Run the plugin through output binding and build the generic nine slots.
    pub fn run(&self) -> Result<PluginCompositionOutput> {
        Ok(self.run_validated_output()?.into_output())
    }

    /// Run the plugin and return an invariant-bearing composition handoff.
    pub fn run_validated_output(&self) -> Result<ValidatedPluginCompositionOutput> {
        let validated = self.plugin.run_validated_output()?;
        let (descriptor, inner) = validated.into_parts();
        let inner_bundle_digest = compute_experiment_bundle_digest(&inner)?;
        let bindings = self.projector.project(&inner)?;
        let config = PluginCompositionConfig {
            schema_version: PLUGIN_COMPOSITION_SCHEMA_VERSION.to_string(),
            adapter_id: PLUGIN_COMPOSITION_ADAPTER_ID.to_string(),
            adapter_descriptor: Some(plugin_composition_adapter_descriptor()),
            experiment_id: self.identity.experiment_id.clone(),
            run_id: self.identity.run_id.clone(),
            plugin_descriptor: descriptor,
            projector_descriptor: Some(self.projector_descriptor.clone()),
            inner_bundle_id: inner.bundle_id.clone(),
            inner_bundle_digest,
            bindings,
            claim_boundary: ClaimBoundary::Level0DesignNote,
        };
        config.validate(&inner)?;
        let outer = build_outer_bundle(&config, &self.provenance)?;
        ValidatedPluginCompositionOutput::new(inner, config, outer)
    }
}

/// Return the stable descriptor retained by newly emitted generic configs.
pub fn plugin_composition_adapter_descriptor() -> ModuleDescriptor {
    ModuleDescriptor {
        module_id: PLUGIN_COMPOSITION_ADAPTER_MODULE_ID.to_string(),
        implementation_id: PLUGIN_COMPOSITION_ADAPTER_ID.to_string(),
        version: "1".to_string(),
        source_revision: PLUGIN_COMPOSITION_ADAPTER_SOURCE_REVISION.to_string(),
    }
}

fn validate_plugin_composition_adapter_descriptor(
    descriptor: &ModuleDescriptor,
    path: &str,
) -> Result<()> {
    descriptor.validate(path)?;
    if descriptor.module_id != PLUGIN_COMPOSITION_ADAPTER_MODULE_ID {
        return Err(ZkBenchError::validation(
            format!("{path}.module_id"),
            "composition adapter descriptor has an unsupported module id",
        ));
    }
    if descriptor.implementation_id != PLUGIN_COMPOSITION_ADAPTER_ID {
        return Err(ZkBenchError::validation(
            format!("{path}.implementation_id"),
            "composition adapter descriptor does not match adapter_id",
        ));
    }
    Ok(())
}

/// Serialize the generic config using deterministic JSON.
pub fn serialize_plugin_composition_config_json(
    config: &PluginCompositionConfig,
) -> Result<String> {
    serde_json::to_string(config).map_err(|error| {
        ZkBenchError::serialization("plugin_composition.config", error.to_string())
    })
}

/// Deserialize a generic config without trusting it until validation.
pub fn deserialize_plugin_composition_config_json(json: &str) -> Result<PluginCompositionConfig> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("plugin_composition.config", error.to_string())
    })
}

/// Compute the digest over canonical generic config bytes.
pub fn compute_plugin_composition_config_digest(
    config: &PluginCompositionConfig,
) -> Result<ArtifactDigest> {
    let json = serialize_plugin_composition_config_json(config)?;
    Ok(compute_artifact_digest_bytes(
        json.as_bytes(),
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    ))
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
struct PluginCompositionArtifactPayload {
    schema_version: &'static str,
    adapter_id: &'static str,
    experiment_id: String,
    run_id: String,
    inner_bundle_id: String,
    inner_bundle_digest: ArtifactDigest,
    binding: PluginCompositionBinding,
    claim_boundary: ClaimBoundary,
}

impl PluginCompositionArtifactPayload {
    fn from_binding(config: &PluginCompositionConfig, binding: &PluginCompositionBinding) -> Self {
        Self {
            schema_version: PLUGIN_COMPOSITION_SCHEMA_VERSION,
            adapter_id: PLUGIN_COMPOSITION_ADAPTER_ID,
            experiment_id: config.experiment_id.clone(),
            run_id: config.run_id.clone(),
            inner_bundle_id: config.inner_bundle_id.clone(),
            inner_bundle_digest: config.inner_bundle_digest.clone(),
            binding: binding.clone(),
            claim_boundary: ClaimBoundary::Level0DesignNote,
        }
    }
}

fn standard_bindings(inner: &ExperimentBundle) -> Result<Vec<PluginCompositionBinding>> {
    Ok(vec![
        binding(
            inner,
            OuterKind::Config,
            "run/config.json",
            &[InnerKind::Config],
        )?,
        binding(
            inner,
            OuterKind::Task,
            "run/task.json",
            &[InnerKind::DataVersion],
        )?,
        binding(
            inner,
            OuterKind::Prompt,
            "run/prompt.json",
            &[InnerKind::ReplayManifest],
        )?,
        binding(
            inner,
            OuterKind::Response,
            "run/response.json",
            &[InnerKind::ReplayResult],
        )?,
        binding(
            inner,
            OuterKind::Evaluation,
            "run/evaluation.json",
            &[InnerKind::Metrics, InnerKind::Report],
        )?,
        binding(
            inner,
            OuterKind::MechanismRecord,
            "run/mechanism-record.json",
            &[InnerKind::MechanismLedger],
        )?,
        binding(
            inner,
            OuterKind::Metadata,
            "run/metadata.json",
            &[InnerKind::Config, InnerKind::ModelVersion],
        )?,
        binding(
            inner,
            OuterKind::Logs,
            "run/logs.json",
            &[
                InnerKind::Config,
                InnerKind::DataVersion,
                InnerKind::ModelVersion,
            ],
        )?,
        binding(
            inner,
            OuterKind::Report,
            "run/report.json",
            &[InnerKind::Report],
        )?,
    ])
}

fn binding(
    inner: &ExperimentBundle,
    outer_kind: OuterKind,
    outer_uri: &str,
    source_kinds: &[InnerKind],
) -> Result<PluginCompositionBinding> {
    let sources = source_kinds
        .iter()
        .map(|kind| {
            let artifact = inner.artifact(*kind)?;
            Ok(PluginCompositionSource {
                inner_kind: *kind,
                inner_uri: artifact.uri.clone(),
                inner_digest: artifact.digest.clone(),
            })
        })
        .collect::<Result<Vec<_>>>()?;
    Ok(PluginCompositionBinding {
        outer_kind,
        outer_uri: outer_uri.to_string(),
        sources,
    })
}

fn build_outer_bundle(
    config: &PluginCompositionConfig,
    provenance: &ExperimentProvenance,
) -> Result<ExperimentArtifactBundle> {
    let artifact_policy = ExperimentArtifactReferencePolicy::new(
        config.experiment_id.clone(),
        config.run_id.clone(),
        provenance.clone(),
    )?;
    let config_ref = artifact_policy.reference("run/config.json", OuterKind::Config, config)?;
    let build_ref = |kind| {
        let binding = config.binding(kind)?;
        let payload = PluginCompositionArtifactPayload::from_binding(config, binding);
        artifact_policy.reference(binding.outer_uri.clone(), binding.outer_kind, &payload)
    };
    let ordered_bindings = config.bindings_in_order()?;
    let mut config_ref = Some(config_ref);
    let artifacts = ordered_bindings
        .into_iter()
        .map(|binding| {
            if binding.outer_kind == OuterKind::Config {
                config_ref.take().ok_or_else(|| {
                    ZkBenchError::validation(
                        "plugin_composition.outer_artifacts",
                        "canonical config slot was constructed more than once",
                    )
                })
            } else {
                build_ref(binding.outer_kind)
            }
        })
        .collect::<Result<Vec<_>>>()?;
    let artifacts: [crate::experiment_observability::ExperimentArtifactRef; OuterKind::SLOT_COUNT] =
        artifacts.try_into().map_err(|_| {
            ZkBenchError::validation(
                "plugin_composition.outer_artifacts",
                "canonical outer slot construction produced an unexpected cardinality",
            )
        })?;
    let outer_bundle_id = expected_outer_bundle_id(
        &config.plugin_descriptor.plugin_id,
        &config.inner_bundle_id,
        &config.experiment_id,
        &config.run_id,
    )?;
    assemble_experiment_artifact_bundle(
        outer_bundle_id,
        config.experiment_id.clone(),
        config.run_id.clone(),
        artifacts,
    )
}

fn expected_outer_bundle_id(
    plugin_id: &str,
    inner_bundle_id: &str,
    experiment_id: &str,
    run_id: &str,
) -> Result<String> {
    let material = (
        PLUGIN_COMPOSITION_ADAPTER_ID,
        plugin_id,
        inner_bundle_id,
        experiment_id,
        run_id,
    );
    let digest = compute_artifact_digest(
        &material,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Manifest),
    )?;
    Ok(format!("plugin_composition_{}", digest.hex_digest))
}

fn require_text(value: &str, path: impl Into<String>) -> Result<()> {
    if value.trim().is_empty() {
        return Err(ZkBenchError::validation(path, "value must not be empty"));
    }
    Ok(())
}

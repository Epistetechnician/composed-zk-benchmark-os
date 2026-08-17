//! One-shot orchestration from a typed plugin catalog to a durable packet.
//!
//! State slice: `benchmark-os-plugin-composition-packet-job-v1`.
//! Configuration extension: `benchmark-os-plugin-composition-packet-job-config-v1`.
//! Persistence extension: `benchmark-os-plugin-composition-packet-store-seam-v1`.
//! Request extension: `benchmark-os-plugin-composition-packet-job-storage-independent-request-v1`.
//! Keyed receipt extension: `benchmark-os-plugin-composition-packet-store-keyed-receipt-v1`.
//! Result extension: `benchmark-os-plugin-composition-packet-job-receipt-result-v1`.
//! Identity extension: `benchmark-os-plugin-composition-identity-value-v1`.
//! Identity constructor locality slice: `benchmark-os-plugin-composition-identity-constructor-locality-v1`.
//! Projector injection slice: `benchmark-os-plugin-composition-packet-job-projector-injection-v1`.
//! Output handoff validation slice: `benchmark-os-plugin-composition-output-handoff-validation-v1`.
//! Materialization handoff validation slice: `benchmark-os-plugin-composition-packet-store-materialization-handoff-validation-v1`.
//! Result handoff validation slice: `benchmark-os-plugin-composition-packet-job-result-handoff-validation-v1`.
//!
//! This module owns only job choreography: catalog resolution, generic plugin
//! composition, store materialization, strict readback, and one-shot state.
//! Plugin validation remains in the catalog/composition modules, while path
//! safety and packet integrity remain in `experiment_packet`. It does not run
//! models, invoke processes, access the network, mutate evidence, or grant
//! runtime authority.

use crate::error::{Result, ZkBenchError};
use crate::experiment_identity::PluginCompositionIdentity;
use crate::experiment_observability::ExperimentProvenance;
use crate::experiment_packet::PluginCompositionPacketOutput;
use crate::experiment_packet_store::{
    FilesystemPluginCompositionPacketStore, KeyedPluginCompositionPacketStore,
    PacketStoreDestination, PacketStoreKey, PacketStoreReceipt,
    ValidatedPacketStoreMaterialization,
};
use crate::experiment_packet_store_compat::{
    LegacyPluginCompositionPacketStoreAdapter, PluginCompositionPacketStore,
};
use crate::experiment_plugin_catalog::ExperimentPluginFactoryCatalog;
use crate::experiment_plugin_composition::{
    validate_plugin_composition_projector, PluginCompositionProjector, PluginCompositionRunner,
    StandardPluginCompositionProjector,
};

/// Storage-independent identity and provenance for one packet job.
///
/// This request is the common interface between job choreography and packet
/// persistence. It deliberately contains no output root, overwrite policy, or
/// protected path because those values belong to a filesystem store adapter.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExperimentPacketJobRequest {
    /// Registered plugin identifier.
    pub plugin_id: String,
    /// Outer experiment identity.
    pub experiment_id: String,
    /// Outer run identity.
    pub run_id: String,
    /// Provenance attached to generated packet artifacts.
    pub provenance: ExperimentProvenance,
}

impl ExperimentPacketJobRequest {
    /// Return the validated identity tuple carried by this request.
    pub fn identity(&self) -> Result<PluginCompositionIdentity> {
        PluginCompositionIdentity::new_at(
            self.plugin_id.clone(),
            self.experiment_id.clone(),
            self.run_id.clone(),
            "experiment_packet_job_request.identity",
        )
    }

    /// Validate identity and provenance without catalog or persistence access.
    pub fn validate(&self) -> Result<()> {
        self.identity()?;
        self.provenance
            .validate("experiment_packet_job_request.provenance")
    }
}

/// Typed configuration for one packet job.
///
/// This value concentrates the job's identity, provenance, output policy, and
/// protected-path invariants. It is configuration only: it does not resolve a
/// plugin, touch the filesystem, or authorize execution.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExperimentPacketJobConfig {
    /// Registered plugin identifier.
    pub plugin_id: String,
    /// Outer experiment identity.
    pub experiment_id: String,
    /// Outer run identity.
    pub run_id: String,
    /// Provenance attached to generated packet artifacts.
    pub provenance: ExperimentProvenance,
    /// Caller-owned packet store destination policy.
    pub destination: PacketStoreDestination,
}

impl ExperimentPacketJobConfig {
    /// Return the validated identity tuple carried by this configuration.
    pub fn identity(&self) -> Result<PluginCompositionIdentity> {
        self.request().identity()
    }

    /// Validate static job configuration without catalog or filesystem access.
    pub fn validate(&self) -> Result<()> {
        self.request().validate()?;
        self.destination.validate()
    }

    /// Return the storage-independent portion of this compatibility config.
    pub fn request(&self) -> ExperimentPacketJobRequest {
        ExperimentPacketJobRequest {
            plugin_id: self.plugin_id.clone(),
            experiment_id: self.experiment_id.clone(),
            run_id: self.run_id.clone(),
            provenance: self.provenance.clone(),
        }
    }
}

/// One-shot job that turns one catalog plugin into a validated durable packet.
pub struct ExperimentPacketJob {
    config: ExperimentPacketJobConfig,
    execution: ExperimentPacketJobExecution,
}

/// One-shot packet job built from a storage-independent request.
///
/// This type is used when the caller supplies a non-filesystem store. It
/// exposes the same orchestration and readback contract as
/// `ExperimentPacketJob` without carrying filesystem-only configuration.
pub struct StorageIndependentExperimentPacketJob {
    execution: ExperimentPacketJobExecution,
}

/// Validated packet-job output together with the receipt required for later
/// keyed readback.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExperimentPacketJobResult {
    materialization: ValidatedPacketStoreMaterialization,
}

impl ExperimentPacketJobResult {
    fn from_materialization(materialization: ValidatedPacketStoreMaterialization) -> Self {
        Self { materialization }
    }

    /// Borrow the typed packet output after strict readback.
    pub fn output(&self) -> &PluginCompositionPacketOutput {
        self.materialization.output()
    }

    /// Borrow the receipt bound to the returned packet output.
    pub fn receipt(&self) -> &PacketStoreReceipt {
        self.materialization.receipt()
    }

    /// Consume the result while preserving its validated receipt/output seam.
    pub fn into_materialization(self) -> ValidatedPacketStoreMaterialization {
        self.materialization
    }
}

struct ExperimentPacketJobExecution {
    catalog: ExperimentPluginFactoryCatalog,
    request: ExperimentPacketJobRequest,
    store: Box<dyn KeyedPluginCompositionPacketStore>,
    projector: Option<Box<dyn PluginCompositionProjector>>,
    attempted: bool,
}

impl ExperimentPacketJobExecution {
    fn new(
        catalog: ExperimentPluginFactoryCatalog,
        request: ExperimentPacketJobRequest,
        store: Box<dyn KeyedPluginCompositionPacketStore>,
        projector: Box<dyn PluginCompositionProjector>,
    ) -> Result<Self> {
        catalog.validate()?;
        request.validate()?;
        validate_plugin_composition_projector(projector.as_ref())?;
        if catalog.resolve(&request.plugin_id).is_none() {
            return Err(ZkBenchError::validation(
                "experiment_packet_job_request.plugin_id",
                format!("plugin {} is not registered", request.plugin_id),
            ));
        }
        Ok(Self {
            catalog,
            request,
            store,
            projector: Some(projector),
            attempted: false,
        })
    }

    fn run_once(&mut self) -> Result<ExperimentPacketJobResult> {
        if self.attempted {
            return Err(ZkBenchError::validation(
                "experiment_packet_job",
                "packet jobs are one-shot and cannot be run twice",
            ));
        }
        self.attempted = true;

        let identity = self.request.identity()?;
        let key = PacketStoreKey::from_identity(identity.clone());
        let plugin = self.catalog.instantiate(&self.request.plugin_id)?;
        let projector = self.projector.take().ok_or_else(|| {
            ZkBenchError::validation(
                "experiment_packet_job.projector",
                "packet job projector is unavailable after the one-shot transition",
            )
        })?;
        let composition = PluginCompositionRunner::new_with_identity_and_projector(
            plugin,
            identity,
            self.request.provenance.clone(),
            projector,
        )?
        .run_validated_output()?;
        let packet = composition.into_packet();
        let materialized = self.store.materialize_keyed_validated(&key, &packet)?;
        let read = self
            .store
            .readback_keyed(materialized.receipt())
            .map_err(|error| {
                ZkBenchError::validation(
                    "experiment_packet_job.readback",
                    format!("receipt-bound packet readback failed: {error}"),
                )
            })?;
        if materialized.output() != &read {
            return Err(ZkBenchError::validation(
                "experiment_packet_job.readback",
                "receipt-bound packet readback does not equal the materialized output",
            ));
        }
        let (_, receipt) = materialized.into_parts();
        let rebound = ValidatedPacketStoreMaterialization::new(read, receipt)?;
        Ok(ExperimentPacketJobResult::from_materialization(rebound))
    }
}

impl ExperimentPacketJob {
    fn standard_projector() -> Box<dyn PluginCompositionProjector> {
        Box::new(StandardPluginCompositionProjector)
    }

    /// Construct a packet job after validating all static job inputs.
    ///
    /// Constructor validation resolves the plugin descriptor but does not
    /// instantiate or execute it, and does not touch the output root.
    pub fn new(
        catalog: ExperimentPluginFactoryCatalog,
        config: ExperimentPacketJobConfig,
    ) -> Result<Self> {
        config.validate()?;
        let store = FilesystemPluginCompositionPacketStore::new(config.destination.clone())?;
        let execution = ExperimentPacketJobExecution::new(
            catalog,
            config.request(),
            Box::new(store),
            Self::standard_projector(),
        )?;
        Ok(Self { config, execution })
    }

    /// Construct a filesystem-backed job with an explicit runtime projector.
    ///
    /// The projector is descriptor-validated during construction and its
    /// identity is retained by newly emitted composition configs; packet wire
    /// fields and durable manifest contracts stay owned by the existing
    /// composition and store modules.
    pub fn new_with_projector(
        catalog: ExperimentPluginFactoryCatalog,
        config: ExperimentPacketJobConfig,
        projector: Box<dyn PluginCompositionProjector>,
    ) -> Result<Self> {
        config.validate()?;
        let store = FilesystemPluginCompositionPacketStore::new(config.destination.clone())?;
        let execution = ExperimentPacketJobExecution::new(
            catalog,
            config.request(),
            Box::new(store),
            projector,
        )?;
        Ok(Self { config, execution })
    }

    /// Construct a packet job with an explicit persistence adapter.
    pub fn new_with_store(
        catalog: ExperimentPluginFactoryCatalog,
        config: ExperimentPacketJobConfig,
        store: Box<dyn PluginCompositionPacketStore>,
    ) -> Result<Self> {
        config.validate()?;
        let store = Box::new(LegacyPluginCompositionPacketStoreAdapter::new(store));
        let execution = ExperimentPacketJobExecution::new(
            catalog,
            config.request(),
            store,
            Self::standard_projector(),
        )?;
        Ok(Self { config, execution })
    }

    /// Construct a packet job with the receipt-bound persistence interface.
    pub fn new_with_keyed_store(
        catalog: ExperimentPluginFactoryCatalog,
        config: ExperimentPacketJobConfig,
        store: Box<dyn KeyedPluginCompositionPacketStore>,
    ) -> Result<Self> {
        config.validate()?;
        let execution = ExperimentPacketJobExecution::new(
            catalog,
            config.request(),
            store,
            Self::standard_projector(),
        )?;
        Ok(Self { config, execution })
    }

    /// Construct a job with an explicit projector and receipt-bound store.
    pub fn new_with_projector_and_keyed_store(
        catalog: ExperimentPluginFactoryCatalog,
        config: ExperimentPacketJobConfig,
        projector: Box<dyn PluginCompositionProjector>,
        store: Box<dyn KeyedPluginCompositionPacketStore>,
    ) -> Result<Self> {
        config.validate()?;
        let execution =
            ExperimentPacketJobExecution::new(catalog, config.request(), store, projector)?;
        Ok(Self { config, execution })
    }

    /// Construct a packet job without filesystem-shaped configuration.
    pub fn new_with_request_and_store(
        catalog: ExperimentPluginFactoryCatalog,
        request: ExperimentPacketJobRequest,
        store: Box<dyn PluginCompositionPacketStore>,
    ) -> Result<StorageIndependentExperimentPacketJob> {
        let store = Box::new(LegacyPluginCompositionPacketStoreAdapter::new(store));
        Ok(StorageIndependentExperimentPacketJob {
            execution: ExperimentPacketJobExecution::new(
                catalog,
                request,
                store,
                Self::standard_projector(),
            )?,
        })
    }

    /// Construct a storage-independent job with the receipt-bound store seam.
    pub fn new_with_request_and_keyed_store(
        catalog: ExperimentPluginFactoryCatalog,
        request: ExperimentPacketJobRequest,
        store: Box<dyn KeyedPluginCompositionPacketStore>,
    ) -> Result<StorageIndependentExperimentPacketJob> {
        Ok(StorageIndependentExperimentPacketJob {
            execution: ExperimentPacketJobExecution::new(
                catalog,
                request,
                store,
                Self::standard_projector(),
            )?,
        })
    }

    /// Construct a storage-independent job with an explicit projector.
    pub fn new_with_request_and_projector_and_keyed_store(
        catalog: ExperimentPluginFactoryCatalog,
        request: ExperimentPacketJobRequest,
        projector: Box<dyn PluginCompositionProjector>,
        store: Box<dyn KeyedPluginCompositionPacketStore>,
    ) -> Result<StorageIndependentExperimentPacketJob> {
        Ok(StorageIndependentExperimentPacketJob {
            execution: ExperimentPacketJobExecution::new(catalog, request, store, projector)?,
        })
    }

    /// Return the validated immutable job configuration.
    pub fn config(&self) -> &ExperimentPacketJobConfig {
        &self.config
    }

    /// Return the selected plugin identifier.
    pub fn plugin_id(&self) -> &str {
        &self.config.plugin_id
    }

    /// Return the caller-owned packet output root.
    pub fn output_root(&self) -> &std::path::Path {
        &self.config.destination.output_root
    }

    /// Run the job exactly once and return only after strict packet readback.
    pub fn run_once(&mut self) -> Result<PluginCompositionPacketOutput> {
        Ok(self.run_once_with_receipt()?.output().clone())
    }

    /// Run the job exactly once and retain the receipt-bound result.
    pub fn run_once_with_receipt(&mut self) -> Result<ExperimentPacketJobResult> {
        self.execution.run_once()
    }
}

impl StorageIndependentExperimentPacketJob {
    /// Return the storage-independent validated request.
    pub fn request(&self) -> &ExperimentPacketJobRequest {
        &self.execution.request
    }

    /// Return the selected plugin identifier.
    pub fn plugin_id(&self) -> &str {
        &self.execution.request.plugin_id
    }

    /// Run the job exactly once and return only after strict packet readback.
    pub fn run_once(&mut self) -> Result<PluginCompositionPacketOutput> {
        Ok(self.run_once_with_receipt()?.output().clone())
    }

    /// Run the storage-independent job and retain the receipt-bound result.
    pub fn run_once_with_receipt(&mut self) -> Result<ExperimentPacketJobResult> {
        self.execution.run_once()
    }
}

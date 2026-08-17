//! Persistence seam for generic plugin-composition packets.
//!
//! State slice: `benchmark-os-plugin-composition-packet-store-seam-v1`.
//! Keyed receipt extension: `benchmark-os-plugin-composition-packet-store-keyed-receipt-v1`.
//! Identity extension: `benchmark-os-plugin-composition-identity-value-v1`.
//! Compatibility extension: `benchmark-os-plugin-composition-packet-store-legacy-seam-containment-v1`.
//! Identity constructor locality slice: `benchmark-os-plugin-composition-identity-constructor-locality-v1`.
//! Materialization handoff validation slice: `benchmark-os-plugin-composition-packet-store-materialization-handoff-validation-v1`.
//! Typed receipt binding slice: `benchmark-os-plugin-composition-packet-store-receipt-typed-binding-v1`.
//! Canonical typed transport slice: `benchmark-os-experiment-packet-canonical-typed-transport-v1`.
//! Typed job readback slice: `benchmark-os-plugin-composition-packet-job-typed-readback-v1`.
//!
//! This module separates packet-job choreography from packet persistence. The
//! filesystem adapter delegates to the existing canonical writer and reader;
//! the in-memory adapter uses the same canonical output builder for tests and
//! local composition without a filesystem. No adapter adds atomic publication,
//! execution, network access, evidence mutation, or runtime authority.

use std::collections::BTreeMap;
use std::path::PathBuf;

use crate::error::{Result, ZkBenchError};
use crate::evidence::ArtifactDigest;
use crate::experiment_identity::PluginCompositionIdentity;
use crate::experiment_packet::{
    build_plugin_composition_packet_output, compute_experiment_packet_manifest_digest,
    read_plugin_composition_packet_outputs, read_plugin_composition_packet_outputs_validated,
    write_plugin_composition_packet_outputs, write_plugin_composition_packet_outputs_validated,
    PluginCompositionPacket, PluginCompositionPacketOutput, ValidatedExperimentPacketOutput,
    ValidatedPluginCompositionPacketOutput,
};

pub use crate::experiment_packet_store_compat::{
    LegacyPluginCompositionPacketStoreAdapter, PluginCompositionPacketStore,
};

/// Stable identity used to address one packet-store materialization.
///
/// The key is deliberately derived from the typed plugin-composition config,
/// not from a filesystem path or a caller's import ordering. It is local
/// metadata identity only and does not authorize execution or publication.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub struct PacketStoreKey {
    /// Registered plugin identifier.
    pub plugin_id: String,
    /// Outer experiment identity.
    pub experiment_id: String,
    /// Outer run identity.
    pub run_id: String,
}

impl PacketStoreKey {
    /// Construct and validate one packet-store key.
    pub fn new(
        plugin_id: impl Into<String>,
        experiment_id: impl Into<String>,
        run_id: impl Into<String>,
    ) -> Result<Self> {
        let identity = PluginCompositionIdentity::new(plugin_id, experiment_id, run_id)?;
        Ok(Self::from_identity(identity))
    }

    /// Construct a packet-store key from a validated typed identity.
    pub fn from_identity(identity: PluginCompositionIdentity) -> Self {
        Self {
            plugin_id: identity.plugin_id,
            experiment_id: identity.experiment_id,
            run_id: identity.run_id,
        }
    }

    /// Return this key as the shared typed identity value.
    pub fn identity(&self) -> Result<PluginCompositionIdentity> {
        PluginCompositionIdentity::new_at(
            self.plugin_id.clone(),
            self.experiment_id.clone(),
            self.run_id.clone(),
            "packet_store_key.identity",
        )
    }

    /// Derive the key from a typed packet before it reaches a store adapter.
    pub fn from_packet(packet: &PluginCompositionPacket) -> Result<Self> {
        Ok(Self::from_identity(packet.composition_config.identity()?))
    }

    /// Validate key shape without touching storage.
    pub fn validate(&self) -> Result<()> {
        self.identity().map(|_| ())
    }

    pub(crate) fn validate_against_packet(&self, packet: &PluginCompositionPacket) -> Result<()> {
        let expected = Self::from_packet(packet)?;
        if self != &expected {
            return Err(ZkBenchError::validation(
                "packet_store_key",
                "packet-store key does not match the packet composition identity",
            ));
        }
        Ok(())
    }

    fn validate_against_output(&self, output: &PluginCompositionPacketOutput) -> Result<()> {
        self.validate_against_packet(&output.packet)?;
        if output.manifest.experiment_id != self.experiment_id
            || output.manifest.run_id != self.run_id
        {
            return Err(ZkBenchError::validation(
                "packet_store_key.manifest",
                "packet-store key does not match the packet manifest identity",
            ));
        }
        Ok(())
    }
}

/// Receipt returned by a keyed store after validating one materialization.
///
/// A caller must present this receipt to read back the packet. The manifest
/// digest makes a stale or cross-run output fail closed even when a legacy
/// adapter internally retains only one materialization.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PacketStoreReceipt {
    /// Key used for the materialization.
    pub key: PacketStoreKey,
    /// Digest of the canonical packet manifest returned by the store.
    pub manifest_digest: ArtifactDigest,
}

impl PacketStoreReceipt {
    /// Issue a receipt from a validated generic packet output handoff.
    pub fn from_validated_output(
        key: PacketStoreKey,
        output: &crate::experiment_packet::ValidatedPluginCompositionPacketOutput,
    ) -> Result<Self> {
        let raw_output = output.as_output();
        key.validate_against_output(raw_output)?;
        let manifest_digest = compute_experiment_packet_manifest_digest(&raw_output.manifest)?;
        if manifest_digest != *output.manifest_digest() {
            return Err(ZkBenchError::validation(
                "packet_store_receipt.manifest_digest",
                "validated packet output manifest digest does not match canonical bytes",
            ));
        }
        Ok(Self {
            key,
            manifest_digest,
        })
    }

    /// Build a receipt only from a canonical output bound to the supplied key.
    pub fn from_output(
        key: PacketStoreKey,
        output: &PluginCompositionPacketOutput,
    ) -> Result<Self> {
        let validated = output.clone().into_validated()?;
        Self::from_validated_output(key, &validated)
    }

    /// Validate the receipt against a freshly read canonical output.
    pub fn validate_output(&self, output: &PluginCompositionPacketOutput) -> Result<()> {
        self.key.validate_against_output(output)?;
        let expected = Self::from_output(self.key.clone(), output)?;
        if self != &expected {
            return Err(ZkBenchError::validation(
                "packet_store_receipt",
                "packet-store receipt does not match the readback output",
            ));
        }
        Ok(())
    }
}

/// Typed materialization plus the receipt required for readback.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PacketStoreMaterialization {
    /// Canonical output produced by the store.
    pub output: PluginCompositionPacketOutput,
    /// Receipt that keys and binds the output.
    pub receipt: PacketStoreReceipt,
}

impl PacketStoreMaterialization {
    /// Construct a receipt-bound materialization from canonical output.
    pub fn from_output(key: PacketStoreKey, output: PluginCompositionPacketOutput) -> Result<Self> {
        let receipt = PacketStoreReceipt::from_output(key, &output)?;
        Ok(Self { output, receipt })
    }

    /// Revalidate this public compatibility shape before a downstream Adapter
    /// treats its output and receipt as one trusted handoff.
    pub fn into_validated(self) -> Result<ValidatedPacketStoreMaterialization> {
        ValidatedPacketStoreMaterialization::new(self.output, self.receipt)
    }
}

/// Invariant-bearing materialization returned from the keyed store Seam.
///
/// The receipt and packet output are private so a downstream Adapter cannot
/// assemble an unchecked pair after the store has validated them. Legacy
/// materialization remains available through `into_legacy`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValidatedPacketStoreMaterialization {
    output: ValidatedExperimentPacketOutput<
        crate::experiment_plugin_composition::PluginCompositionConfig,
    >,
    receipt: PacketStoreReceipt,
}

impl ValidatedPacketStoreMaterialization {
    /// Construct a validated receipt/output handoff.
    pub fn new(output: PluginCompositionPacketOutput, receipt: PacketStoreReceipt) -> Result<Self> {
        let output = ValidatedExperimentPacketOutput::from_output(output)?;
        Self::from_validated_output(output, receipt)
    }

    /// Construct a receipt-bound handoff from an already validated packet
    /// output without downgrading it through the legacy public shape.
    pub fn from_validated_output(
        output: ValidatedPluginCompositionPacketOutput,
        receipt: PacketStoreReceipt,
    ) -> Result<Self> {
        let expected = PacketStoreReceipt::from_validated_output(receipt.key.clone(), &output)?;
        if receipt != expected {
            return Err(ZkBenchError::validation(
                "packet_store_materialization.receipt",
                "packet-store receipt does not match the validated packet output",
            ));
        }
        Ok(Self { output, receipt })
    }

    /// Borrow the validated packet output.
    pub fn output(&self) -> &PluginCompositionPacketOutput {
        self.output.as_output()
    }

    /// Borrow the validated packet output without reopening its legacy shape.
    pub fn validated_output(&self) -> &ValidatedPluginCompositionPacketOutput {
        &self.output
    }

    /// Borrow the receipt bound to the validated packet output.
    pub fn receipt(&self) -> &PacketStoreReceipt {
        &self.receipt
    }

    /// Return the validated output and receipt to the next Adapter.
    pub fn into_parts(self) -> (PluginCompositionPacketOutput, PacketStoreReceipt) {
        (self.output.into_output(), self.receipt)
    }

    /// Return the historical public materialization shape.
    pub fn into_legacy(self) -> PacketStoreMaterialization {
        let (output, receipt) = self.into_parts();
        PacketStoreMaterialization { output, receipt }
    }
}

/// Caller-owned filesystem destination policy for one packet store.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PacketStoreDestination {
    /// Packet output root owned by the caller.
    pub output_root: PathBuf,
    /// Whether an identical existing packet may be rewritten.
    pub overwrite: bool,
    /// Roots that packet materialization must never overlap.
    pub protected_paths: Vec<PathBuf>,
}

impl PacketStoreDestination {
    /// Validate static destination values without touching the filesystem.
    pub fn validate(&self) -> Result<()> {
        if self.output_root.as_os_str().is_empty() {
            return Err(ZkBenchError::validation(
                "packet_store.destination.output_root",
                "output root must not be empty",
            ));
        }
        for (index, path) in self.protected_paths.iter().enumerate() {
            if path.as_os_str().is_empty() {
                return Err(ZkBenchError::validation(
                    format!("packet_store.destination.protected_paths[{index}]"),
                    "protected path must not be empty",
                ));
            }
        }
        Ok(())
    }
}

/// Keyed persistence interface used by the current packet-job path.
pub trait KeyedPluginCompositionPacketStore {
    /// Materialize one packet under an explicit identity and return its receipt.
    fn materialize_keyed(
        &mut self,
        key: &PacketStoreKey,
        packet: &PluginCompositionPacket,
    ) -> Result<PacketStoreMaterialization>;

    /// Materialize and return one invariant-bearing receipt/output handoff.
    ///
    /// The legacy method remains the required compatibility Interface. This
    /// additive method validates its public result at the keyed store Seam so
    /// custom Adapters receive the same fail-closed contract as built-ins.
    fn materialize_keyed_validated(
        &mut self,
        key: &PacketStoreKey,
        packet: &PluginCompositionPacket,
    ) -> Result<ValidatedPacketStoreMaterialization> {
        self.materialize_keyed(key, packet)?.into_validated()
    }

    /// Read back only the materialization named by a valid receipt.
    fn readback_keyed(&self, receipt: &PacketStoreReceipt)
        -> Result<PluginCompositionPacketOutput>;

    /// Read back and return one invariant-bearing receipt/output handoff.
    ///
    /// The legacy method remains the required compatibility Interface. This
    /// additive method validates its public result at the keyed store Seam so
    /// custom Adapters receive the same fail-closed contract as built-ins.
    fn readback_keyed_validated(
        &self,
        receipt: &PacketStoreReceipt,
    ) -> Result<ValidatedPacketStoreMaterialization> {
        receipt.key.validate()?;
        let output = self.readback_keyed(receipt)?;
        ValidatedPacketStoreMaterialization::new(output, receipt.clone())
    }
}

/// Filesystem adapter over the existing canonical packet writer and reader.
pub struct FilesystemPluginCompositionPacketStore {
    destination: PacketStoreDestination,
}

impl FilesystemPluginCompositionPacketStore {
    /// Construct a filesystem store without touching its destination.
    pub fn new(destination: PacketStoreDestination) -> Result<Self> {
        destination.validate()?;
        Ok(Self { destination })
    }

    /// Return the immutable destination policy owned by this adapter.
    pub fn destination(&self) -> &PacketStoreDestination {
        &self.destination
    }
}

impl PluginCompositionPacketStore for FilesystemPluginCompositionPacketStore {
    fn materialize(
        &mut self,
        packet: &PluginCompositionPacket,
    ) -> Result<PluginCompositionPacketOutput> {
        write_plugin_composition_packet_outputs(
            &self.destination.output_root,
            packet,
            self.destination.overwrite,
            &self.destination.protected_paths,
        )
    }

    fn readback(&self) -> Result<PluginCompositionPacketOutput> {
        read_plugin_composition_packet_outputs(
            &self.destination.output_root,
            &self.destination.protected_paths,
        )
    }
}

impl KeyedPluginCompositionPacketStore for FilesystemPluginCompositionPacketStore {
    fn materialize_keyed(
        &mut self,
        key: &PacketStoreKey,
        packet: &PluginCompositionPacket,
    ) -> Result<PacketStoreMaterialization> {
        self.materialize_keyed_validated(key, packet)
            .map(ValidatedPacketStoreMaterialization::into_legacy)
    }

    fn materialize_keyed_validated(
        &mut self,
        key: &PacketStoreKey,
        packet: &PluginCompositionPacket,
    ) -> Result<ValidatedPacketStoreMaterialization> {
        key.validate_against_packet(packet)?;
        let output = write_plugin_composition_packet_outputs_validated(
            &self.destination.output_root,
            packet,
            self.destination.overwrite,
            &self.destination.protected_paths,
        )?;
        let receipt = PacketStoreReceipt::from_validated_output(key.clone(), &output)?;
        ValidatedPacketStoreMaterialization::from_validated_output(output, receipt)
    }

    fn readback_keyed(
        &self,
        receipt: &PacketStoreReceipt,
    ) -> Result<PluginCompositionPacketOutput> {
        self.readback_keyed_validated(receipt)
            .map(|handoff| handoff.into_parts().0)
    }

    fn readback_keyed_validated(
        &self,
        receipt: &PacketStoreReceipt,
    ) -> Result<ValidatedPacketStoreMaterialization> {
        receipt.key.validate()?;
        let output = read_plugin_composition_packet_outputs_validated(
            &self.destination.output_root,
            &self.destination.protected_paths,
        )?;
        receipt.validate_output(output.as_output())?;
        ValidatedPacketStoreMaterialization::from_validated_output(output, receipt.clone())
    }
}

/// In-memory adapter over the same canonical packet-output builder.
///
/// This adapter is intentionally local and non-durable. It provides a real
/// second implementation of the job's persistence contract without implying
/// publication, execution, evidence acceptance, or runtime authority.
#[derive(Default)]
pub struct InMemoryPluginCompositionPacketStore {
    materialized: BTreeMap<PacketStoreKey, ValidatedPacketStoreMaterialization>,
    legacy_last_key: Option<PacketStoreKey>,
}

impl InMemoryPluginCompositionPacketStore {
    /// Construct an empty in-memory packet store.
    pub fn new() -> Self {
        Self::default()
    }
}

impl PluginCompositionPacketStore for InMemoryPluginCompositionPacketStore {
    fn materialize(
        &mut self,
        packet: &PluginCompositionPacket,
    ) -> Result<PluginCompositionPacketOutput> {
        let key = PacketStoreKey::from_packet(packet)?;
        let handoff = <Self as KeyedPluginCompositionPacketStore>::materialize_keyed_validated(
            self, &key, packet,
        )?;
        self.legacy_last_key = Some(key);
        Ok(handoff.output().clone())
    }

    fn readback(&self) -> Result<PluginCompositionPacketOutput> {
        let key = self.legacy_last_key.as_ref().ok_or_else(|| {
            ZkBenchError::validation(
                "packet_store.in_memory",
                "packet readback requested before materialization",
            )
        })?;
        self.materialized
            .get(key)
            .map(|materialization| materialization.output().clone())
            .ok_or_else(|| {
                ZkBenchError::validation(
                    "packet_store.in_memory",
                    "legacy packet readback key is no longer materialized",
                )
            })
    }
}

impl KeyedPluginCompositionPacketStore for InMemoryPluginCompositionPacketStore {
    fn materialize_keyed(
        &mut self,
        key: &PacketStoreKey,
        packet: &PluginCompositionPacket,
    ) -> Result<PacketStoreMaterialization> {
        self.materialize_keyed_validated(key, packet)
            .map(ValidatedPacketStoreMaterialization::into_legacy)
    }

    fn materialize_keyed_validated(
        &mut self,
        key: &PacketStoreKey,
        packet: &PluginCompositionPacket,
    ) -> Result<ValidatedPacketStoreMaterialization> {
        key.validate_against_packet(packet)?;
        let output = build_plugin_composition_packet_output(packet)?;
        let receipt = PacketStoreReceipt::from_validated_output(key.clone(), &output)?;
        let materialization =
            ValidatedPacketStoreMaterialization::from_validated_output(output, receipt)?;
        self.materialized
            .insert(key.clone(), materialization.clone());
        Ok(materialization)
    }

    fn readback_keyed(
        &self,
        receipt: &PacketStoreReceipt,
    ) -> Result<PluginCompositionPacketOutput> {
        self.readback_keyed_validated(receipt)
            .map(|handoff| handoff.into_parts().0)
    }

    fn readback_keyed_validated(
        &self,
        receipt: &PacketStoreReceipt,
    ) -> Result<ValidatedPacketStoreMaterialization> {
        receipt.key.validate()?;
        let materialization = self.materialized.get(&receipt.key).ok_or_else(|| {
            ZkBenchError::validation(
                "packet_store.in_memory",
                "requested packet-store key has no materialization",
            )
        })?;
        ValidatedPacketStoreMaterialization::new(materialization.output().clone(), receipt.clone())
    }
}

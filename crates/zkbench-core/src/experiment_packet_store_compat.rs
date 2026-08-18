//! Compatibility-only packet-store seam.
//!
//! State slice: `benchmark-os-plugin-composition-packet-store-legacy-seam-containment-v1`.
//!
//! The keyed receipt-bound store is the current packet-job interface. This
//! module contains the historical unkeyed interface and its upgrade adapter so
//! compatibility code stays visible and cannot be mistaken for the active
//! storage contract. The root crate continues to re-export these names for
//! source compatibility. No packet wire shape, persistence policy, execution,
//! evidence, or runtime authority is added here.

use crate::error::Result;
use crate::experiment_packet::{PluginCompositionPacket, PluginCompositionPacketOutput};
use crate::experiment_packet_store::{
    KeyedPluginCompositionPacketStore, PacketStoreKey, PacketStoreMaterialization,
    PacketStoreReceipt,
};

/// Historical unkeyed persistence interface retained for source compatibility.
///
/// New packet-store adapters should implement
/// [`KeyedPluginCompositionPacketStore`] so materialization and readback are
/// bound to an explicit plugin/experiment/run identity and receipt.
pub trait PluginCompositionPacketStore {
    /// Materialize one validated packet and return the typed written value.
    fn materialize(
        &mut self,
        packet: &PluginCompositionPacket,
    ) -> Result<PluginCompositionPacketOutput>;

    /// Read the most recent materialized packet through the adapter's policy.
    fn readback(&self) -> Result<PluginCompositionPacketOutput>;
}

/// Compatibility adapter that upgrades the historical unkeyed interface.
///
/// The wrapped adapter cannot select storage by key internally, so receipt
/// validation remains the fail-closed protection against stale or cross-run
/// readback. New adapters should implement the keyed interface directly.
pub struct LegacyPluginCompositionPacketStoreAdapter {
    inner: Box<dyn PluginCompositionPacketStore>,
}

impl LegacyPluginCompositionPacketStoreAdapter {
    /// Wrap one historical store for compatibility constructors.
    pub fn new(inner: Box<dyn PluginCompositionPacketStore>) -> Self {
        Self { inner }
    }
}

impl KeyedPluginCompositionPacketStore for LegacyPluginCompositionPacketStoreAdapter {
    fn materialize_keyed(
        &mut self,
        key: &PacketStoreKey,
        packet: &PluginCompositionPacket,
    ) -> Result<PacketStoreMaterialization> {
        key.validate_against_packet(packet)?;
        let output = self.inner.materialize(packet)?;
        PacketStoreMaterialization::from_output(key.clone(), output)
    }

    fn readback_keyed(
        &self,
        receipt: &PacketStoreReceipt,
    ) -> Result<PluginCompositionPacketOutput> {
        let output = self.inner.readback()?;
        receipt.validate_output(&output)?;
        Ok(output)
    }
}

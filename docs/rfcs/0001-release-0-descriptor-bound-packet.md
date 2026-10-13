# RFC 0001: Release 0 descriptor-bound packet storage

- Status: implemented as an unexported slice
- State slice: `release-0-descriptor-bound-packet-v1`
- Scope: local descriptor-bound composition and receipt-bound packet storage

## Summary

Release 0 adds a standalone Rust module at
`crates/zkbench-core/src/packet.rs`. It models one packet produced by one
plugin descriptor and stores it in memory behind a canonical receipt. The
integration test includes the module by path because this slice is not yet
exported from `crates/zkbench-core/src/lib.rs`.

The module is transport and validation plumbing. It does not discover or load
plugins, execute a plugin, dereference a source URI, make a network request,
run a process, access a model or GPU, write durable files, claim filesystem
atomicity, or promote evidence.

## Data contract

`PluginDescriptor::new(plugin_id, plugin_version)` constructs the descriptor
and computes its SHA-256 digest from the descriptor schema version, plugin ID,
and plugin version. `PacketSlot::new` copies that descriptor binding and the
packet/run identity into each slot. Its `SourceRef` retains an opaque URI and
the SHA-256 digest of the supplied local payload bytes; the module never opens
the URI.

`Packet::new` requires:

1. a non-empty packet ID and run ID;
2. one valid plugin descriptor;
3. a unique declared set of required slot IDs; and
4. exactly one valid slot for every required ID.

The required slot set is non-empty.

Validation rejects duplicate or missing slots, undeclared slots, stale source
digests, cross-run slot identities, packet-ID mismatches, and plugin
ID/version/descriptor-digest mismatches. Slot ordering is not semantic.

`Packet::canonical_digest` sorts required IDs and slots before hashing their
canonical JSON representation. `PacketReceipt::for_packet` computes a
canonical slot digest and receipt digest for every slot, then a packet receipt
digest over the sorted slot receipts and packet digest.

## Storage contract

`InMemoryPacketStore::put(packet)` validates the packet, rejects a duplicate
packet/run identity, stores the packet, and returns its canonical
`PacketReceipt`. `InMemoryPacketStore::read(identity, receipt)` requires the
exact identity and exact stored receipt. It rejects cross-run receipts,
mismatched identities, stale/tampered receipt digests, and absent packet
identities. Storage has no replacement or deletion API in this slice, so a
receipt cannot silently follow a new packet under the same key.

The store is process-local and deterministic. It is not a durability,
crash-consistency, atomic-publication, or multi-process coordination
boundary.

## Required integration exports

The implementation intentionally does not edit `src/lib.rs` or any existing
module. A follow-up integration change must add:

```rust
pub mod packet;
```

If the crate's root API convention requires flat re-exports, the smallest
optional export is:

```rust
pub use packet::{
    Digest256, InMemoryPacketStore, Packet, PacketError, PacketIdentity,
    PacketReceipt, PacketSlot, PluginBinding, PluginDescriptor, Result,
    SlotReceipt, SourceRef,
};
```

That follow-up must remain separate from this state slice because modifying
`lib.rs`, `Cargo.toml`, or existing modules was explicitly out of scope.

## Verification

The focused test file is
`crates/zkbench-core/tests/packet.rs`. It covers canonical order
independence, valid readback, duplicate and missing slots, stale source
digests, cross-run slots, plugin mismatches, duplicate packet identities,
tampered/missing receipt slots, and cross-run receipts.

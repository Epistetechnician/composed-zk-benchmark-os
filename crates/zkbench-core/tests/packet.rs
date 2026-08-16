//! Focused tests for state slice `release-0-descriptor-bound-packet-v1`.

#[path = "../src/packet.rs"]
mod packet;

use packet::{
    Digest256, InMemoryPacketStore, Packet, PacketError, PacketIdentity, PacketReceipt, PacketSlot,
    PluginDescriptor,
};

fn fixture() -> (Packet, PacketIdentity, PluginDescriptor) {
    let identity = PacketIdentity::new("packet-1", "run-1").expect("identity is valid");
    let plugin = PluginDescriptor::new("plugin.alpha", "1.2.3").expect("descriptor is valid");
    let slots = vec![
        PacketSlot::new(
            "config",
            &identity,
            &plugin,
            "fixtures/config.json",
            br#"{"seed":7}"#.to_vec(),
        )
        .expect("config slot is valid"),
        PacketSlot::new(
            "result",
            &identity,
            &plugin,
            "fixtures/result.json",
            br#"{"status":"local"}"#.to_vec(),
        )
        .expect("result slot is valid"),
    ];
    let packet = Packet::new(
        identity.clone(),
        plugin.clone(),
        vec!["result".to_string(), "config".to_string()],
        slots,
    )
    .expect("packet is valid");
    (packet, identity, plugin)
}

#[test]
fn valid_packet_round_trips_through_receipt_bound_store() {
    let (packet, identity, plugin) = fixture();
    let mut store = InMemoryPacketStore::new();

    let receipt = store.put(packet.clone()).expect("put succeeds");
    let readback = store
        .read(&identity, &receipt)
        .expect("exact receipt reads packet");

    assert_eq!(readback, packet);
    assert_eq!(
        Digest256::parse(plugin.descriptor_digest.as_str())
            .expect("stored digest is canonical")
            .as_str(),
        plugin.descriptor_digest.as_str()
    );
    assert_eq!(store.len(), 1);
    assert!(!store.is_empty());
}

#[test]
fn canonical_packet_and_receipt_digests_ignore_slot_order() {
    let (packet, identity, plugin) = fixture();
    let reversed = Packet::new(
        identity,
        plugin,
        packet.required_slots.clone(),
        packet.slots.iter().cloned().rev().collect(),
    )
    .expect("reordered packet is valid");

    assert_eq!(
        packet.canonical_digest().expect("digest succeeds"),
        reversed.canonical_digest().expect("digest succeeds")
    );
    assert_eq!(
        PacketReceipt::for_packet(&packet).expect("receipt succeeds"),
        PacketReceipt::for_packet(&reversed).expect("receipt succeeds")
    );
}

#[test]
fn duplicate_and_missing_slots_are_rejected() {
    let (packet, identity, plugin) = fixture();
    let duplicate = Packet::new(
        identity.clone(),
        plugin.clone(),
        vec!["config".to_string()],
        vec![packet.slots[0].clone(), packet.slots[0].clone()],
    );
    assert!(matches!(duplicate, Err(PacketError::DuplicateSlot(_))));

    let missing = Packet::new(
        identity.clone(),
        plugin.clone(),
        vec![
            "config".to_string(),
            "result".to_string(),
            "report".to_string(),
        ],
        packet.slots,
    );
    assert!(matches!(missing, Err(PacketError::MissingSlot(slot)) if slot == "report"));

    let empty = Packet::new(identity, plugin, Vec::new(), Vec::new());
    assert!(matches!(
        empty,
        Err(PacketError::MissingSlot(slot)) if slot == "<required-slot>"
    ));
}

#[test]
fn stale_cross_run_and_mismatched_slots_are_rejected() {
    let (packet, identity, plugin) = fixture();

    let mut stale = packet.clone();
    stale.slots[0].source.digest = Digest256::from_bytes(b"changed");
    assert!(matches!(
        stale.validate(),
        Err(PacketError::StaleSlot { slot_id }) if slot_id == "config"
    ));

    let other_identity = PacketIdentity::new("packet-1", "run-2").expect("identity is valid");
    let cross_run_slot = PacketSlot::new(
        "config",
        &other_identity,
        &plugin,
        "fixtures/config.json",
        br#"{"seed":7}"#.to_vec(),
    )
    .expect("slot is internally valid");
    let cross_run = Packet::new(
        identity.clone(),
        plugin.clone(),
        vec!["config".to_string()],
        vec![cross_run_slot],
    );
    assert!(matches!(cross_run, Err(PacketError::CrossRunSlot { .. })));

    let other_plugin = PluginDescriptor::new("plugin.alpha", "9.9.9").expect("descriptor is valid");
    let mismatched_slot = PacketSlot::new(
        "config",
        &identity,
        &other_plugin,
        "fixtures/config.json",
        br#"{"seed":7}"#.to_vec(),
    )
    .expect("slot is internally valid");
    let mismatched = Packet::new(
        identity,
        plugin,
        vec!["config".to_string()],
        vec![mismatched_slot],
    );
    assert!(matches!(
        mismatched,
        Err(PacketError::MismatchedSlot { field, .. }) if field == "plugin_descriptor"
    ));
}

#[test]
fn store_rejects_duplicate_identity_and_tampered_receipts() {
    let (packet, identity, _) = fixture();
    let mut store = InMemoryPacketStore::new();
    let receipt = store.put(packet.clone()).expect("put succeeds");

    assert!(matches!(
        store.put(packet),
        Err(PacketError::DuplicatePacket(_))
    ));

    let mut tampered = receipt.clone();
    tampered.packet_digest = Digest256::from_bytes(b"stale");
    assert!(matches!(
        store.read(&identity, &tampered),
        Err(PacketError::StaleReceipt)
    ));

    let mut missing_slot_receipt = receipt;
    missing_slot_receipt.slots.pop();
    assert!(matches!(
        store.read(&identity, &missing_slot_receipt),
        Err(PacketError::StaleReceipt)
    ));
}

#[test]
fn store_rejects_cross_run_receipts() {
    let (packet, identity, plugin) = fixture();
    let other_identity = PacketIdentity::new("packet-2", "run-2").expect("identity is valid");
    let other_slot = PacketSlot::new(
        "config",
        &other_identity,
        &plugin,
        "fixtures/config.json",
        br#"{"seed":7}"#.to_vec(),
    )
    .expect("slot is valid");
    let other_packet = Packet::new(
        other_identity,
        plugin,
        vec!["config".to_string()],
        vec![other_slot],
    )
    .expect("packet is valid");
    let other_receipt = PacketReceipt::for_packet(&other_packet).expect("receipt is valid");

    let mut store = InMemoryPacketStore::new();
    store.put(packet).expect("first put succeeds");
    assert!(matches!(
        store.read(&identity, &other_receipt),
        Err(PacketError::CrossRunReceipt { .. })
    ));
}

//! Descriptor-bound plugin composition and receipt-bound packet storage.
//!
//! State slice: `release-0-descriptor-bound-packet-v1`.
//!
//! This module is intentionally standalone until the crate integration export
//! is reviewed. It defines a deterministic, in-memory transport boundary for
//! one plugin's packet slots. It does not load plugins, read source URIs,
//! execute a run, publish files, access the network, or promote evidence.

use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use serde::{Deserialize, Serialize};
use sha2::{Digest as Sha2Digest, Sha256};

/// Packet schema identifier for the Release 0 slice.
pub const PACKET_SCHEMA_VERSION: &str = "release-0-descriptor-bound-packet-v1";

/// Descriptor identity fields covered by a plugin descriptor digest.
pub const PLUGIN_DESCRIPTOR_SCHEMA_VERSION: &str = "release-0-plugin-descriptor-v1";

/// Fallible result used by this module.
pub type Result<T> = std::result::Result<T, PacketError>;

/// Canonical lowercase SHA-256 digest.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(transparent)]
pub struct Digest256(String);

impl Digest256 {
    /// Hash arbitrary bytes with SHA-256.
    pub fn from_bytes(bytes: &[u8]) -> Self {
        let digest = Sha256::digest(bytes);
        let mut encoded = String::with_capacity(digest.len() * 2);
        for byte in digest {
            encoded.push(char::from(b"0123456789abcdef"[(byte >> 4) as usize]));
            encoded.push(char::from(b"0123456789abcdef"[(byte & 0x0f) as usize]));
        }
        Self(encoded)
    }

    /// Parse a canonical lowercase SHA-256 digest.
    pub fn parse(value: impl Into<String>) -> Result<Self> {
        let value = value.into();
        if value.len() != 64
            || !value
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        {
            return Err(PacketError::InvalidDigest {
                field: "digest".to_string(),
            });
        }
        Ok(Self(value))
    }

    /// Borrow the canonical hexadecimal representation.
    pub fn as_str(&self) -> &str {
        &self.0
    }

    fn validate(&self, field: impl Into<String>) -> Result<()> {
        let field = field.into();
        if self.0.len() != 64
            || !self
                .0
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        {
            return Err(PacketError::InvalidDigest { field });
        }
        Ok(())
    }
}

impl fmt::Display for Digest256 {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.0)
    }
}

/// Identity of one packet materialization and its run.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub struct PacketIdentity {
    /// Stable packet identity within the local composition scope.
    pub packet_id: String,
    /// Stable run identity bound to every slot and receipt.
    pub run_id: String,
}

impl PacketIdentity {
    /// Construct a non-empty packet/run identity.
    pub fn new(packet_id: impl Into<String>, run_id: impl Into<String>) -> Result<Self> {
        let identity = Self {
            packet_id: packet_id.into(),
            run_id: run_id.into(),
        };
        identity.validate()?;
        Ok(identity)
    }

    fn validate(&self) -> Result<()> {
        require_text(&self.packet_id, "packet_id")?;
        require_text(&self.run_id, "run_id")
    }
}

/// Descriptor for the in-process plugin responsible for a packet.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PluginDescriptor {
    /// Descriptor schema version.
    pub schema_version: String,
    /// Stable plugin identifier.
    pub plugin_id: String,
    /// Plugin implementation version.
    pub plugin_version: String,
    /// Digest over the schema version, plugin ID, and plugin version.
    pub descriptor_digest: Digest256,
}

impl PluginDescriptor {
    /// Construct a descriptor and derive its canonical digest.
    pub fn new(plugin_id: impl Into<String>, plugin_version: impl Into<String>) -> Result<Self> {
        let descriptor = Self {
            schema_version: PLUGIN_DESCRIPTOR_SCHEMA_VERSION.to_string(),
            plugin_id: plugin_id.into(),
            plugin_version: plugin_version.into(),
            descriptor_digest: Digest256::from_bytes(&[]),
        };
        descriptor.validate_text()?;
        let descriptor_digest = descriptor.expected_digest()?;
        Ok(Self {
            descriptor_digest,
            ..descriptor
        })
    }

    /// Validate descriptor fields and the digest binding.
    pub fn validate(&self) -> Result<()> {
        self.validate_text()?;
        self.descriptor_digest
            .validate("plugin.descriptor_digest")?;
        if self.descriptor_digest != self.expected_digest()? {
            return Err(PacketError::MismatchedPlugin {
                field: "descriptor_digest",
            });
        }
        Ok(())
    }

    fn validate_text(&self) -> Result<()> {
        if self.schema_version != PLUGIN_DESCRIPTOR_SCHEMA_VERSION {
            return Err(PacketError::MismatchedPlugin {
                field: "schema_version",
            });
        }
        require_text(&self.plugin_id, "plugin_id")?;
        require_text(&self.plugin_version, "plugin_version")
    }

    fn expected_digest(&self) -> Result<Digest256> {
        digest_json(&DescriptorDigestInput {
            schema_version: &self.schema_version,
            plugin_id: &self.plugin_id,
            plugin_version: &self.plugin_version,
        })
    }

    fn binding(&self) -> PluginBinding {
        PluginBinding {
            plugin_id: self.plugin_id.clone(),
            plugin_version: self.plugin_version.clone(),
            descriptor_digest: self.descriptor_digest.clone(),
        }
    }
}

#[derive(Serialize)]
struct DescriptorDigestInput<'a> {
    schema_version: &'a str,
    plugin_id: &'a str,
    plugin_version: &'a str,
}

/// Per-slot plugin identity copied from the packet descriptor.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PluginBinding {
    /// Stable plugin identifier.
    pub plugin_id: String,
    /// Plugin implementation version.
    pub plugin_version: String,
    /// Descriptor digest that binds the exact descriptor.
    pub descriptor_digest: Digest256,
}

impl PluginBinding {
    fn validate(&self) -> Result<()> {
        require_text(&self.plugin_id, "slot.plugin_id")?;
        require_text(&self.plugin_version, "slot.plugin_version")?;
        self.descriptor_digest.validate("slot.descriptor_digest")
    }
}

/// URI and digest identifying the local source bytes carried by a slot.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SourceRef {
    /// Opaque source URI retained as packet metadata; this module never opens it.
    pub uri: String,
    /// SHA-256 digest of the slot payload bytes.
    pub digest: Digest256,
}

impl SourceRef {
    /// Construct a source reference from local payload bytes.
    pub fn from_bytes(uri: impl Into<String>, payload: &[u8]) -> Result<Self> {
        let source = Self {
            uri: uri.into(),
            digest: Digest256::from_bytes(payload),
        };
        source.validate()?;
        Ok(source)
    }

    fn validate(&self) -> Result<()> {
        require_text(&self.uri, "source.uri")?;
        self.digest.validate("source.digest")
    }
}

/// One explicitly named packet slot.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PacketSlot {
    /// Required slot identifier.
    pub slot_id: String,
    /// Packet/run identity copied into the slot.
    pub identity: PacketIdentity,
    /// Plugin identity copied into the slot.
    pub plugin: PluginBinding,
    /// Source URI and payload digest.
    pub source: SourceRef,
    /// Local bytes represented by the source digest.
    pub payload: Vec<u8>,
}

impl PacketSlot {
    /// Construct a slot bound to one packet identity and plugin descriptor.
    pub fn new(
        slot_id: impl Into<String>,
        identity: &PacketIdentity,
        plugin: &PluginDescriptor,
        source_uri: impl Into<String>,
        payload: impl Into<Vec<u8>>,
    ) -> Result<Self> {
        plugin.validate()?;
        let payload = payload.into();
        Ok(Self {
            slot_id: slot_id.into(),
            identity: identity.clone(),
            plugin: plugin.binding(),
            source: SourceRef::from_bytes(source_uri, &payload)?,
            payload,
        })
    }

    fn validate(&self) -> Result<()> {
        require_text(&self.slot_id, "slot.slot_id")?;
        self.identity.validate()?;
        self.plugin.validate()?;
        self.source.validate()?;
        if self.source.digest != Digest256::from_bytes(&self.payload) {
            return Err(PacketError::StaleSlot {
                slot_id: self.slot_id.clone(),
            });
        }
        Ok(())
    }
}

/// A complete descriptor-bound composition packet.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Packet {
    /// Packet schema version.
    pub schema_version: String,
    /// Packet/run identity.
    pub identity: PacketIdentity,
    /// Plugin descriptor bound to every slot.
    pub plugin: PluginDescriptor,
    /// Exact slot IDs required by this composition.
    pub required_slots: Vec<String>,
    /// Materialized slots; order is not semantically meaningful.
    pub slots: Vec<PacketSlot>,
}

impl Packet {
    /// Construct and validate a complete packet.
    pub fn new(
        identity: PacketIdentity,
        plugin: PluginDescriptor,
        required_slots: Vec<String>,
        slots: Vec<PacketSlot>,
    ) -> Result<Self> {
        let packet = Self {
            schema_version: PACKET_SCHEMA_VERSION.to_string(),
            identity,
            plugin,
            required_slots,
            slots,
        };
        packet.validate()?;
        Ok(packet)
    }

    /// Validate descriptor, identity, slot completeness, and slot bindings.
    pub fn validate(&self) -> Result<()> {
        if self.schema_version != PACKET_SCHEMA_VERSION {
            return Err(PacketError::MismatchedPacket {
                field: "schema_version",
            });
        }
        self.identity.validate()?;
        self.plugin.validate()?;

        let required = unique_slot_ids(&self.required_slots)?;
        if required.is_empty() {
            return Err(PacketError::MissingSlot("<required-slot>".to_string()));
        }
        let actual = self
            .slots
            .iter()
            .map(|slot| slot.slot_id.clone())
            .collect::<Vec<_>>();
        let actual_set = unique_slot_ids(&actual)?;

        if let Some(slot_id) = required
            .iter()
            .find(|slot_id| !actual_set.contains(*slot_id))
        {
            return Err(PacketError::MissingSlot((*slot_id).clone()));
        }
        if let Some(slot_id) = actual_set
            .iter()
            .find(|slot_id| !required.contains(*slot_id))
        {
            return Err(PacketError::UnexpectedSlot((*slot_id).clone()));
        }

        let expected_binding = self.plugin.binding();
        for slot in &self.slots {
            slot.validate()?;
            if slot.identity.run_id != self.identity.run_id {
                return Err(PacketError::CrossRunSlot {
                    slot_id: slot.slot_id.clone(),
                    expected_run_id: self.identity.run_id.clone(),
                    actual_run_id: slot.identity.run_id.clone(),
                });
            }
            if slot.identity.packet_id != self.identity.packet_id {
                return Err(PacketError::MismatchedSlot {
                    slot_id: slot.slot_id.clone(),
                    field: "packet_id",
                });
            }
            if slot.plugin != expected_binding {
                return Err(PacketError::MismatchedSlot {
                    slot_id: slot.slot_id.clone(),
                    field: "plugin_descriptor",
                });
            }
        }
        Ok(())
    }

    /// Compute the canonical digest of the packet with slots sorted by ID.
    pub fn canonical_digest(&self) -> Result<Digest256> {
        self.validate()?;
        let mut required_slots = self.required_slots.clone();
        required_slots.sort();
        let mut slots = self.slots.iter().collect::<Vec<_>>();
        slots.sort_by(|left, right| left.slot_id.cmp(&right.slot_id));
        digest_json(&CanonicalPacket {
            schema_version: &self.schema_version,
            identity: &self.identity,
            plugin: &self.plugin,
            required_slots,
            slots,
        })
    }
}

#[derive(Serialize)]
struct CanonicalPacket<'a> {
    schema_version: &'a str,
    identity: &'a PacketIdentity,
    plugin: &'a PluginDescriptor,
    required_slots: Vec<String>,
    slots: Vec<&'a PacketSlot>,
}

#[derive(Serialize)]
struct CanonicalSlot<'a> {
    schema_version: &'static str,
    slot_id: &'a str,
    identity: &'a PacketIdentity,
    plugin: &'a PluginBinding,
    source: &'a SourceRef,
    payload: &'a [u8],
}

/// Digest binding for one canonical slot.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SlotReceipt {
    /// Slot identifier.
    pub slot_id: String,
    /// Digest of the canonical slot contents.
    pub slot_digest: Digest256,
    /// Digest of the identity plus this slot digest.
    pub receipt_digest: Digest256,
}

#[derive(Serialize)]
struct CanonicalSlotReceipt<'a> {
    schema_version: &'static str,
    identity: &'a PacketIdentity,
    slot_id: &'a str,
    slot_digest: &'a Digest256,
}

/// Canonical receipt required to read a packet from storage.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PacketReceipt {
    /// Packet/run identity covered by this receipt.
    pub identity: PacketIdentity,
    /// Canonical packet digest.
    pub packet_digest: Digest256,
    /// One receipt per required slot, sorted by slot ID.
    pub slots: Vec<SlotReceipt>,
    /// Digest of the canonical receipt body.
    pub receipt_digest: Digest256,
}

#[derive(Serialize)]
struct CanonicalReceipt<'a> {
    schema_version: &'static str,
    identity: &'a PacketIdentity,
    packet_digest: &'a Digest256,
    slots: &'a [SlotReceipt],
}

impl PacketReceipt {
    /// Build the canonical receipt for a validated packet.
    pub fn for_packet(packet: &Packet) -> Result<Self> {
        packet.validate()?;
        let packet_digest = packet.canonical_digest()?;
        let mut slots = packet
            .slots
            .iter()
            .map(|slot| -> Result<SlotReceipt> {
                let slot_digest = digest_json(&CanonicalSlot {
                    schema_version: PACKET_SCHEMA_VERSION,
                    slot_id: &slot.slot_id,
                    identity: &slot.identity,
                    plugin: &slot.plugin,
                    source: &slot.source,
                    payload: &slot.payload,
                })?;
                let receipt_digest = digest_json(&CanonicalSlotReceipt {
                    schema_version: PACKET_SCHEMA_VERSION,
                    identity: &packet.identity,
                    slot_id: &slot.slot_id,
                    slot_digest: &slot_digest,
                })?;
                Ok(SlotReceipt {
                    slot_id: slot.slot_id.clone(),
                    slot_digest,
                    receipt_digest,
                })
            })
            .collect::<Result<Vec<_>>>()?;
        slots.sort_by(|left, right| left.slot_id.cmp(&right.slot_id));
        let receipt_digest = digest_json(&CanonicalReceipt {
            schema_version: PACKET_SCHEMA_VERSION,
            identity: &packet.identity,
            packet_digest: &packet_digest,
            slots: &slots,
        })?;
        Ok(Self {
            identity: packet.identity.clone(),
            packet_digest,
            slots,
            receipt_digest,
        })
    }

    /// Validate this receipt against the exact canonical packet.
    pub fn validate_against(&self, packet: &Packet) -> Result<()> {
        packet.validate()?;
        if self.identity.run_id != packet.identity.run_id {
            return Err(PacketError::CrossRunReceipt {
                expected_run_id: packet.identity.run_id.clone(),
                actual_run_id: self.identity.run_id.clone(),
            });
        }
        if self.identity != packet.identity {
            return Err(PacketError::MismatchedReceipt { field: "identity" });
        }
        let expected = Self::for_packet(packet)?;
        if self != &expected {
            return Err(PacketError::StaleReceipt);
        }
        Ok(())
    }
}

/// Local deterministic packet store for one process.
#[derive(Debug, Default)]
pub struct InMemoryPacketStore {
    packets: BTreeMap<PacketIdentity, StoredPacket>,
}

#[derive(Debug, Clone)]
struct StoredPacket {
    packet: Packet,
    receipt: PacketReceipt,
}

impl InMemoryPacketStore {
    /// Construct an empty store.
    pub fn new() -> Self {
        Self::default()
    }

    /// Store one packet and return its canonical receipt.
    pub fn put(&mut self, packet: Packet) -> Result<PacketReceipt> {
        packet.validate()?;
        if self.packets.contains_key(&packet.identity) {
            return Err(PacketError::DuplicatePacket(packet.identity));
        }
        let receipt = PacketReceipt::for_packet(&packet)?;
        self.packets.insert(
            packet.identity.clone(),
            StoredPacket {
                packet,
                receipt: receipt.clone(),
            },
        );
        Ok(receipt)
    }

    /// Read a packet only with its exact packet identity and canonical receipt.
    pub fn read(&self, identity: &PacketIdentity, receipt: &PacketReceipt) -> Result<Packet> {
        if identity.run_id != receipt.identity.run_id {
            return Err(PacketError::CrossRunReceipt {
                expected_run_id: identity.run_id.clone(),
                actual_run_id: receipt.identity.run_id.clone(),
            });
        }
        if identity != &receipt.identity {
            return Err(PacketError::MismatchedReceipt { field: "identity" });
        }
        let stored = self
            .packets
            .get(identity)
            .ok_or_else(|| PacketError::MissingPacket(identity.clone()))?;
        if receipt != &stored.receipt {
            return Err(PacketError::StaleReceipt);
        }
        receipt.validate_against(&stored.packet)?;
        Ok(stored.packet.clone())
    }

    /// Return the number of stored packet identities.
    pub fn len(&self) -> usize {
        self.packets.len()
    }

    /// Return whether the store has no packet identities.
    pub fn is_empty(&self) -> bool {
        self.packets.is_empty()
    }
}

/// Errors raised by descriptor, slot, receipt, and in-memory store checks.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PacketError {
    /// A required text field was empty or whitespace-only.
    EmptyField(&'static str),
    /// A digest was not canonical lowercase SHA-256.
    InvalidDigest { field: String },
    /// A slot ID was repeated.
    DuplicateSlot(String),
    /// A required slot was absent.
    MissingSlot(String),
    /// A slot was supplied but not declared as required.
    UnexpectedSlot(String),
    /// A slot came from another run.
    CrossRunSlot {
        slot_id: String,
        expected_run_id: String,
        actual_run_id: String,
    },
    /// A slot field did not match its packet binding.
    MismatchedSlot {
        slot_id: String,
        field: &'static str,
    },
    /// Slot source bytes no longer match their declared digest.
    StaleSlot { slot_id: String },
    /// A descriptor field did not match its canonical binding.
    MismatchedPlugin { field: &'static str },
    /// A packet field did not match its schema binding.
    MismatchedPacket { field: &'static str },
    /// A receipt identity did not match the requested packet.
    MismatchedReceipt { field: &'static str },
    /// A receipt belonged to another run.
    CrossRunReceipt {
        expected_run_id: String,
        actual_run_id: String,
    },
    /// Receipt bytes or slot receipts were stale or modified.
    StaleReceipt,
    /// A packet identity was already stored.
    DuplicatePacket(PacketIdentity),
    /// No packet was stored for an identity.
    MissingPacket(PacketIdentity),
    /// Canonical JSON could not be serialized.
    Canonicalization(String),
}

impl fmt::Display for PacketError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::EmptyField(field) => write!(formatter, "{field} must not be empty"),
            Self::InvalidDigest { field } => write!(formatter, "{field} is not canonical SHA-256"),
            Self::DuplicateSlot(slot_id) => write!(formatter, "slot {slot_id} is duplicated"),
            Self::MissingSlot(slot_id) => write!(formatter, "slot {slot_id} is missing"),
            Self::UnexpectedSlot(slot_id) => write!(formatter, "slot {slot_id} is not required"),
            Self::CrossRunSlot {
                slot_id,
                expected_run_id,
                actual_run_id,
            } => write!(
                formatter,
                "slot {slot_id} belongs to run {actual_run_id}, expected {expected_run_id}"
            ),
            Self::MismatchedSlot { slot_id, field } => {
                write!(formatter, "slot {slot_id} mismatches {field}")
            }
            Self::StaleSlot { slot_id } => {
                write!(formatter, "slot {slot_id} has stale source bytes")
            }
            Self::MismatchedPlugin { field } => write!(formatter, "plugin mismatches {field}"),
            Self::MismatchedPacket { field } => write!(formatter, "packet mismatches {field}"),
            Self::MismatchedReceipt { field } => write!(formatter, "receipt mismatches {field}"),
            Self::CrossRunReceipt {
                expected_run_id,
                actual_run_id,
            } => write!(
                formatter,
                "receipt belongs to run {actual_run_id}, expected {expected_run_id}"
            ),
            Self::StaleReceipt => formatter.write_str("receipt is stale or not canonical"),
            Self::DuplicatePacket(identity) => write!(
                formatter,
                "packet {} for run {} is already stored",
                identity.packet_id, identity.run_id
            ),
            Self::MissingPacket(identity) => write!(
                formatter,
                "packet {} for run {} is not stored",
                identity.packet_id, identity.run_id
            ),
            Self::Canonicalization(message) => {
                write!(formatter, "canonicalization failed: {message}")
            }
        }
    }
}

impl std::error::Error for PacketError {}

fn require_text(value: &str, field: &'static str) -> Result<()> {
    if value.trim().is_empty() {
        return Err(PacketError::EmptyField(field));
    }
    Ok(())
}

fn unique_slot_ids(slot_ids: &[String]) -> Result<BTreeSet<String>> {
    let mut unique = BTreeSet::new();
    for slot_id in slot_ids {
        require_text(slot_id, "slot_id")?;
        if !unique.insert(slot_id.clone()) {
            return Err(PacketError::DuplicateSlot(slot_id.clone()));
        }
    }
    Ok(unique)
}

fn digest_json<T: Serialize>(value: &T) -> Result<Digest256> {
    let bytes = serde_json::to_vec(value)
        .map_err(|error| PacketError::Canonicalization(error.to_string()))?;
    Ok(Digest256::from_bytes(&bytes))
}

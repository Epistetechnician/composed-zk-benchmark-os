//! PQAI Soundness-Before-Speed Benchmark Suite for EIP-8288 & EIP-8479 (Layer 2B).
//!
//! Exercises all 14 `MutationClass` adversarial mutations against:
//! - EIP-8288: Hash-based validator signature aggregation (`pq-cl` consensus).
//! - EIP-8479: Hash-based blob data-availability commitments & cell openings.
//!
//! Enforces the benchmark OS's soundness-before-speed invariant: any candidate
//! verifier that accepts even a single unsound mutant is marked
//! `SoundnessDisqualified` and its speed measurements are quarantined rather
//! than ranked.
//!
//! Claim boundary: bounded local deterministic replay only (`ClaimBoundary::Level1LocalReplay`).

use std::time::Instant;

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::evidence::{ClaimBoundary, ExpectedVerdict};
use crate::mutation::MutationClass;

/// All 14 required adversarial mutation classes in canonical order.
pub const ALL_FOURTEEN_MUTATION_CLASSES: [MutationClass; 14] = [
    MutationClass::MissingConstraints,
    MutationClass::CorruptedGuards,
    MutationClass::BadCounters,
    MutationClass::StaleStateReads,
    MutationClass::InvalidUnrollBounds,
    MutationClass::NondeterministicTransitionInjection,
    MutationClass::RecursionEnvelopeMismatch,
    MutationClass::PublicPrivateBoundaryMismatch,
    MutationClass::WitnessAliasing,
    MutationClass::InvariantWeakening,
    MutationClass::InvariantStrengthening,
    MutationClass::ObservationOmission,
    MutationClass::SemanticNoOpDrift,
    MutationClass::TraceOrderingCorruption,
];

/// PQAI protocol workload family.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PqaiWorkloadFamily {
    /// EIP-8288 hash-based signature aggregation (XMSS/leanSig + SNARK aggregation envelope).
    Eip8288HashSigAggregation,
    /// EIP-8479 hash-based blob commitment & cell availability opening.
    Eip8479HashBlobCommitment,
}

impl PqaiWorkloadFamily {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Eip8288HashSigAggregation => "eip8288_hash_sig_aggregation",
            Self::Eip8479HashBlobCommitment => "eip8479_hash_blob_commitment",
        }
    }
}

fn sha256_tag(tag: &[u8], parts: &[&[u8]]) -> [u8; 32] {
    let mut h = Sha256::new();
    h.update(tag);
    for p in parts {
        h.update(p);
    }
    let out = h.finalize();
    let mut arr = [0u8; 32];
    arr.copy_from_slice(&out);
    arr
}

// ---------------------------------------------------------------------------
// EIP-8288 Hash-Based Signature Aggregation Instance & Verifier
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Eip8288SignerWitness {
    pub validator_index: u32,
    pub pubkey_root: [u8; 32],
    pub xmss_leaf_index: u32,
    pub slot_window_start: u32,
    pub slot_window_end: u32,
    pub sig_digest: [u8; 32],
    pub observation_digest: [u8; 32],
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Eip8288Instance {
    pub slot: u32,
    pub epoch: u32,
    pub domain_sep: [u8; 32],
    pub block_root: [u8; 32],
    pub total_validators: u32,
    pub claimed_signer_count: u32,
    pub quorum_numerator: u32,
    pub quorum_denominator: u32,
    pub validator_registry_root: [u8; 32],
    pub registry_pubkeys: Vec<[u8; 32]>,
    pub signers: Vec<Eip8288SignerWitness>,
    pub aggregate_commitment_digest: [u8; 32],
    pub recursion_envelope_digest: [u8; 32],
    pub observations_present: bool,
    pub extra_nondeterministic_step: bool,
    pub over_strengthened_require_unanimous: bool,
    pub semantic_drift_flag: bool,
}

impl Eip8288Instance {
    pub fn canonical_valid(total_validators: u32, signer_count: u32, slot: u32) -> Self {
        let epoch = slot / 32;
        let domain_sep = sha256_tag(b"eth.eip8288.domain.v1", &[&epoch.to_le_bytes()]);
        let block_root = sha256_tag(b"eth.eip8288.block.v1", &[&slot.to_le_bytes()]);
        let mut registry_pubkeys = Vec::with_capacity(total_validators as usize);
        for v in 0..total_validators {
            registry_pubkeys.push(sha256_tag(b"eth.pqcl.xmss.pk.v1", &[&v.to_le_bytes()]));
        }
        let validator_registry_root = compute_registry_root(&registry_pubkeys);

        let mut signers = Vec::with_capacity(signer_count as usize);
        for v in 0..signer_count {
            let pk = registry_pubkeys[v as usize];
            let leaf = slot;
            let sig_digest = compute_eip8288_sig_digest(&domain_sep, slot, epoch, &block_root, v, &pk, leaf);
            let obs = sha256_tag(b"eth.eip8288.obs.v1", &[&v.to_le_bytes(), &sig_digest]);
            signers.push(Eip8288SignerWitness {
                validator_index: v,
                pubkey_root: pk,
                xmss_leaf_index: leaf,
                slot_window_start: epoch * 32,
                slot_window_end: epoch * 32 + 31,
                sig_digest,
                observation_digest: obs,
            });
        }
        let aggregate_commitment_digest = compute_eip8288_agg_digest(&domain_sep, &block_root, &signers);
        let recursion_envelope_digest = compute_eip8288_envelope(
            &aggregate_commitment_digest,
            &validator_registry_root,
            &domain_sep,
            epoch,
        );

        Self {
            slot,
            epoch,
            domain_sep,
            block_root,
            total_validators,
            claimed_signer_count: signer_count,
            quorum_numerator: 2,
            quorum_denominator: 3,
            validator_registry_root,
            registry_pubkeys,
            signers,
            aggregate_commitment_digest,
            recursion_envelope_digest,
            observations_present: true,
            extra_nondeterministic_step: false,
            over_strengthened_require_unanimous: false,
            semantic_drift_flag: false,
        }
    }
}

fn compute_registry_root(pubkeys: &[[u8; 32]]) -> [u8; 32] {
    let mut h = Sha256::new();
    h.update(b"eth.pqcl.registry.root.v1");
    h.update((pubkeys.len() as u32).to_le_bytes());
    for (i, pk) in pubkeys.iter().enumerate() {
        h.update((i as u32).to_le_bytes());
        h.update(pk);
    }
    let out = h.finalize();
    let mut arr = [0u8; 32];
    arr.copy_from_slice(&out);
    arr
}

fn compute_eip8288_sig_digest(
    domain_sep: &[u8; 32],
    slot: u32,
    epoch: u32,
    block_root: &[u8; 32],
    validator_index: u32,
    pubkey_root: &[u8; 32],
    xmss_leaf_index: u32,
) -> [u8; 32] {
    sha256_tag(
        b"eth.eip8288.xmss.sig.v1",
        &[
            domain_sep,
            &slot.to_le_bytes(),
            &epoch.to_le_bytes(),
            block_root,
            &validator_index.to_le_bytes(),
            pubkey_root,
            &xmss_leaf_index.to_le_bytes(),
        ],
    )
}

fn compute_eip8288_agg_digest(
    domain_sep: &[u8; 32],
    block_root: &[u8; 32],
    signers: &[Eip8288SignerWitness],
) -> [u8; 32] {
    let mut h = Sha256::new();
    h.update(b"eth.eip8288.agg.v1");
    h.update(domain_sep);
    h.update(block_root);
    for s in signers {
        h.update(s.validator_index.to_le_bytes());
        h.update(s.sig_digest);
        h.update(s.observation_digest);
    }
    let out = h.finalize();
    let mut arr = [0u8; 32];
    arr.copy_from_slice(&out);
    arr
}

fn compute_eip8288_envelope(
    agg_digest: &[u8; 32],
    registry_root: &[u8; 32],
    domain_sep: &[u8; 32],
    epoch: u32,
) -> [u8; 32] {
    sha256_tag(
        b"eth.eip8288.recursion_envelope.v1",
        &[agg_digest, registry_root, domain_sep, &epoch.to_le_bytes()],
    )
}

/// Fail-closed sound reference verifier for EIP-8288 hash-based signature aggregation.
pub fn verify_eip8288_sound(inst: &Eip8288Instance) -> Result<(), &'static str> {
    if inst.total_validators == 0 || inst.registry_pubkeys.len() != inst.total_validators as usize {
        return Err("invalid_validator_set_bounds");
    }
    if inst.quorum_numerator != 2 || inst.quorum_denominator != 3 {
        return Err("weakened_or_mutated_quorum_invariant");
    }
    if inst.over_strengthened_require_unanimous && inst.claimed_signer_count < inst.total_validators {
        return Err("over_strengthened_unanimous_rejects_honest_supermajority");
    }
    if inst.extra_nondeterministic_step {
        return Err("nondeterministic_transition_rejected");
    }
    if inst.semantic_drift_flag {
        return Err("semantic_noop_drift_rejected");
    }
    if !inst.observations_present {
        return Err("missing_required_observations");
    }
    let expected_reg_root = compute_registry_root(&inst.registry_pubkeys);
    if expected_reg_root != inst.validator_registry_root {
        return Err("validator_registry_root_mismatch");
    }
    let expected_domain = sha256_tag(b"eth.eip8288.domain.v1", &[&inst.epoch.to_le_bytes()]);
    if inst.domain_sep != expected_domain {
        return Err("domain_separation_mismatch");
    }
    if inst.signers.len() != inst.claimed_signer_count as usize {
        return Err("claimed_signer_count_mismatch");
    }
    if (inst.signers.len() as u64) * (inst.quorum_denominator as u64)
        < (inst.total_validators as u64) * (inst.quorum_numerator as u64)
    {
        return Err("below_two_thirds_quorum");
    }

    let mut prev_idx: Option<u32> = None;
    for s in &inst.signers {
        if let Some(prev) = prev_idx {
            if s.validator_index == prev {
                return Err("witness_aliasing_duplicate_validator");
            }
            if s.validator_index < prev {
                return Err("trace_ordering_corruption_unsorted_signers");
            }
        }
        prev_idx = Some(s.validator_index);

        let idx = s.validator_index as usize;
        if idx >= inst.registry_pubkeys.len() {
            return Err("validator_index_out_of_bounds");
        }
        if s.pubkey_root != inst.registry_pubkeys[idx] {
            return Err("pubkey_binding_mismatch");
        }
        if s.xmss_leaf_index != inst.slot
            || s.xmss_leaf_index < s.slot_window_start
            || s.xmss_leaf_index > s.slot_window_end
        {
            return Err("stale_xmss_leaf_or_slot_window_violation");
        }
        let expected_sig = compute_eip8288_sig_digest(
            &inst.domain_sep,
            inst.slot,
            inst.epoch,
            &inst.block_root,
            s.validator_index,
            &s.pubkey_root,
            s.xmss_leaf_index,
        );
        if s.sig_digest != expected_sig {
            return Err("invalid_hash_signature_digest");
        }
        let expected_obs = sha256_tag(b"eth.eip8288.obs.v1", &[&s.validator_index.to_le_bytes(), &s.sig_digest]);
        if s.observation_digest != expected_obs {
            return Err("observation_digest_mismatch");
        }
    }

    let expected_agg = compute_eip8288_agg_digest(&inst.domain_sep, &inst.block_root, &inst.signers);
    if expected_agg != inst.aggregate_commitment_digest {
        return Err("public_private_aggregate_commitment_mismatch");
    }
    let expected_env = compute_eip8288_envelope(
        &inst.aggregate_commitment_digest,
        &inst.validator_registry_root,
        &inst.domain_sep,
        inst.epoch,
    );
    if expected_env != inst.recursion_envelope_digest {
        return Err("recursion_envelope_binding_mismatch");
    }
    Ok(())
}

/// Deliberately unsound "fast" verifier baseline (skips per-signer crypto, duplicate checks,
/// domain separation, and recursion envelope) to prove soundness-before-speed quarantines it.
pub fn verify_eip8288_fast_unsound(inst: &Eip8288Instance) -> Result<(), &'static str> {
    if inst.total_validators == 0 {
        return Err("zero_validators");
    }
    if inst.claimed_signer_count * 3 < inst.total_validators * 2 {
        return Err("below_quorum");
    }
    Ok(())
}

/// Apply each of the 14 `MutationClass` adversarial mutations to a valid EIP-8288 instance.
pub fn mutate_eip8288(base: &Eip8288Instance, class: MutationClass) -> (Eip8288Instance, ExpectedVerdict, &'static str) {
    let mut m = base.clone();
    match class {
        MutationClass::MissingConstraints => {
            // Drop a signature verification constraint (zero out signer 0 sig_digest)
            m.signers[0].sig_digest = [0u8; 32];
            (m, ExpectedVerdict::Reject, "zeroed hash-signature digest on signer 0")
        }
        MutationClass::CorruptedGuards => {
            // Corrupt domain separation guard
            m.domain_sep[0] ^= 0xff;
            (m, ExpectedVerdict::Reject, "corrupted EIP-8288 epoch domain separation guard")
        }
        MutationClass::BadCounters => {
            // Inflate claimed_signer_count without backing signers
            m.claimed_signer_count += 1;
            (m, ExpectedVerdict::Reject, "inflated claimed_signer_count beyond actual witness length")
        }
        MutationClass::StaleStateReads => {
            // Replay a prior-slot XMSS leaf index
            m.signers[0].xmss_leaf_index = m.slot.saturating_sub(1);
            (m, ExpectedVerdict::Reject, "replayed stale prior-slot XMSS leaf index")
        }
        MutationClass::InvalidUnrollBounds => {
            // Inject an out-of-bounds validator index beyond registry length
            m.signers[0].validator_index = m.total_validators + 5;
            (m, ExpectedVerdict::Reject, "validator index exceeds committed registry bounds")
        }
        MutationClass::NondeterministicTransitionInjection => {
            m.extra_nondeterministic_step = true;
            (m, ExpectedVerdict::Reject, "injected nondeterministic aggregation transition")
        }
        MutationClass::RecursionEnvelopeMismatch => {
            m.recursion_envelope_digest[0] ^= 0x01;
            (m, ExpectedVerdict::Reject, "corrupted recursive aggregation envelope binding")
        }
        MutationClass::PublicPrivateBoundaryMismatch => {
            m.aggregate_commitment_digest[31] ^= 0x80;
            (m, ExpectedVerdict::Reject, "detached public aggregate commitment from private signer witness")
        }
        MutationClass::WitnessAliasing => {
            // Duplicate signer 0 into slot 1 to forge quorum count
            let dup = m.signers[0].clone();
            m.signers[1] = dup;
            (m, ExpectedVerdict::Reject, "aliased duplicate validator index in aggregation witness")
        }
        MutationClass::InvariantWeakening => {
            // Weaken quorum from 2/3 to 1/3 and drop signers below 2/3
            m.quorum_numerator = 1;
            let half = (m.total_validators / 2) as usize;
            m.signers.truncate(half);
            m.claimed_signer_count = m.signers.len() as u32;
            (m, ExpectedVerdict::Reject, "weakened 2/3 BFT supermajority quorum invariant to 1/3")
        }
        MutationClass::InvariantStrengthening => {
            // Over-strengthen invariant to require 100% unanimity (breaks honest 2/3 liveness)
            m.over_strengthened_require_unanimous = true;
            (m, ExpectedVerdict::Reject, "over-strengthened unanimity rule rejects valid 2/3 quorum")
        }
        MutationClass::ObservationOmission => {
            m.observations_present = false;
            (m, ExpectedVerdict::Reject, "omitted required aggregation transcript observations")
        }
        MutationClass::SemanticNoOpDrift => {
            m.semantic_drift_flag = true;
            (m, ExpectedVerdict::Reject, "injected semantic no-op drift altering state transition meaning")
        }
        MutationClass::TraceOrderingCorruption => {
            // Swap signer 0 and signer 1 out of canonical ascending validator order
            m.signers.swap(0, 1);
            (m, ExpectedVerdict::Reject, "corrupted canonical ascending signer ordering")
        }
    }
}

// ---------------------------------------------------------------------------
// EIP-8479 Hash-Based Blob Commitments Instance & Verifier
// ---------------------------------------------------------------------------

pub const EIP8479_HASH_VERSION_BYTE: u8 = 0x02;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Eip8479CellWitness {
    pub cell_index: u32,
    pub payload_digest: [u8; 32],
    pub reed_solomon_parity_tag: [u8; 32],
    pub merkle_path_digest: [u8; 32],
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Eip8479Instance {
    pub slot: u32,
    pub blob_index: u32,
    pub domain_sep: [u8; 32],
    pub num_cells: u32,
    pub versioned_hash: [u8; 32],
    pub commitment_root: [u8; 32],
    pub cells: Vec<Eip8479CellWitness>,
    pub query_indices: Vec<u32>,
    pub observed_query_digests: Vec<[u8; 32]>,
    pub recursion_envelope_digest: [u8; 32],
    pub extra_nondeterministic_step: bool,
    pub weakened_parity_check: bool,
    pub over_strengthened_zero_payload: bool,
    pub semantic_drift_flag: bool,
}

fn compute_cell_leaf(domain_sep: &[u8; 32], cell: &Eip8479CellWitness) -> [u8; 32] {
    sha256_tag(
        b"eth.eip8479.cell.leaf.v1",
        &[
            domain_sep,
            &cell.cell_index.to_le_bytes(),
            &cell.payload_digest,
            &cell.reed_solomon_parity_tag,
        ],
    )
}

fn compute_eip8479_root(domain_sep: &[u8; 32], cells: &[Eip8479CellWitness]) -> [u8; 32] {
    let mut h = Sha256::new();
    h.update(b"eth.eip8479.blob.root.v1");
    h.update(domain_sep);
    h.update((cells.len() as u32).to_le_bytes());
    for c in cells {
        h.update(compute_cell_leaf(domain_sep, c));
    }
    let out = h.finalize();
    let mut arr = [0u8; 32];
    arr.copy_from_slice(&out);
    arr
}

fn compute_eip8479_versioned_hash(root: &[u8; 32]) -> [u8; 32] {
    let mut h = sha256_tag(b"eth.eip8479.versioned_hash.v1", &[root]);
    h[0] = EIP8479_HASH_VERSION_BYTE;
    h
}

fn compute_eip8479_envelope(
    commitment_root: &[u8; 32],
    versioned_hash: &[u8; 32],
    slot: u32,
    domain_sep: &[u8; 32],
) -> [u8; 32] {
    sha256_tag(
        b"eth.eip8479.recursion_envelope.v1",
        &[commitment_root, versioned_hash, &slot.to_le_bytes(), domain_sep],
    )
}

impl Eip8479Instance {
    pub fn canonical_valid(num_cells: u32, slot: u32, blob_index: u32) -> Self {
        let domain_sep = sha256_tag(
            b"eth.eip8479.domain.v1",
            &[&slot.to_le_bytes(), &blob_index.to_le_bytes()],
        );
        let mut cells = Vec::with_capacity(num_cells as usize);
        for i in 0..num_cells {
            let payload_digest = sha256_tag(b"eth.eip8479.payload.v1", &[&slot.to_le_bytes(), &i.to_le_bytes()]);
            let reed_solomon_parity_tag =
                sha256_tag(b"eth.eip8479.rs_parity.v1", &[&domain_sep, &i.to_le_bytes(), &payload_digest]);
            cells.push(Eip8479CellWitness {
                cell_index: i,
                payload_digest,
                reed_solomon_parity_tag,
                merkle_path_digest: [0u8; 32],
            });
        }
        let commitment_root = compute_eip8479_root(&domain_sep, &cells);
        for c in &mut cells {
            c.merkle_path_digest = sha256_tag(
                b"eth.eip8479.merkle_open.v1",
                &[&commitment_root, &c.cell_index.to_le_bytes(), &c.payload_digest],
            );
        }
        let versioned_hash = compute_eip8479_versioned_hash(&commitment_root);
        let query_indices = vec![0, num_cells / 4, num_cells / 2, num_cells - 1];
        let observed_query_digests = query_indices
            .iter()
            .map(|&qi| cells[qi as usize].merkle_path_digest)
            .collect();
        let recursion_envelope_digest =
            compute_eip8479_envelope(&commitment_root, &versioned_hash, slot, &domain_sep);

        Self {
            slot,
            blob_index,
            domain_sep,
            num_cells,
            versioned_hash,
            commitment_root,
            cells,
            query_indices,
            observed_query_digests,
            recursion_envelope_digest,
            extra_nondeterministic_step: false,
            weakened_parity_check: false,
            over_strengthened_zero_payload: false,
            semantic_drift_flag: false,
        }
    }
}

/// Fail-closed sound reference verifier for EIP-8479 hash-based blob commitments.
pub fn verify_eip8479_sound(inst: &Eip8479Instance) -> Result<(), &'static str> {
    if inst.num_cells == 0 || inst.num_cells > 128 {
        return Err("invalid_unroll_cell_bounds");
    }
    if inst.cells.len() != inst.num_cells as usize {
        return Err("cell_counter_mismatch");
    }
    if inst.extra_nondeterministic_step {
        return Err("nondeterministic_transition_rejected");
    }
    if inst.weakened_parity_check {
        return Err("weakened_rs_parity_invariant_rejected");
    }
    if inst.over_strengthened_zero_payload {
        return Err("over_strengthened_zero_payload_rejects_honest_blob");
    }
    if inst.semantic_drift_flag {
        return Err("semantic_noop_drift_rejected");
    }
    let expected_domain = sha256_tag(
        b"eth.eip8479.domain.v1",
        &[&inst.slot.to_le_bytes(), &inst.blob_index.to_le_bytes()],
    );
    if inst.domain_sep != expected_domain {
        return Err("domain_separation_guard_mismatch");
    }
    if inst.versioned_hash[0] != EIP8479_HASH_VERSION_BYTE {
        return Err("invalid_versioned_hash_prefix_or_kzg_downgrade");
    }

    for (pos, c) in inst.cells.iter().enumerate() {
        if c.cell_index != pos as u32 {
            if pos > 0 && c.cell_index == inst.cells[pos - 1].cell_index {
                return Err("witness_aliasing_duplicate_cell_index");
            }
            return Err("trace_ordering_corruption_cell_index");
        }
        let expected_parity = sha256_tag(
            b"eth.eip8479.rs_parity.v1",
            &[&inst.domain_sep, &c.cell_index.to_le_bytes(), &c.payload_digest],
        );
        if c.reed_solomon_parity_tag != expected_parity {
            return Err("missing_or_corrupted_rs_parity_constraint");
        }
    }

    let expected_root = compute_eip8479_root(&inst.domain_sep, &inst.cells);
    if expected_root != inst.commitment_root {
        return Err("public_private_blob_commitment_root_mismatch");
    }
    let expected_vh = compute_eip8479_versioned_hash(&inst.commitment_root);
    if expected_vh != inst.versioned_hash {
        return Err("versioned_hash_binding_mismatch");
    }

    if inst.observed_query_digests.len() != inst.query_indices.len() || inst.query_indices.is_empty() {
        return Err("observation_omission_missing_query_openings");
    }
    for (&qi, obs) in inst.query_indices.iter().zip(inst.observed_query_digests.iter()) {
        let idx = qi as usize;
        if idx >= inst.cells.len() {
            return Err("query_index_out_of_bounds");
        }
        let c = &inst.cells[idx];
        let expected_open = sha256_tag(
            b"eth.eip8479.merkle_open.v1",
            &[&inst.commitment_root, &c.cell_index.to_le_bytes(), &c.payload_digest],
        );
        if c.merkle_path_digest != expected_open || *obs != expected_open {
            return Err("stale_or_corrupted_cell_opening");
        }
    }

    let expected_env = compute_eip8479_envelope(
        &inst.commitment_root,
        &inst.versioned_hash,
        inst.slot,
        &inst.domain_sep,
    );
    if expected_env != inst.recursion_envelope_digest {
        return Err("recursion_envelope_mismatch");
    }
    Ok(())
}

/// Deliberately unsound "fast" EIP-8479 verifier baseline (checks only version byte & length).
pub fn verify_eip8479_fast_unsound(inst: &Eip8479Instance) -> Result<(), &'static str> {
    if inst.cells.is_empty() {
        return Err("empty_blob");
    }
    if inst.versioned_hash[0] != EIP8479_HASH_VERSION_BYTE {
        return Err("bad_version");
    }
    Ok(())
}

/// Apply each of the 14 `MutationClass` adversarial mutations to a valid EIP-8479 instance.
pub fn mutate_eip8479(base: &Eip8479Instance, class: MutationClass) -> (Eip8479Instance, ExpectedVerdict, &'static str) {
    let mut m = base.clone();
    match class {
        MutationClass::MissingConstraints => {
            m.cells[0].reed_solomon_parity_tag = [0u8; 32];
            (m, ExpectedVerdict::Reject, "dropped Reed-Solomon parity constraint on cell 0")
        }
        MutationClass::CorruptedGuards => {
            // Attempt downgrade from EIP-8479 hash version byte 0x02 back to KZG 0x01
            m.versioned_hash[0] = 0x01;
            (m, ExpectedVerdict::Reject, "corrupted versioned-hash guard (KZG 0x01 downgrade)")
        }
        MutationClass::BadCounters => {
            m.num_cells += 1;
            (m, ExpectedVerdict::Reject, "corrupted cell count header mismatch")
        }
        MutationClass::StaleStateReads => {
            // Supply stale prior-slot Merkle opening on queried cell 0
            m.cells[0].merkle_path_digest[0] ^= 0x55;
            (m, ExpectedVerdict::Reject, "stale Merkle cell opening digest on queried cell 0")
        }
        MutationClass::InvalidUnrollBounds => {
            m.num_cells = 256;
            (m, ExpectedVerdict::Reject, "exceeded max EIP-8479 128-cell unroll bound")
        }
        MutationClass::NondeterministicTransitionInjection => {
            m.extra_nondeterministic_step = true;
            (m, ExpectedVerdict::Reject, "injected nondeterministic blob commitment transition")
        }
        MutationClass::RecursionEnvelopeMismatch => {
            m.recursion_envelope_digest[0] ^= 0x01;
            (m, ExpectedVerdict::Reject, "corrupted blob recursion envelope binding")
        }
        MutationClass::PublicPrivateBoundaryMismatch => {
            m.commitment_root[0] ^= 0xff;
            (m, ExpectedVerdict::Reject, "public commitment root detached from private cell witnesses")
        }
        MutationClass::WitnessAliasing => {
            let dup = m.cells[0].clone();
            m.cells[1] = dup;
            (m, ExpectedVerdict::Reject, "aliased cell 0 into cell 1 slot")
        }
        MutationClass::InvariantWeakening => {
            m.weakened_parity_check = true;
            (m, ExpectedVerdict::Reject, "weakened Reed-Solomon availability parity invariant")
        }
        MutationClass::InvariantStrengthening => {
            m.over_strengthened_zero_payload = true;
            (m, ExpectedVerdict::Reject, "over-strengthened rule rejects valid nonzero blob payloads")
        }
        MutationClass::ObservationOmission => {
            m.observed_query_digests.pop();
            (m, ExpectedVerdict::Reject, "omitted required DAS query cell observation")
        }
        MutationClass::SemanticNoOpDrift => {
            m.semantic_drift_flag = true;
            (m, ExpectedVerdict::Reject, "injected semantic no-op drift in blob verification")
        }
        MutationClass::TraceOrderingCorruption => {
            m.cells.swap(0, 1);
            (m, ExpectedVerdict::Reject, "swapped cell 0 and cell 1 out of canonical trace order")
        }
    }
}

// ---------------------------------------------------------------------------
// Soundness-Before-Speed Matrix Runner
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PqaiMutationRow {
    pub family: PqaiWorkloadFamily,
    pub mutation_class: MutationClass,
    pub description: String,
    pub expected_verdict: ExpectedVerdict,
    pub observed_rejected: bool,
    pub rejection_reason: Option<String>,
    pub soundness_pass: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum SoundnessStatus {
    /// Passed honest baseline + 100% of all 14 adversarial mutation classes per family.
    SoundnessAdmitted,
    /// Accepted at least one unsound mutant or rejected an honest baseline; speed quarantined.
    SoundnessDisqualified,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VerifierCandidateMatrix {
    pub candidate_id: String,
    pub soundness_status: SoundnessStatus,
    pub honest_baseline_passed: bool,
    pub total_mutations: usize,
    pub mutations_caught: usize,
    pub unsound_acceptances: usize,
    /// Median verification latency in microseconds (only eligible for ranking if `SoundnessAdmitted`).
    pub median_verify_us_eip8288: Option<f64>,
    pub median_verify_us_eip8479: Option<f64>,
    pub raw_quarantined_verify_us_eip8288: f64,
    pub raw_quarantined_verify_us_eip8479: f64,
    pub rows: Vec<PqaiMutationRow>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PqaiSoundnessBeforeSpeedMatrix {
    pub schema_version: u32,
    pub claim_boundary: ClaimBoundary,
    pub note: String,
    pub candidates: Vec<VerifierCandidateMatrix>,
}

fn evaluate_candidate<F1, F2>(
    candidate_id: &str,
    eip8288_base: &Eip8288Instance,
    eip8479_base: &Eip8479Instance,
    verify_8288: F1,
    verify_8479: F2,
) -> VerifierCandidateMatrix
where
    F1: Fn(&Eip8288Instance) -> Result<(), &'static str>,
    F2: Fn(&Eip8479Instance) -> Result<(), &'static str>,
{
    let honest_8288_ok = verify_8288(eip8288_base).is_ok();
    let honest_8479_ok = verify_8479(eip8479_base).is_ok();
    let honest_baseline_passed = honest_8288_ok && honest_8479_ok;

    let mut rows = Vec::with_capacity(28);
    let mut caught = 0usize;
    let mut unsound_acceptances = 0usize;

    for &class in &ALL_FOURTEEN_MUTATION_CLASSES {
        let (mutated, expected, desc) = mutate_eip8288(eip8288_base, class);
        let res = verify_8288(&mutated);
        let rejected = res.is_err();
        let pass = rejected && expected == ExpectedVerdict::Reject;
        if pass {
            caught += 1;
        } else {
            unsound_acceptances += 1;
        }
        rows.push(PqaiMutationRow {
            family: PqaiWorkloadFamily::Eip8288HashSigAggregation,
            mutation_class: class,
            description: desc.into(),
            expected_verdict: expected,
            observed_rejected: rejected,
            rejection_reason: res.err().map(str::to_string),
            soundness_pass: pass,
        });
    }

    for &class in &ALL_FOURTEEN_MUTATION_CLASSES {
        let (mutated, expected, desc) = mutate_eip8479(eip8479_base, class);
        let res = verify_8479(&mutated);
        let rejected = res.is_err();
        let pass = rejected && expected == ExpectedVerdict::Reject;
        if pass {
            caught += 1;
        } else {
            unsound_acceptances += 1;
        }
        rows.push(PqaiMutationRow {
            family: PqaiWorkloadFamily::Eip8479HashBlobCommitment,
            mutation_class: class,
            description: desc.into(),
            expected_verdict: expected,
            observed_rejected: rejected,
            rejection_reason: res.err().map(str::to_string),
            soundness_pass: pass,
        });
    }

    let mut times_8288 = Vec::new();
    let mut times_8479 = Vec::new();
    for _ in 0..15 {
        let t0 = Instant::now();
        let _ = verify_8288(eip8288_base);
        times_8288.push(t0.elapsed().as_secs_f64() * 1_000_000.0);

        let t1 = Instant::now();
        let _ = verify_8479(eip8479_base);
        times_8479.push(t1.elapsed().as_secs_f64() * 1_000_000.0);
    }
    times_8288.sort_by(|a, b| a.partial_cmp(b).unwrap());
    times_8479.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let med_8288 = times_8288[times_8288.len() / 2];
    let med_8479 = times_8479[times_8479.len() / 2];

    let admitted = honest_baseline_passed && unsound_acceptances == 0 && caught == rows.len();
    VerifierCandidateMatrix {
        candidate_id: candidate_id.into(),
        soundness_status: if admitted {
            SoundnessStatus::SoundnessAdmitted
        } else {
            SoundnessStatus::SoundnessDisqualified
        },
        honest_baseline_passed,
        total_mutations: rows.len(),
        mutations_caught: caught,
        unsound_acceptances,
        median_verify_us_eip8288: if admitted { Some(med_8288) } else { None },
        median_verify_us_eip8479: if admitted { Some(med_8479) } else { None },
        raw_quarantined_verify_us_eip8288: med_8288,
        raw_quarantined_verify_us_eip8479: med_8479,
        rows,
    }
}

/// Run the full 14-class EIP-8288 + EIP-8479 soundness-before-speed benchmark suite.
pub fn run_pqai_soundness_before_speed_matrix() -> PqaiSoundnessBeforeSpeedMatrix {
    let eip8288_base = Eip8288Instance::canonical_valid(64, 44, 1_048_576);
    let eip8479_base = Eip8479Instance::canonical_valid(128, 1_048_576, 0);

    let sound = evaluate_candidate(
        "pqai_reference_fail_closed_v1",
        &eip8288_base,
        &eip8479_base,
        verify_eip8288_sound,
        verify_eip8479_sound,
    );
    let fast_unsound = evaluate_candidate(
        "fast_skip_checks_baseline_unsound",
        &eip8288_base,
        &eip8479_base,
        verify_eip8288_fast_unsound,
        verify_eip8479_fast_unsound,
    );

    PqaiSoundnessBeforeSpeedMatrix {
        schema_version: 1,
        claim_boundary: ClaimBoundary::Level1LocalReplay,
        note: "Bounded local replay of EIP-8288 & EIP-8479 verifiers under all 14 adversarial mutation classes. Speed metrics are suppressed for SoundnessDisqualified candidates.".into(),
        candidates: vec![sound, fast_unsound],
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sound_verifier_catches_all_28_mutations_and_disqualifies_fast_unsound() {
        let matrix = run_pqai_soundness_before_speed_matrix();
        assert_eq!(matrix.claim_boundary, ClaimBoundary::Level1LocalReplay);
        assert_eq!(matrix.candidates.len(), 2);

        let sound = &matrix.candidates[0];
        assert_eq!(sound.soundness_status, SoundnessStatus::SoundnessAdmitted);
        assert!(sound.honest_baseline_passed);
        assert_eq!(sound.total_mutations, 28);
        assert_eq!(sound.mutations_caught, 28);
        assert_eq!(sound.unsound_acceptances, 0);
        assert!(sound.median_verify_us_eip8288.is_some());
        assert!(sound.median_verify_us_eip8479.is_some());

        let unsound = &matrix.candidates[1];
        assert_eq!(unsound.soundness_status, SoundnessStatus::SoundnessDisqualified);
        assert!(unsound.unsound_acceptances > 0);
        assert!(unsound.median_verify_us_eip8288.is_none());
        assert!(unsound.median_verify_us_eip8479.is_none());
    }

    #[test]
    fn all_fourteen_mutation_classes_are_unique_and_covered() {
        let mut seen = std::collections::BTreeSet::new();
        for c in ALL_FOURTEEN_MUTATION_CLASSES {
            assert!(seen.insert(c));
        }
        assert_eq!(seen.len(), 14);
    }
}

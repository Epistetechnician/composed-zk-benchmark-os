use std::collections::{BTreeMap, BTreeSet};

use crate::{AssurancePropertyV1, AssuranceVerdictV1, DependencyDisclosureV1};

use super::types::EvidenceSnapshotV1;

pub fn evaluate_independence(snapshot: &EvidenceSnapshotV1) -> Option<bool> {
    let observation = snapshot
        .observations()
        .iter()
        .find(|value| value.property == AssurancePropertyV1::EvidenceRootDisclosure)?;
    if observation.verdict != AssuranceVerdictV1::Pass {
        return Some(false);
    }
    if observation.dependency_disclosure == DependencyDisclosureV1::Unknown {
        return Some(false);
    }
    let mut seen = BTreeSet::new();
    for root in observation
        .current_roots
        .iter()
        .chain(observation.dependency_roots.iter())
    {
        if !seen.insert(root.root_id().to_owned()) {
            return Some(false);
        }
    }
    if observation.current_roots.is_empty() {
        return Some(false);
    }
    // Dual-vendor collapse: distinct current roots that share a compromised
    // dependency root id are not an independent quorum.
    if shared_compromised_upstream(snapshot) {
        return Some(false);
    }
    Some(true)
}

fn shared_compromised_upstream(snapshot: &EvidenceSnapshotV1) -> bool {
    let mut dependency_to_currents: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
    for observation in snapshot.observations() {
        if observation.verdict != AssuranceVerdictV1::Pass {
            continue;
        }
        if observation.current_roots.is_empty() || observation.dependency_roots.is_empty() {
            continue;
        }
        for dependency in &observation.dependency_roots {
            let entry = dependency_to_currents
                .entry(dependency.root_id().to_owned())
                .or_default();
            for current in &observation.current_roots {
                entry.insert(current.root_id().to_owned());
            }
        }
    }
    dependency_to_currents
        .values()
        .any(|currents| currents.len() >= 2)
}

pub fn resolve_assurance_tier(
    snapshot: &EvidenceSnapshotV1,
    independence_ok: bool,
) -> super::types::AssuranceTierV1 {
    use super::types::AssuranceTierV1;
    if !independence_ok {
        return AssuranceTierV1::Quarantined;
    }
    let mut pass_count = 0_u32;
    for observation in snapshot.observations() {
        if observation.verdict == AssuranceVerdictV1::Pass {
            pass_count += 1;
        }
    }
    match pass_count {
        0 => AssuranceTierV1::Quarantined,
        1..=3 => AssuranceTierV1::UnprovenOrNovel,
        4..=6 => AssuranceTierV1::CurrentlyAssured,
        _ => AssuranceTierV1::StrongCurrentAssuranceLowImpact,
    }
}

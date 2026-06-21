// Throwaway capture utility: emit a fresh HSAI challenge packet for a real CVM
// capture. Uses the shipped crate functions. The agent public key is read from
// HSAI_AGENT_PUBKEY_SPKI_HEX (set by the operator); the private key never
// enters this binary or the repo.

use hsai_agent_case::{ActionId, AgentCase, MemoryRoot, ModelId, OracleContract, Verdict};
use hsai_attestation_phala::{
    build_agent_case_challenge_packet, capture_workflow_manifest, validate_hsai_challenge_packet,
    RealArtifactProviderMode,
};
use hsai_claim_envelope::{Predicate, PropertyKind, SubjectId};
use hsai_distinct_agent::{distinctness, Anchor};
use std::collections::BTreeSet;

const POLICY_ID: &str = "hsai-real-capture-2026-06-16:v1";

fn main() {
    let agent_pubkey_spki_hex = std::env::var("HSAI_AGENT_PUBKEY_SPKI_HEX")
        .expect("HSAI_AGENT_PUBKEY_SPKI_HEX must be set to the agent SPKI public key hex");
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .expect("clock");
    let expires_at = now + 3600; // 1 hour window

    let subject = SubjectId("hsai-capture-agent-2026-06-16".to_owned());
    let case = AgentCase {
        action: ActionId("admit-work".to_owned()),
        subject: subject.clone(),
        claimed_model: ModelId("hsai-capture-emitter-2026-06-16".to_owned()),
        memory_root: MemoryRoot([7; 32]),
        observed_at: now,
        oracle: OracleContract {
            expected: Verdict::Accept,
            target_guarantees: BTreeSet::from([distinctness(&subject)]),
            excluded: BTreeSet::from([Predicate {
                subject: SubjectId("hsai-capture-action".to_owned()),
                property: PropertyKind::SemanticCorrectness,
            }]),
        },
    };
    let anchor = Anchor::HardwareAttested {
        vendor: "phala-dstack".to_owned(),
        device: "hsai-capture-cvm".to_owned(),
    };

    let packet = build_agent_case_challenge_packet(
        &case,
        &anchor,
        &agent_pubkey_spki_hex,
        now, // nonce = creation timestamp, single-use
        now,
        expires_at,
        POLICY_ID,
    )
    .expect("challenge packet must build");

    validate_hsai_challenge_packet(&packet, now).expect("challenge packet must self-validate");

    let manifest =
        capture_workflow_manifest(packet.clone(), RealArtifactProviderMode::ManagedVerifier);

    println!("{}", serde_json::to_string_pretty(&packet).unwrap());
    println!();
    println!("{}", serde_json::to_string_pretty(&manifest).unwrap());
}

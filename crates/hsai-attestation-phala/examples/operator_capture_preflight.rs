//! Operator-facing capture preflight.
//!
//! Emits a JSON HSAI-owned challenge packet and a non-secret capture workflow
//! manifest from fixed sample inputs. This is capture input only: it is not
//! attestation evidence, not proof, not benchmark output, and not Phase 4
//! authorization. It performs no network access and does not fabricate an
//! artifact.
//!
//! An operator runs this example to obtain the exact
//! `expected_report_data_hex` that must be placed into the Phala/dstack
//! workload's `reportData` / `custom-data` field before a real quote or managed
//! verifier response is generated outside normal tests.

use hsai_agent_case::{ActionId, AgentCase, MemoryRoot, ModelId, OracleContract, Verdict};
use hsai_attestation_phala::{
    build_agent_case_challenge_packet, capture_workflow_manifest, validate_hsai_challenge_packet,
    RealArtifactProviderMode,
};
use hsai_claim_envelope::{Predicate, PropertyKind, SubjectId};
use hsai_distinct_agent::{distinctness, Anchor};
use std::collections::BTreeSet;

const AGENT_PUBKEY_SPKI_HEX: &str = "aabbccddeeff00112233445566778899";
const NONCE: u64 = 77;
const CHALLENGE_CREATED_AT: u64 = 1_750_000_000;
const CHALLENGE_EXPIRES_AT: u64 = 1_750_003_600;
const OBSERVED_AT: u64 = 1_750_000_000;
const POLICY_ID: &str = "operator-capture-preflight:v1";

fn sample_case() -> AgentCase {
    let subject = SubjectId("operator-capture-agent".to_owned());
    AgentCase {
        action: ActionId("admit-work".to_owned()),
        subject: subject.clone(),
        claimed_model: ModelId("operator-capture-emitter".to_owned()),
        memory_root: MemoryRoot([9; 32]),
        observed_at: OBSERVED_AT,
        oracle: OracleContract {
            expected: Verdict::Accept,
            target_guarantees: BTreeSet::from([distinctness(&subject)]),
            excluded: BTreeSet::from([Predicate {
                subject: SubjectId("operator-capture-action".to_owned()),
                property: PropertyKind::SemanticCorrectness,
            }]),
        },
    }
}

fn sample_anchor() -> Anchor {
    Anchor::HardwareAttested {
        vendor: "phala-dstack".to_owned(),
        device: "operator-capture-cvm".to_owned(),
    }
}

fn main() {
    let case = sample_case();
    let anchor = sample_anchor();

    let packet = build_agent_case_challenge_packet(
        &case,
        &anchor,
        AGENT_PUBKEY_SPKI_HEX,
        NONCE,
        CHALLENGE_CREATED_AT,
        CHALLENGE_EXPIRES_AT,
        POLICY_ID,
    )
    .expect("challenge packet must build from fixed sample inputs");

    // Local preflight: the packet must self-validate before it is handed to an
    // operator. This is not attestation validation; no artifact exists yet.
    validate_hsai_challenge_packet(&packet, OBSERVED_AT)
        .expect("challenge packet must self-validate at preflight time");

    let manifest =
        capture_workflow_manifest(packet.clone(), RealArtifactProviderMode::ManagedVerifier);

    let packet_json =
        serde_json::to_string_pretty(&packet).expect("challenge packet must serialize");
    let manifest_json =
        serde_json::to_string_pretty(&manifest).expect("capture manifest must serialize");

    println!("{packet_json}");
    println!();
    println!("{manifest_json}");

    eprintln!();
    eprintln!("claim boundary: {}", manifest.claim_boundary);
    eprintln!();
    eprintln!(
        "operator next step: place packet.expected_report_data_hex ({}) into the \
         Phala/dstack workload reportData/custom-data field, then run the real \
         capture outside normal tests. Do not commit secrets.",
        packet.expected_report_data_hex
    );
}

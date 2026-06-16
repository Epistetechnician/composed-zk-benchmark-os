use std::fs;
use std::path::Path;

use zkbench_core::{
    create_evidence_record_candidate, deserialize_evidence_acceptance_policy_json,
    deserialize_evidence_append_proposal_json, guard_claim_boundary_escalation,
    review_evidence_append_proposal, serialize_evidence_acceptance_policy_json,
    validate_evidence_record_candidate, ClaimBoundary, EvidenceAcceptancePolicy,
    EvidenceAppendProposalLedger, EvidenceLedger, EvidenceRecordCandidateStatus,
    EvidenceReviewChecklist, EvidenceReviewDecisionKind, EvidenceReviewerRole,
};

#[test]
fn reviewed_proposal_creates_candidate_without_ledger_mutation() {
    let proposal = deserialize_evidence_append_proposal_json(include_str!(
        "fixtures/evidence_append_proposal.json"
    ))
    .expect("proposal fixture should parse");
    let checklist = EvidenceReviewChecklist::satisfied_phase_j_default();
    let decision = review_evidence_append_proposal(
        &proposal,
        EvidenceReviewerRole::EvidenceReviewer,
        EvidenceReviewDecisionKind::ApproveForCandidateOnly,
        checklist,
    )
    .expect("human review should approve candidate-only creation");
    let policy = EvidenceAcceptancePolicy::phase_j_conservative();
    let candidate =
        create_evidence_record_candidate(&policy, &proposal, &decision).expect("candidate");

    assert_eq!(
        candidate.proposed_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert_eq!(
        candidate.status,
        EvidenceRecordCandidateStatus::CandidateOnly
    );
    assert!(!candidate.claims_accepted_evidence);
    assert!(!candidate.is_official_benchmark_evidence());
    assert!(validate_evidence_record_candidate(&candidate).valid);

    let ledger = EvidenceLedger::new();
    let proposal_ledger = EvidenceAppendProposalLedger::new();
    assert_eq!(ledger.entries.len(), 0);
    assert_eq!(proposal_ledger.entries.len(), 0);
}

#[test]
fn escalation_guard_blocks_level2_candidate_creation() {
    let proposal = deserialize_evidence_append_proposal_json(include_str!(
        "fixtures/evidence_append_proposal.json"
    ))
    .expect("proposal fixture should parse");
    let checklist = EvidenceReviewChecklist::satisfied_phase_j_default();
    let decision = review_evidence_append_proposal(
        &proposal,
        EvidenceReviewerRole::Maintainer,
        EvidenceReviewDecisionKind::ApproveForCandidateOnly,
        checklist,
    )
    .expect("review should succeed");
    let policy = EvidenceAcceptancePolicy::phase_j_conservative();
    let validation = policy.validate_proposal_for_candidate(
        &proposal,
        &decision,
        ClaimBoundary::Level2ReproducibleBenchmarkArtifact,
    );

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path.contains("target_claim_boundary")));
}

#[test]
fn default_escalation_guard_rejects_level0_to_level1_without_policy() {
    let result = guard_claim_boundary_escalation(
        ClaimBoundary::Level0DesignNote,
        ClaimBoundary::Level1LocalReplay,
        false,
    );
    assert!(result.is_err());
}

#[test]
fn level1_local_policy_allows_strict_local_candidate_boundary() {
    let result = guard_claim_boundary_escalation(
        ClaimBoundary::Level0DesignNote,
        ClaimBoundary::Level1LocalReplay,
        true,
    )
    .expect("Level1 local-only policy should allow strict local escalation");
    assert!(result.allowed);
}

#[test]
fn automated_reviewer_cannot_approve_candidate_creation() {
    let proposal = deserialize_evidence_append_proposal_json(include_str!(
        "fixtures/evidence_append_proposal.json"
    ))
    .expect("proposal fixture should parse");
    let checklist = EvidenceReviewChecklist::satisfied_phase_j_default();
    let decision = review_evidence_append_proposal(
        &proposal,
        EvidenceReviewerRole::AutomatedPolicyCheck,
        EvidenceReviewDecisionKind::ApproveForCandidateOnly,
        checklist,
    );

    assert!(decision.is_err());
}

#[test]
fn acceptance_policy_round_trips_deterministically() {
    let policy = EvidenceAcceptancePolicy::phase_j_conservative();
    let json = serialize_evidence_acceptance_policy_json(&policy)
        .expect("acceptance policy should serialize");
    let parsed =
        deserialize_evidence_acceptance_policy_json(&json).expect("policy should deserialize");
    let json_again =
        serialize_evidence_acceptance_policy_json(&parsed).expect("policy should serialize again");

    assert_eq!(policy, parsed);
    assert_eq!(json, json_again);
    assert!(json.contains("Evidence-record candidates are not accepted evidence"));
}

#[test]
fn phase_j_source_contains_no_process_command_api() {
    let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let source = read_source_tree(&manifest_dir.join("src/evidence"));

    assert!(!source.contains("std::process::Command"));
    assert!(!source.contains("Command::new"));
}

fn read_source_tree(root: &Path) -> String {
    let mut combined = String::new();
    read_source_tree_into(root, &mut combined);
    combined
}

fn read_source_tree_into(path: &Path, combined: &mut String) {
    if path.is_file() {
        let text = fs::read_to_string(path).expect("source file should be readable");
        combined.push_str(&text);
        combined.push('\n');
        return;
    }
    for entry in fs::read_dir(path).expect("source directory should be readable") {
        let entry = entry.expect("source directory entry should be readable");
        read_source_tree_into(&entry.path(), combined);
    }
}

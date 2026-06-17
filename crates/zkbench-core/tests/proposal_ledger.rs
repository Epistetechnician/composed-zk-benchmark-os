use tempfile::tempdir;
use zkbench_core::{
    create_evidence_append_proposal, deserialize_evidence_append_proposal_ledger_json,
    deserialize_external_result_candidate_json, normalize_synthetic_result_candidate,
    serialize_evidence_append_proposal_ledger_json, validate_synthetic_result_candidate,
    ClaimBoundary, EvidenceAppendProposalLedger, ResultCandidateArtifactResolver,
};

fn resolver() -> ResultCandidateArtifactResolver {
    ResultCandidateArtifactResolver::from_in_memory_bytes(vec![(
        "artifacts/synthetic_metric_source.json".to_string(),
        b"synthetic metric source v1\n".to_vec(),
    )])
}

fn proposal() -> zkbench_core::EvidenceAppendProposal {
    let candidate = deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_valid.json"
    ))
    .expect("fixture should parse");
    let resolver = resolver();
    let validation = validate_synthetic_result_candidate(&candidate, &resolver);
    let draft = normalize_synthetic_result_candidate(&candidate, &validation, &resolver)
        .expect("valid candidate should normalize");
    create_evidence_append_proposal(&draft).expect("proposal should build")
}

#[test]
fn empty_proposal_ledger_fixture_validates() {
    let ledger = deserialize_evidence_append_proposal_ledger_json(include_str!(
        "fixtures/proposal_ledger.json"
    ))
    .expect("ledger fixture should parse");
    let validation = ledger.validate();

    assert!(validation.valid, "{:?}", validation.issues);
    assert_eq!(validation.summary.entry_count, 0);
}

#[test]
fn proposal_ledger_appends_valid_proposal_and_roundtrips() {
    let mut ledger = EvidenceAppendProposalLedger::new();
    ledger
        .append(proposal())
        .expect("proposal append should work");
    let validation = ledger.validate();
    assert!(validation.valid, "{:?}", validation.issues);
    assert_eq!(validation.summary.entry_count, 1);

    let json =
        serialize_evidence_append_proposal_ledger_json(&ledger).expect("ledger should serialize");
    let parsed =
        deserialize_evidence_append_proposal_ledger_json(&json).expect("ledger should deserialize");
    assert_eq!(ledger, parsed);
}

#[test]
fn proposal_ledger_rejects_invalid_proposal_before_append() {
    let mut proposal = proposal();
    proposal.proposed_claim_boundary = ClaimBoundary::Level1LocalReplay;
    let mut ledger = EvidenceAppendProposalLedger::new();

    let error = ledger
        .append(proposal)
        .expect_err("invalid proposal should be rejected before append");

    assert!(error.to_string().contains("proposal validation failed"));
    assert!(ledger.entries.is_empty());
    assert_eq!(ledger.summary.entry_count, 0);
}

#[test]
fn proposal_ledger_detects_stale_cached_summary() {
    let mut ledger = EvidenceAppendProposalLedger::new();
    ledger
        .append(proposal())
        .expect("proposal append should work");
    ledger.summary.entry_count = 0;

    let validation = ledger.validate();

    assert!(!validation.valid);
    assert_eq!(validation.summary.entry_count, 1);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.message.contains("cached summary")));
}

#[test]
fn proposal_ledger_persists_as_json() {
    let mut ledger = EvidenceAppendProposalLedger::new();
    ledger
        .append(proposal())
        .expect("proposal append should work");
    let dir = tempdir().expect("tempdir should be available");
    let path = dir.path().join("proposal-ledger.json");

    ledger.save_json(&path).expect("ledger should save");
    let loaded =
        EvidenceAppendProposalLedger::load_json(&path).expect("ledger should load from json");
    assert_eq!(ledger, loaded);
}

#[test]
fn proposal_ledger_detects_tampering() {
    let mut ledger = EvidenceAppendProposalLedger::new();
    ledger
        .append(proposal())
        .expect("proposal append should work");
    ledger.entries[0]
        .proposal
        .notes
        .push("tampered local note".to_string());

    let validation = ledger.validate();
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.message.contains("digest mismatch")));
}

use tempfile::tempdir;
use zkbench_core::{
    create_evidence_append_proposal, deserialize_evidence_append_proposal_ledger_json,
    deserialize_external_result_candidate_json, normalize_synthetic_result_candidate,
    serialize_evidence_append_proposal_ledger_json, validate_synthetic_result_candidate,
    ClaimBoundary, EvidenceAppendProposalLedger, EvidenceAppendProposalReviewState,
    EvidenceAppendProposalStatus, ResultCandidateArtifactResolver,
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
fn proposal_ledger_default_matches_new_and_chains_multiple_entries() {
    let mut ledger = EvidenceAppendProposalLedger::default();
    assert_eq!(ledger, EvidenceAppendProposalLedger::new());

    let first = proposal();
    let mut second = proposal();
    second.id.push_str("_second");
    second.source_normalized_draft_id.push_str("_second");

    ledger.append(first).expect("first proposal should append");
    ledger
        .append(second)
        .expect("second proposal should append");

    let validation = ledger.validate();
    assert!(validation.valid, "{:?}", validation.issues);
    assert_eq!(validation.summary.entry_count, 2);
    assert_eq!(ledger.entries[0].sequence_number, 0);
    assert_eq!(ledger.entries[1].sequence_number, 1);
    assert_eq!(
        ledger.entries[1].previous_digest,
        Some(ledger.entries[0].entry_digest.clone())
    );
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
fn proposal_ledger_rejects_forbidden_claim_text_in_notes() {
    let mut ledger = EvidenceAppendProposalLedger::new();
    ledger
        .append(proposal())
        .expect("proposal append should work");
    ledger
        .notes
        .push("this proposal ledger is official benchmark evidence".to_string());

    let validation = ledger.validate();

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.message.contains("notes[2]")));
}

#[test]
fn proposal_ledger_rejects_forbidden_claim_text_in_entry_notes() {
    let mut ledger = EvidenceAppendProposalLedger::new();
    ledger
        .append(proposal())
        .expect("proposal append should work");
    ledger.entries[0]
        .notes
        .push("this proposal ledger entry is official benchmark evidence".to_string());

    let validation = ledger.validate();

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.message.contains("entries[0].notes[0]")));
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

#[test]
fn proposal_ledger_detects_sequence_previous_digest_and_proposal_state_drift() {
    let mut ledger = EvidenceAppendProposalLedger::new();
    ledger
        .append(proposal())
        .expect("first proposal append should work");
    let mut second = proposal();
    second.id.push_str("_second");
    second.source_normalized_draft_id.push_str("_second");
    ledger
        .append(second)
        .expect("second proposal append should work");

    ledger.entries[1].sequence_number = 7;
    ledger.entries[1].previous_digest = None;
    ledger.entries[1].proposal.proposed_artifact_refs[0]
        .artifact_ref
        .clear();
    ledger.entries[1].proposal.status = EvidenceAppendProposalStatus::ApprovedForFutureAppendOnly;
    ledger.entries[1].proposal.review_state = EvidenceAppendProposalReviewState::PendingReview;

    let validation = ledger.validate();

    assert!(!validation.valid);
    for expected in [
        "sequence number 7 does not match index 1",
        "previous digest does not match prior entry",
        "proposal validation failed",
        "proposal state does not authorize accepted evidence",
        "entry digest mismatch",
    ] {
        assert!(
            validation
                .issues
                .iter()
                .any(|issue| issue.message.contains(expected)),
            "missing expected validation issue containing {expected:?}: {:?}",
            validation.issues
        );
    }
}

#[test]
fn proposal_ledger_json_file_errors_are_reported() {
    let mut ledger = EvidenceAppendProposalLedger::new();
    ledger
        .append(proposal())
        .expect("proposal append should work");
    let dir = tempdir().expect("tempdir should be available");

    let save_error = ledger
        .save_json(dir.path())
        .expect_err("saving JSON to a directory should fail");
    assert!(save_error
        .to_string()
        .contains(&dir.path().display().to_string()));

    let missing_path = dir.path().join("missing-ledger.json");
    let read_error = EvidenceAppendProposalLedger::load_json(&missing_path)
        .expect_err("missing ledger file should fail to load");
    assert!(read_error.to_string().contains("missing-ledger.json"));

    let malformed_path = dir.path().join("malformed-ledger.json");
    std::fs::write(&malformed_path, b"{not-json").expect("malformed fixture should write");
    let parse_error = EvidenceAppendProposalLedger::load_json(&malformed_path)
        .expect_err("malformed ledger JSON should fail to parse");
    assert!(parse_error
        .to_string()
        .contains("proposal_ledger.load_json"));
}

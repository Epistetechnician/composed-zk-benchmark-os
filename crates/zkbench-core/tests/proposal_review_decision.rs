use zkbench_core::{
    build_default_evidence_review_checklist, deserialize_evidence_review_decision_json,
    review_evidence_append_proposal, serialize_evidence_review_decision_json,
    validate_evidence_review_decision, EvidenceReviewChecklist, EvidenceReviewDecision,
    EvidenceReviewDecisionKind, EvidenceReviewerRole,
};

fn proposal() -> zkbench_core::EvidenceAppendProposal {
    zkbench_core::deserialize_evidence_append_proposal_json(include_str!(
        "fixtures/evidence_append_proposal.json"
    ))
    .expect("proposal fixture should parse")
}

#[test]
fn default_review_checklist_is_unsatisfied_until_reviewed() {
    let checklist = build_default_evidence_review_checklist();

    assert!(!checklist.required_items_satisfied());
    assert!(checklist.unsatisfied_required_item_ids().len() >= 4);
}

#[test]
fn manual_candidate_only_decision_validates() {
    let decision = review_evidence_append_proposal(
        &proposal(),
        EvidenceReviewerRole::Maintainer,
        EvidenceReviewDecisionKind::ApproveForCandidateOnly,
        EvidenceReviewChecklist::satisfied_phase_j_default(),
    )
    .expect("manual review should create a decision");
    let report = validate_evidence_review_decision(&decision);

    assert!(report.valid, "{:?}", report.blocking_issues);
    assert!(decision.approves_candidate_only());
}

#[test]
fn automated_policy_check_alone_cannot_approve_candidate() {
    let err = review_evidence_append_proposal(
        &proposal(),
        EvidenceReviewerRole::AutomatedPolicyCheck,
        EvidenceReviewDecisionKind::ApproveForCandidateOnly,
        EvidenceReviewChecklist::satisfied_phase_j_default(),
    )
    .expect_err("automated-only approval must be rejected");

    assert!(err.to_string().contains("cannot approve candidate"));
}

#[test]
fn review_decision_fixture_roundtrips() {
    let decision: EvidenceReviewDecision = deserialize_evidence_review_decision_json(include_str!(
        "fixtures/proposal_review_decision.json"
    ))
    .expect("decision fixture should parse");
    let report = validate_evidence_review_decision(&decision);
    assert!(report.valid, "{:?}", report.blocking_issues);

    let json =
        serialize_evidence_review_decision_json(&decision).expect("decision should serialize");
    let parsed =
        deserialize_evidence_review_decision_json(&json).expect("decision should deserialize");
    assert_eq!(decision, parsed);
}

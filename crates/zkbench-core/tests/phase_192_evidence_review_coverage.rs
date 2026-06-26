use zkbench_core::{
    build_default_evidence_review_checklist, deserialize_evidence_review_checklist_json,
    deserialize_evidence_review_decision_json, review_evidence_append_proposal,
    serialize_evidence_review_checklist_json, validate_evidence_review_decision, ClaimBoundary,
    EvidenceReviewChecklist, EvidenceReviewDecision, EvidenceReviewDecisionKind,
    EvidenceReviewDecisionStatus, EvidenceReviewFinding, EvidenceReviewFindingSeverity,
    EvidenceReviewPolicy, EvidenceReviewerRole,
};

fn proposal() -> zkbench_core::EvidenceAppendProposal {
    zkbench_core::deserialize_evidence_append_proposal_json(include_str!(
        "fixtures/evidence_append_proposal.json"
    ))
    .expect("proposal fixture should parse")
}

fn satisfied_checklist() -> EvidenceReviewChecklist {
    EvidenceReviewChecklist::satisfied_phase_j_default()
}

#[test]
fn evidence_review_policy_default_declares_manual_boundary() {
    let policy = EvidenceReviewPolicy::default();

    assert_eq!(policy.id, "phase_j_manual_review_policy");
    assert_eq!(
        policy.required_human_roles,
        vec![
            EvidenceReviewerRole::Maintainer,
            EvidenceReviewerRole::ResearchReviewer,
            EvidenceReviewerRole::EvidenceReviewer
        ]
    );
    assert!(policy
        .notes
        .iter()
        .any(|note| note.contains("not accepted evidence")));
    assert!(policy
        .notes
        .iter()
        .any(|note| note.contains("AutomatedPolicyCheck alone")));
    assert!(EvidenceReviewerRole::Maintainer.is_human_review_role());
    assert!(EvidenceReviewerRole::ResearchReviewer.is_human_review_role());
    assert!(EvidenceReviewerRole::EvidenceReviewer.is_human_review_role());
    assert!(!EvidenceReviewerRole::AutomatedPolicyCheck.is_human_review_role());
    assert!(!EvidenceReviewerRole::FutureExternalReviewer.is_human_review_role());
}

#[test]
fn evidence_review_builders_cover_reject_changes_and_append_preview_paths() {
    let rejected = EvidenceReviewDecision::reject(
        EvidenceReviewerRole::FutureExternalReviewer,
        "proposal_rejected",
        vec!["manual rejection recorded".to_string()],
    );
    assert_eq!(rejected.id, "review_decision_proposal_rejected_rejected");
    assert_eq!(
        rejected.decision_status,
        EvidenceReviewDecisionStatus::FinalizedRejected
    );
    assert_eq!(
        rejected.claim_boundary_decision,
        ClaimBoundary::Level0DesignNote
    );
    assert!(!rejected.approves_candidate_only());

    let changes = EvidenceReviewDecision::request_changes(
        EvidenceReviewerRole::EvidenceReviewer,
        "proposal_changes",
        vec!["missing provenance detail".to_string()],
    );
    assert_eq!(
        changes.decision_status,
        EvidenceReviewDecisionStatus::FinalizedChangesRequested
    );
    assert!(changes
        .blocking_issues
        .iter()
        .any(|issue| issue.contains("changes requested")));
    assert!(!changes.approves_candidate_only());

    let preview = review_evidence_append_proposal(
        &proposal(),
        EvidenceReviewerRole::ResearchReviewer,
        EvidenceReviewDecisionKind::ApproveForFutureAppendPreview,
        satisfied_checklist(),
    )
    .expect("append-preview review decision should build from satisfied manual review");
    assert!(preview.id.ends_with("_append_preview"));
    assert_eq!(
        preview.decision_kind,
        EvidenceReviewDecisionKind::ApproveForFutureAppendPreview
    );
    assert_eq!(
        preview.decision_status,
        EvidenceReviewDecisionStatus::FinalizedCandidateOnly
    );
    assert!(!preview.approves_candidate_only());
}

#[test]
fn evidence_review_validation_reports_shape_role_checklist_and_text_rejections() {
    let mut decision = EvidenceReviewDecision::approve_for_candidate_only(
        EvidenceReviewerRole::Maintainer,
        "proposal_validation_edges",
        satisfied_checklist(),
    )
    .expect("baseline decision should build");
    decision.id.clear();
    decision.source_proposal_id = "   ".to_string();
    decision.reviewer_role = EvidenceReviewerRole::AutomatedPolicyCheck;
    decision.checklist = build_default_evidence_review_checklist();
    decision
        .notes
        .push("claims official benchmark evidence".to_string());
    decision
        .blocking_issues
        .push("claims a formal proof of acceptance".to_string());
    decision.findings.push(EvidenceReviewFinding {
        id: "forbidden_finding".to_string(),
        message: "claims official benchmark evidence for a candidate".to_string(),
        severity: EvidenceReviewFindingSeverity::Blocking,
        blocking: true,
    });
    decision.checklist.items[0]
        .notes
        .push("claims official benchmark evidence".to_string());

    let report = validate_evidence_review_decision(&decision);

    assert!(!report.valid);
    assert!(report.decision_id.is_empty());
    assert!(report
        .notes
        .iter()
        .any(|note| note.contains("not accepted evidence")));
    for expected in [
        "review decision id is empty",
        "source proposal id is empty",
        "AutomatedPolicyCheck alone cannot approve candidate creation",
        "required checklist items are not satisfied",
        "decision notes[2] contain a forbidden claim",
        "decision blocking_issues[0] contain a forbidden claim",
        "decision findings[0] contain a forbidden claim",
        "decision checklist items[0].notes[0] contain a forbidden claim",
    ] {
        assert!(
            report
                .blocking_issues
                .iter()
                .any(|issue| issue.contains(expected)),
            "missing expected issue: {expected}; got {:?}",
            report.blocking_issues
        );
    }
}

#[test]
fn evidence_review_checklist_helpers_and_json_contexts_are_exercised() {
    let empty = EvidenceReviewChecklist {
        items: Vec::new(),
        requirements: Vec::new(),
        findings: Vec::new(),
        decisions: Vec::new(),
    };
    assert!(!empty.required_items_satisfied());
    assert!(empty.unsatisfied_required_item_ids().is_empty());

    let mut optional_only = build_default_evidence_review_checklist();
    for item in &mut optional_only.items {
        item.required = false;
    }
    assert!(optional_only.required_items_satisfied());
    assert!(optional_only.unsatisfied_required_item_ids().is_empty());

    let checklist_json = serialize_evidence_review_checklist_json(&optional_only)
        .expect("checklist should serialize");
    let parsed = deserialize_evidence_review_checklist_json(&checklist_json)
        .expect("checklist should deserialize");
    assert_eq!(optional_only, parsed);

    let checklist_error = deserialize_evidence_review_checklist_json("{not json")
        .expect_err("malformed checklist json should fail closed");
    assert!(checklist_error
        .to_string()
        .contains("deserialize_evidence_review_checklist_json"));

    let decision_error = deserialize_evidence_review_decision_json("{not json")
        .expect_err("malformed decision json should fail closed");
    assert!(decision_error
        .to_string()
        .contains("deserialize_evidence_review_decision_json"));
}

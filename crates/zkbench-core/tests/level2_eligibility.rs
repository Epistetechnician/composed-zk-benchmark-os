use zkbench_core::{
    check_level2_eligibility, create_evidence_record_candidate,
    deserialize_level2_eligibility_report_json, review_evidence_append_proposal,
    serialize_level2_eligibility_report_json, ClaimBoundary, EvidenceAcceptancePolicy,
    EvidenceReviewChecklist, EvidenceReviewDecisionKind, EvidenceReviewerRole,
    Level2EligibilityBlockingReason, Level2EligibilityChecker, Level2EligibilityReport,
    Level2EligibilityStatus,
};

fn candidate() -> zkbench_core::EvidenceRecordCandidate {
    let proposal = zkbench_core::deserialize_evidence_append_proposal_json(include_str!(
        "fixtures/evidence_append_proposal.json"
    ))
    .expect("proposal fixture should parse");
    let decision = review_evidence_append_proposal(
        &proposal,
        EvidenceReviewerRole::Maintainer,
        EvidenceReviewDecisionKind::ApproveForCandidateOnly,
        EvidenceReviewChecklist::satisfied_phase_j_default(),
    )
    .expect("manual decision should build");
    let policy = EvidenceAcceptancePolicy::phase_j_level1_local_only();

    create_evidence_record_candidate(&policy, &proposal, &decision)
        .expect("reviewed candidate should build")
}

#[test]
fn complete_candidate_can_be_eligible_for_future_review_only() {
    let report = check_level2_eligibility(&candidate()).expect("eligibility should run");

    assert_eq!(
        report.status,
        Level2EligibilityStatus::EligibleForFutureReview
    );
    assert_eq!(report.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert!(!report.creates_level2_evidence);
    assert!(!report.creates_level2_evidence());
}

#[test]
fn missing_required_external_capture_is_insufficient_information() {
    let checker = Level2EligibilityChecker {
        require_external_artifact_capture: true,
        ..Level2EligibilityChecker::default()
    };
    let report = checker
        .check(&candidate())
        .expect("eligibility should run without external execution");

    assert_eq!(
        report.status,
        Level2EligibilityStatus::InsufficientInformation
    );
    assert!(report
        .blocking_reasons
        .contains(&Level2EligibilityBlockingReason::MissingExternalArtifactCapture));
    assert!(!report.creates_level2_evidence);
}

#[test]
fn eligibility_report_fixture_roundtrips() {
    let report: Level2EligibilityReport = deserialize_level2_eligibility_report_json(include_str!(
        "fixtures/level2_eligibility_report.json"
    ))
    .expect("eligibility report fixture should parse");
    assert_eq!(
        report.status,
        Level2EligibilityStatus::EligibleForFutureReview
    );
    assert!(!report.creates_level2_evidence);

    let json = serialize_level2_eligibility_report_json(&report).expect("report should serialize");
    let parsed =
        deserialize_level2_eligibility_report_json(&json).expect("report should deserialize");
    assert_eq!(report, parsed);
}

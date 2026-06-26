use zkbench_core::{
    check_level2_eligibility, create_evidence_record_candidate,
    deserialize_level2_eligibility_report_json, review_evidence_append_proposal, ClaimBoundary,
    EvidenceAcceptancePolicy, EvidenceReviewChecklist, EvidenceReviewDecisionKind,
    EvidenceReviewerRole, Level2EligibilityBlockingReason, Level2EligibilityChecker,
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

fn requirement_satisfied(report: &zkbench_core::Level2EligibilityReport, id: &str) -> Option<bool> {
    report
        .requirements
        .iter()
        .find(|requirement| requirement.id == id)
        .map(|requirement| requirement.satisfied)
}

#[test]
fn eligibility_checker_reports_required_marker_paths_without_evidence_elevation() {
    let checker = Level2EligibilityChecker {
        require_external_artifact_capture: true,
        require_replay_manifest: true,
        notes: vec!["phase 182 local checker configuration".to_string()],
    };

    let missing = checker
        .check(&candidate())
        .expect("eligibility should run without external execution");
    assert_eq!(
        missing.status,
        Level2EligibilityStatus::InsufficientInformation
    );
    assert_eq!(missing.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert!(!missing.creates_level2_evidence);
    assert!(!missing.creates_level2_evidence());
    assert!(missing
        .blocking_reasons
        .contains(&Level2EligibilityBlockingReason::MissingExternalArtifactCapture));
    assert!(missing
        .blocking_reasons
        .contains(&Level2EligibilityBlockingReason::MissingReplayManifest));
    assert_eq!(
        requirement_satisfied(&missing, "external_artifact_capture_marker"),
        Some(false)
    );
    assert_eq!(
        requirement_satisfied(&missing, "replay_manifest_marker"),
        Some(false)
    );

    let mut marked = candidate();
    marked
        .notes
        .push("external artifact capture reviewed by maintainer".to_string());
    marked
        .notes
        .push("replay manifest reviewed by maintainer".to_string());
    let accepted = checker
        .check(&marked)
        .expect("review markers should satisfy future-review metadata gates");
    assert_eq!(
        accepted.status,
        Level2EligibilityStatus::EligibleForFutureReview
    );
    assert!(accepted.blocking_reasons.is_empty());
    assert_eq!(
        requirement_satisfied(&accepted, "external_artifact_capture_marker"),
        Some(true)
    );
    assert_eq!(
        requirement_satisfied(&accepted, "replay_manifest_marker"),
        Some(true)
    );
}

#[test]
fn eligibility_blocks_invalid_candidates_and_records_blocking_finding() {
    let mut invalid = candidate();
    invalid.id.clear();
    invalid.proposed_artifact_refs.clear();
    invalid.validation_report_digest = None;
    invalid.proposed_provenance_summary.clear();

    let report = check_level2_eligibility(&invalid).expect("invalid candidate should report");
    assert_eq!(report.status, Level2EligibilityStatus::Blocked);
    assert!(report
        .blocking_reasons
        .contains(&Level2EligibilityBlockingReason::CandidateInvalid));
    assert!(report
        .blocking_reasons
        .contains(&Level2EligibilityBlockingReason::MissingArtifactDigest));
    assert!(report
        .blocking_reasons
        .contains(&Level2EligibilityBlockingReason::MissingProvenance));
    assert_eq!(
        requirement_satisfied(&report, "candidate_valid"),
        Some(false)
    );
    assert_eq!(
        requirement_satisfied(&report, "artifact_digests_present"),
        Some(false)
    );
    assert_eq!(
        requirement_satisfied(&report, "provenance_present"),
        Some(false)
    );

    let finding = report
        .findings
        .iter()
        .find(|finding| finding.id == "candidate_invalid")
        .expect("candidate invalid finding should be present");
    assert_eq!(
        finding.blocking_reason,
        Some(Level2EligibilityBlockingReason::CandidateInvalid)
    );
    assert!(finding.message.contains("candidate validation failed"));
}

#[test]
fn eligibility_blocks_forbidden_claim_flags_and_level2_boundary() {
    let mut candidate = candidate();
    candidate.claims_official_benchmark_evidence = true;
    candidate.claims_formal_evidence = true;
    candidate.claims_proof_system_soundness = true;
    candidate.proposed_claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;

    let report = check_level2_eligibility(&candidate)
        .expect("forbidden claim flags should fail closed as eligibility metadata");
    assert_eq!(report.status, Level2EligibilityStatus::Blocked);
    for reason in [
        Level2EligibilityBlockingReason::CandidateInvalid,
        Level2EligibilityBlockingReason::OfficialClaimDetected,
        Level2EligibilityBlockingReason::FormalClaimDetected,
        Level2EligibilityBlockingReason::SoundnessClaimDetected,
        Level2EligibilityBlockingReason::Level2ActualEvidenceBlocked,
    ] {
        assert!(
            report.blocking_reasons.contains(&reason),
            "missing {reason:?}: {report:?}"
        );
    }
    assert_eq!(report.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert!(!report.creates_level2_evidence);
}

#[test]
fn malformed_eligibility_report_json_preserves_deserialization_context() {
    let error = deserialize_level2_eligibility_report_json("{\"id\":")
        .expect_err("malformed eligibility report json should preserve parser context");
    let message = error.to_string();
    assert!(message.contains("deserialize_level2_eligibility_report_json"));
    assert!(message.contains("EOF") || message.contains("expected"));
}

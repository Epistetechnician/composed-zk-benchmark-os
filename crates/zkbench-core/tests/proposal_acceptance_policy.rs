use zkbench_core::{
    build_default_evidence_acceptance_policy, create_evidence_record_candidate,
    deserialize_evidence_acceptance_policy_json, guard_claim_boundary_escalation,
    review_evidence_append_proposal, serialize_evidence_acceptance_policy_json,
    validate_evidence_acceptance_policy, ClaimBoundary, EvidenceAcceptanceBlockingReason,
    EvidenceAcceptancePolicy, EvidenceAcceptancePolicyMode, EvidenceAppendProposalReviewState,
    EvidenceAppendProposalStatus, EvidenceClass, EvidenceReviewChecklist,
    EvidenceReviewDecisionKind, EvidenceReviewerRole, SyntheticImportValidationIssue,
    SyntheticImportValidationIssueKind,
};

fn proposal() -> zkbench_core::EvidenceAppendProposal {
    zkbench_core::deserialize_evidence_append_proposal_json(include_str!(
        "fixtures/evidence_append_proposal.json"
    ))
    .expect("proposal fixture should parse")
}

fn decision(
    proposal: &zkbench_core::EvidenceAppendProposal,
) -> zkbench_core::EvidenceReviewDecision {
    review_evidence_append_proposal(
        proposal,
        EvidenceReviewerRole::Maintainer,
        EvidenceReviewDecisionKind::ApproveForCandidateOnly,
        EvidenceReviewChecklist::satisfied_phase_j_default(),
    )
    .expect("manual decision should build")
}

#[test]
fn default_acceptance_policy_validates() {
    let policy = build_default_evidence_acceptance_policy();
    let validation = validate_evidence_acceptance_policy(&policy);

    assert!(validation.valid, "{:?}", validation.issues);
}

#[test]
fn default_trait_builds_conservative_candidate_policy() {
    let policy = EvidenceAcceptancePolicy::default();

    assert_eq!(policy, build_default_evidence_acceptance_policy());
    assert_eq!(policy.mode, EvidenceAcceptancePolicyMode::CandidateOnly);
}

#[test]
fn acceptance_policy_round_trips_through_json() {
    let policy = EvidenceAcceptancePolicy::phase_j_level1_local_only();
    let json = serialize_evidence_acceptance_policy_json(&policy).expect("policy should serialize");
    let reparsed =
        deserialize_evidence_acceptance_policy_json(&json).expect("policy should deserialize");

    assert_eq!(reparsed, policy);
    assert!(validate_evidence_acceptance_policy(&reparsed).valid);
}

#[test]
fn malformed_acceptance_policy_json_reports_deserialization_error() {
    let error = deserialize_evidence_acceptance_policy_json("{not-json")
        .expect_err("malformed policy JSON should fail");

    assert!(error
        .to_string()
        .contains("deserialize_evidence_acceptance_policy_json"));
}

#[test]
fn policy_validation_reports_all_static_policy_rejection_paths() {
    let mut policy = build_default_evidence_acceptance_policy();
    policy.id.clear();
    policy.mode = EvidenceAcceptancePolicyMode::ProposalOnly;
    policy
        .allowed_claim_boundaries
        .push(ClaimBoundary::Level2ReproducibleBenchmarkArtifact);

    let validation = validate_evidence_acceptance_policy(&policy);
    let issue_paths = validation
        .issues
        .iter()
        .map(|issue| issue.path.as_str())
        .collect::<Vec<_>>();

    assert!(!validation.valid);
    for expected in [
        "policy.id",
        "policy.mode",
        "policy.allowed_claim_boundaries",
    ] {
        assert!(
            issue_paths.contains(&expected),
            "missing expected issue path {expected}; got {issue_paths:?}"
        );
    }
}

#[test]
fn policy_accepts_reviewed_candidate_only_proposal() {
    let proposal = proposal();
    let decision = decision(&proposal);
    let policy = build_default_evidence_acceptance_policy();

    let validation = policy.validate_proposal_for_candidate(
        &proposal,
        &decision,
        ClaimBoundary::Level0DesignNote,
    );

    assert!(validation.valid, "{:?}", validation.issues);
}

#[test]
fn proposal_only_policy_blocks_candidate_creation_through_rule_results() {
    let proposal = proposal();
    let decision = decision(&proposal);
    let mut policy = build_default_evidence_acceptance_policy();
    policy.mode = EvidenceAcceptancePolicyMode::ProposalOnly;

    let validation = policy.validate_proposal_for_candidate(
        &proposal,
        &decision,
        ClaimBoundary::Level0DesignNote,
    );

    assert!(!validation.valid);
    assert!(validation.rule_results.iter().any(|result| {
        !result.passed
            && result.blocking_reason
                == Some(EvidenceAcceptanceBlockingReason::ProposalNotReviewable)
    }));
}

#[test]
fn proposal_validation_reports_source_proposal_rejection_paths() {
    let mut proposal = proposal();
    let decision = decision(&proposal);
    let policy = build_default_evidence_acceptance_policy();
    proposal.status = EvidenceAppendProposalStatus::Superseded;
    proposal.review_state = EvidenceAppendProposalReviewState::Rejected;
    proposal
        .blocking_issues
        .push(SyntheticImportValidationIssue::error(
            SyntheticImportValidationIssueKind::OfficialClaimDetected,
            "candidate.notes[0]",
            "official benchmark claim",
        ));
    proposal.proposed_evidence_class = EvidenceClass::ReproducibleBenchmarkArtifact;
    proposal.proposed_artifact_refs.clear();
    proposal.proposed_provenance_summary.clear();

    let validation = policy.validate_proposal_for_candidate(
        &proposal,
        &decision,
        ClaimBoundary::Level0DesignNote,
    );
    let reasons = validation
        .issues
        .iter()
        .map(|issue| issue.blocking_reason)
        .collect::<Vec<_>>();

    assert!(!validation.valid);
    for expected in [
        EvidenceAcceptanceBlockingReason::ProposalNotReviewable,
        EvidenceAcceptanceBlockingReason::ProposalRejected,
        EvidenceAcceptanceBlockingReason::ProposalHasBlockingIssues,
        EvidenceAcceptanceBlockingReason::DisallowedEvidenceClass,
        EvidenceAcceptanceBlockingReason::MissingArtifactDigest,
        EvidenceAcceptanceBlockingReason::MissingProvenance,
    ] {
        assert!(
            reasons.contains(&expected),
            "missing expected reason {expected:?}; got {reasons:?}"
        );
    }
}

#[test]
fn proposal_validation_reports_changes_requested_review_state() {
    let mut proposal = proposal();
    let decision = decision(&proposal);
    let policy = build_default_evidence_acceptance_policy();
    proposal.review_state = EvidenceAppendProposalReviewState::ChangesRequested;

    let validation = policy.validate_proposal_for_candidate(
        &proposal,
        &decision,
        ClaimBoundary::Level0DesignNote,
    );

    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.blocking_reason == EvidenceAcceptanceBlockingReason::ProposalChangesRequested
    }));
}

#[test]
fn proposal_validation_reports_review_and_forbidden_text_rejection_paths() {
    let mut proposal = proposal();
    proposal
        .notes
        .push("official benchmark evidence claim".to_string());
    proposal
        .proposed_provenance_summary
        .push("formal proof claim".to_string());
    let mut decision = decision(&proposal);
    decision.reviewer_role = EvidenceReviewerRole::AutomatedPolicyCheck;
    decision.decision_kind = EvidenceReviewDecisionKind::Reject;
    decision
        .notes
        .push("proof-system soundness claim".to_string());
    let policy = build_default_evidence_acceptance_policy();

    let validation = policy.validate_proposal_for_candidate(
        &proposal,
        &decision,
        ClaimBoundary::Level0DesignNote,
    );
    let reasons = validation
        .issues
        .iter()
        .map(|issue| issue.blocking_reason)
        .collect::<Vec<_>>();

    assert!(!validation.valid);
    for expected in [
        EvidenceAcceptanceBlockingReason::InvalidReviewDecision,
        EvidenceAcceptanceBlockingReason::AutomatedReviewInsufficient,
        EvidenceAcceptanceBlockingReason::OfficialBenchmarkClaimDetected,
        EvidenceAcceptanceBlockingReason::FormalEvidenceBlocked,
        EvidenceAcceptanceBlockingReason::SoundnessClaimDetected,
    ] {
        assert!(
            reasons.contains(&expected),
            "missing expected reason {expected:?}; got {reasons:?}"
        );
    }
}

#[test]
fn policy_blocks_level2_actual_evidence() {
    let proposal = proposal();
    let decision = decision(&proposal);
    let policy = EvidenceAcceptancePolicy::phase_j_level1_local_only();

    let validation = policy.validate_proposal_for_candidate(
        &proposal,
        &decision,
        ClaimBoundary::Level2ReproducibleBenchmarkArtifact,
    );

    assert!(!validation.valid);
    assert!(validation.issues.iter().any(|issue| {
        issue.blocking_reason == EvidenceAcceptanceBlockingReason::Level2ActualEvidenceBlocked
    }));
}

#[test]
fn policy_blocks_non_approving_review_decisions_from_candidate_creation() {
    let proposal = proposal();
    let policy = build_default_evidence_acceptance_policy();

    for decision_kind in [
        EvidenceReviewDecisionKind::Reject,
        EvidenceReviewDecisionKind::RequestChanges,
    ] {
        let decision = review_evidence_append_proposal(
            &proposal,
            EvidenceReviewerRole::Maintainer,
            decision_kind,
            EvidenceReviewChecklist::phase_j_default(),
        )
        .expect("non-approving review decision should build");

        let validation = policy.validate_proposal_for_candidate(
            &proposal,
            &decision,
            ClaimBoundary::Level0DesignNote,
        );

        assert!(!validation.valid);
        assert!(validation.issues.iter().any(|issue| {
            issue.blocking_reason == EvidenceAcceptanceBlockingReason::InvalidReviewDecision
        }));
        assert!(
            create_evidence_record_candidate(&policy, &proposal, &decision).is_err(),
            "non-approving review decision must not create a candidate: {decision_kind:?}"
        );
    }
}

#[test]
fn escalation_guard_requires_explicit_level1_local_policy() {
    let blocked = guard_claim_boundary_escalation(
        ClaimBoundary::Level0DesignNote,
        ClaimBoundary::Level1LocalReplay,
        false,
    );
    assert!(blocked.is_err());

    let allowed = guard_claim_boundary_escalation(
        ClaimBoundary::Level0DesignNote,
        ClaimBoundary::Level1LocalReplay,
        true,
    )
    .expect("explicit local-only policy should allow Level1 candidate boundary");
    assert!(allowed.allowed);
}

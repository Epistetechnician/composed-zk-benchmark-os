use zkbench_core::{
    create_evidence_record_candidate, deserialize_evidence_record_candidate_json,
    review_evidence_append_proposal, serialize_evidence_record_candidate_json,
    validate_evidence_record_candidate, ClaimBoundary, EvidenceAcceptancePolicy,
    EvidenceAcceptancePolicyMode, EvidenceClass, EvidenceRecordCandidate,
    EvidenceRecordCandidateIssueKind, EvidenceRecordCandidateStatus, EvidenceReviewChecklist,
    EvidenceReviewDecisionKind, EvidenceReviewerRole,
};

fn proposal() -> zkbench_core::EvidenceAppendProposal {
    zkbench_core::deserialize_evidence_append_proposal_json(include_str!(
        "fixtures/evidence_append_proposal.json"
    ))
    .expect("proposal fixture should parse")
}

fn level1_candidate() -> EvidenceRecordCandidate {
    let proposal = proposal();
    let decision = review_evidence_append_proposal(
        &proposal,
        EvidenceReviewerRole::Maintainer,
        EvidenceReviewDecisionKind::ApproveForCandidateOnly,
        EvidenceReviewChecklist::satisfied_phase_j_default(),
    )
    .expect("manual decision should build");
    let policy = EvidenceAcceptancePolicy::phase_j_level1_local_only();

    create_evidence_record_candidate(&policy, &proposal, &decision)
        .expect("reviewed local-only candidate should build")
}

#[test]
fn level1_local_candidate_validates_but_is_not_accepted_evidence() {
    let candidate = level1_candidate();
    let validation = validate_evidence_record_candidate(&candidate);

    assert!(validation.valid, "{:?}", validation.issues);
    assert_eq!(
        candidate.proposed_evidence_class,
        EvidenceClass::LocalReplay
    );
    assert_eq!(
        candidate.proposed_claim_boundary,
        ClaimBoundary::Level1LocalReplay
    );
    assert!(!candidate.is_accepted_evidence());
    assert!(!candidate.is_official_benchmark_evidence());
    assert!(candidate.requires_future_manual_append());
}

#[test]
fn candidate_only_policy_builds_design_note_candidate() {
    let proposal = proposal();
    let decision = review_evidence_append_proposal(
        &proposal,
        EvidenceReviewerRole::Maintainer,
        EvidenceReviewDecisionKind::ApproveForCandidateOnly,
        EvidenceReviewChecklist::satisfied_phase_j_default(),
    )
    .expect("manual decision should build");
    let policy = EvidenceAcceptancePolicy::phase_j_conservative();

    let candidate = create_evidence_record_candidate(&policy, &proposal, &decision)
        .expect("candidate-only policy should build design-note candidate");

    assert_eq!(candidate.proposed_evidence_class, EvidenceClass::DesignNote);
    assert_eq!(
        candidate.proposed_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(!candidate.is_level2_or_above_candidate());
    assert!(validate_evidence_record_candidate(&candidate).valid);
}

#[test]
fn invalid_policy_and_non_candidate_modes_do_not_create_candidates() {
    let proposal = proposal();
    let decision = review_evidence_append_proposal(
        &proposal,
        EvidenceReviewerRole::Maintainer,
        EvidenceReviewDecisionKind::ApproveForCandidateOnly,
        EvidenceReviewChecklist::satisfied_phase_j_default(),
    )
    .expect("manual decision should build");

    let mut invalid_policy = EvidenceAcceptancePolicy::phase_j_level1_local_only();
    invalid_policy.id.clear();
    let invalid_policy_error =
        create_evidence_record_candidate(&invalid_policy, &proposal, &decision)
            .expect_err("invalid policy should fail before candidate creation");
    assert!(invalid_policy_error
        .to_string()
        .contains("candidate.policy"));

    let mut proposal_only_policy = EvidenceAcceptancePolicy::phase_j_conservative();
    proposal_only_policy.mode = EvidenceAcceptancePolicyMode::ProposalOnly;
    let mode_error = create_evidence_record_candidate(&proposal_only_policy, &proposal, &decision)
        .expect_err("proposal-only policy should not create candidates");
    assert!(mode_error.to_string().contains("candidate.policy"));
}

#[test]
fn rejected_and_superseded_candidates_do_not_require_future_append() {
    let mut candidate = level1_candidate();
    candidate.status = EvidenceRecordCandidateStatus::PendingFutureManualAppend;
    assert!(candidate.requires_future_manual_append());

    candidate.status = EvidenceRecordCandidateStatus::Rejected;
    assert!(!candidate.requires_future_manual_append());

    candidate.status = EvidenceRecordCandidateStatus::Superseded;
    assert!(!candidate.requires_future_manual_append());
}

#[test]
fn candidate_fixture_roundtrips() {
    let candidate = deserialize_evidence_record_candidate_json(include_str!(
        "fixtures/evidence_record_candidate_level1.json"
    ))
    .expect("candidate fixture should parse");
    let validation = validate_evidence_record_candidate(&candidate);
    assert!(validation.valid, "{:?}", validation.issues);

    let json =
        serialize_evidence_record_candidate_json(&candidate).expect("candidate should serialize");
    let parsed =
        deserialize_evidence_record_candidate_json(&json).expect("candidate should deserialize");
    assert_eq!(candidate, parsed);
}

#[test]
fn malformed_candidate_json_reports_deserialization_error() {
    let error = deserialize_evidence_record_candidate_json("{not-json")
        .expect_err("malformed candidate JSON should fail");

    assert!(error
        .to_string()
        .contains("deserialize_evidence_record_candidate_json"));
}

#[test]
fn candidate_creation_reports_acceptance_validation_failure() {
    let mut proposal = proposal();
    let decision = review_evidence_append_proposal(
        &proposal,
        EvidenceReviewerRole::Maintainer,
        EvidenceReviewDecisionKind::ApproveForCandidateOnly,
        EvidenceReviewChecklist::satisfied_phase_j_default(),
    )
    .expect("manual decision should build before proposal drift");
    proposal.proposed_artifact_refs.clear();
    proposal.validation_report_digest = None;
    let policy = EvidenceAcceptancePolicy::phase_j_level1_local_only();

    let error = create_evidence_record_candidate(&policy, &proposal, &decision)
        .expect_err("proposal without artifact metadata should fail acceptance validation");

    assert!(error
        .to_string()
        .contains("candidate.acceptance_validation"));
}

#[test]
fn candidate_rejects_level2_or_claim_flags() {
    let mut candidate = level1_candidate();
    candidate.proposed_claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    candidate.claims_official_benchmark_evidence = true;
    candidate.candidate_metrics_are_score_inputs = true;

    let validation = validate_evidence_record_candidate(&candidate);
    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path.contains("proposed_claim_boundary")));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path.contains("claim_flags")));
    assert!(candidate.is_level2_or_above_candidate());
}

#[test]
fn candidate_validation_rejects_each_claim_flag() {
    for mutate in [
        |candidate: &mut EvidenceRecordCandidate| candidate.claims_accepted_evidence = true,
        |candidate: &mut EvidenceRecordCandidate| {
            candidate.claims_official_benchmark_evidence = true;
        },
        |candidate: &mut EvidenceRecordCandidate| candidate.claims_formal_evidence = true,
        |candidate: &mut EvidenceRecordCandidate| {
            candidate.claims_proof_system_soundness = true;
        },
    ] {
        let mut candidate = level1_candidate();
        mutate(&mut candidate);

        let validation = validate_evidence_record_candidate(&candidate);

        assert!(!validation.valid);
        assert!(validation.issues.iter().any(|issue| {
            issue.kind == EvidenceRecordCandidateIssueKind::AcceptedEvidenceClaim
                && issue.path == "candidate.claim_flags"
        }));
    }
}

#[test]
fn candidate_validation_rejects_each_disallowed_evidence_class() {
    for evidence_class in [
        EvidenceClass::ReproducibleBenchmarkArtifact,
        EvidenceClass::CrossBackendReplay,
        EvidenceClass::FormalPropertyStatement,
        EvidenceClass::MachineCheckedScopedProof,
        EvidenceClass::IndependentlyReproducedEvidence,
    ] {
        let mut candidate = level1_candidate();
        candidate.proposed_evidence_class = evidence_class;

        let validation = validate_evidence_record_candidate(&candidate);

        assert!(!validation.valid);
        assert!(validation.issues.iter().any(|issue| {
            issue.kind == EvidenceRecordCandidateIssueKind::DisallowedEvidenceClass
                && issue.path == "candidate.proposed_evidence_class"
        }));
    }
}

#[test]
fn candidate_validation_reports_all_local_metadata_rejection_paths() {
    let mut candidate = level1_candidate();
    candidate.id.clear();
    candidate.source.source_proposal_id.clear();
    candidate.source.review_decision_id.clear();
    candidate.proposed_evidence_class = EvidenceClass::MachineCheckedScopedProof;
    candidate.proposed_provenance_summary.clear();
    candidate.proposed_artifact_refs.clear();
    candidate.validation_report_digest = None;
    candidate.acceptance_validation.valid = false;
    candidate
        .blocking_issues
        .push("formal proof claim".to_string());
    candidate
        .notes
        .push("official benchmark evidence claim".to_string());
    candidate
        .proposed_provenance_summary
        .push("proof-system soundness claim".to_string());

    let validation = validate_evidence_record_candidate(&candidate);
    let kinds = validation
        .issues
        .iter()
        .map(|issue| issue.kind)
        .collect::<Vec<_>>();

    assert!(!validation.valid);
    for expected in [
        EvidenceRecordCandidateIssueKind::EmptyId,
        EvidenceRecordCandidateIssueKind::DisallowedEvidenceClass,
        EvidenceRecordCandidateIssueKind::MissingArtifactDigest,
        EvidenceRecordCandidateIssueKind::AcceptanceValidationFailed,
        EvidenceRecordCandidateIssueKind::ForbiddenClaimLanguage,
    ] {
        assert!(
            kinds.contains(&expected),
            "missing expected issue kind {expected:?}; got {kinds:?}"
        );
    }
    assert!(
        validation
            .issues
            .iter()
            .filter(|issue| issue.kind == EvidenceRecordCandidateIssueKind::EmptyId)
            .count()
            >= 3
    );
}

#[test]
fn candidate_validation_reports_missing_provenance_when_empty() {
    let mut candidate = level1_candidate();
    candidate.proposed_provenance_summary.clear();

    let validation = validate_evidence_record_candidate(&candidate);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.kind == EvidenceRecordCandidateIssueKind::MissingProvenance));
}

use zkbench_core::{
    score_report_from_local_mutation_evidence, validate_score_report, ClaimBoundary,
    FormalEvidenceScore, LocalMutationEvidenceSummary, PerformanceScore, ReproducibilityScore,
    ScoreConfidence,
};

#[test]
fn local_mutation_score_report_validates_as_local_summary_only() {
    let report = score_report_from_local_mutation_evidence(LocalMutationEvidenceSummary {
        local_accepted_traces: 2,
        local_rejected_traces: 3,
        mutation_variants_generated: 4,
        outcome_changes_observed: 1,
        unsound_acceptance_candidates: 1,
    });

    let validation = validate_score_report(&report);

    assert!(validation.valid, "{:?}", validation.issues);
    assert_eq!(report.claim_boundary_max, ClaimBoundary::Level1LocalReplay);
    assert!(report.performance.is_none());
    assert!(report.formal_evidence.is_none());
}

#[test]
fn local_score_report_rejects_populated_score_axes() {
    let mut report = score_report_from_local_mutation_evidence(LocalMutationEvidenceSummary {
        local_accepted_traces: 1,
        local_rejected_traces: 1,
        mutation_variants_generated: 1,
        outcome_changes_observed: 0,
        unsound_acceptance_candidates: 0,
    });
    report.performance = Some(PerformanceScore {
        normalized_score: Some(0.99),
        confidence: ScoreConfidence::Low,
        missing_metrics: Vec::new(),
    });

    let validation = validate_score_report(&report);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path == "performance"));
}

#[test]
fn score_report_rejects_forbidden_positive_claim_text() {
    let mut report = score_report_from_local_mutation_evidence(LocalMutationEvidenceSummary {
        local_accepted_traces: 1,
        local_rejected_traces: 1,
        mutation_variants_generated: 1,
        outcome_changes_observed: 0,
        unsound_acceptance_candidates: 0,
    });
    report
        .notes
        .push("this score report is official benchmark evidence".to_string());
    report.formal_evidence = Some(FormalEvidenceScore {
        scoped_proof_score: None,
        confidence: ScoreConfidence::Low,
        notes: vec!["this score report is a machine-checked proof".to_string()],
    });

    let validation = validate_score_report(&report);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path == "notes[2]"));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path == "formal_evidence.notes[0]"));
}

#[test]
fn score_report_rejects_out_of_range_score_values() {
    let mut report = score_report_from_local_mutation_evidence(LocalMutationEvidenceSummary {
        local_accepted_traces: 1,
        local_rejected_traces: 1,
        mutation_variants_generated: 1,
        outcome_changes_observed: 0,
        unsound_acceptance_candidates: 0,
    });
    report.claim_boundary_max = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    report.performance = Some(PerformanceScore {
        normalized_score: Some(1.000_001),
        confidence: ScoreConfidence::High,
        missing_metrics: Vec::new(),
    });

    let validation = validate_score_report(&report);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path == "performance.normalized_score"));
}

#[test]
fn score_report_rejects_non_finite_score_values() {
    let mut report = score_report_from_local_mutation_evidence(LocalMutationEvidenceSummary {
        local_accepted_traces: 1,
        local_rejected_traces: 1,
        mutation_variants_generated: 1,
        outcome_changes_observed: 0,
        unsound_acceptance_candidates: 0,
    });
    report.claim_boundary_max = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    report.reproducibility = Some(ReproducibilityScore {
        reproducibility_score: Some(f64::INFINITY),
        confidence: ScoreConfidence::High,
        notes: Vec::new(),
    });

    let validation = validate_score_report(&report);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.path == "reproducibility.reproducibility_score"));
}

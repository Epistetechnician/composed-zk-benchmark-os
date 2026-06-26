use zkbench_core::{
    score_report_from_evidence, score_report_from_local_mutation_evidence, validate_score_report,
    AdapterPortabilityScore, ClaimBoundary, CorrectnessScore, EvidenceClass, EvidenceRecord,
    FormalEvidenceScore, LocalMutationEvidenceSummary, PerformanceScore, ProvenanceRecord,
    RecursionStressScore, ReproducibilityScore, RiskPenalty, ScoreConfidence, ScoreReport,
    SoundnessFailureDetectionScore,
};

fn evidence(boundary: ClaimBoundary) -> EvidenceRecord {
    EvidenceRecord {
        evidence_class: match boundary {
            ClaimBoundary::Level0DesignNote => EvidenceClass::DesignNote,
            ClaimBoundary::Level1LocalReplay => EvidenceClass::LocalReplay,
            ClaimBoundary::Level2ReproducibleBenchmarkArtifact => {
                EvidenceClass::ReproducibleBenchmarkArtifact
            }
            ClaimBoundary::Level3CrossBackendReplay => EvidenceClass::CrossBackendReplay,
            ClaimBoundary::Level4FormalPropertyStatement => EvidenceClass::FormalPropertyStatement,
            ClaimBoundary::Level5MachineCheckedScopedProof => {
                EvidenceClass::MachineCheckedScopedProof
            }
            ClaimBoundary::Level6IndependentlyReproducedEvidence => {
                EvidenceClass::IndependentlyReproducedEvidence
            }
        },
        claim_boundary: boundary,
        provenance: ProvenanceRecord {
            source: format!("phase_187::{boundary}"),
            captured_at: None,
            command: None,
            notes: vec!["local scoring coverage fixture".to_string()],
        },
        artifact_digest: None,
        notes: vec!["fixture evidence record only".to_string()],
        backend_target: None,
    }
}

fn local_summary() -> LocalMutationEvidenceSummary {
    LocalMutationEvidenceSummary {
        local_accepted_traces: 1,
        local_rejected_traces: 2,
        mutation_variants_generated: 3,
        outcome_changes_observed: 1,
        unsound_acceptance_candidates: 0,
    }
}

fn all_axes_report(boundary: ClaimBoundary) -> ScoreReport {
    let mut report = score_report_from_local_mutation_evidence(local_summary());
    report.claim_boundary_max = boundary;
    report.confidence = ScoreConfidence::High;
    report.performance = Some(PerformanceScore {
        normalized_score: Some(0.25),
        confidence: ScoreConfidence::High,
        missing_metrics: vec!["future prover timing".to_string()],
    });
    report.correctness = Some(CorrectnessScore {
        alignment_score: Some(0.50),
        confidence: ScoreConfidence::High,
        notes: vec!["bounded correctness metadata only".to_string()],
    });
    report.soundness_failure_detection = Some(SoundnessFailureDetectionScore {
        negative_test_coverage: Some(0.75),
        confidence: ScoreConfidence::High,
        notes: vec!["bounded negative-test metadata only".to_string()],
    });
    report.recursion_stress = Some(RecursionStressScore {
        recursion_depth_score: Some(1.0),
        confidence: ScoreConfidence::High,
        notes: vec!["bounded recursion metadata only".to_string()],
    });
    report.formal_evidence = Some(FormalEvidenceScore {
        scoped_proof_score: Some(0.0),
        confidence: ScoreConfidence::High,
        notes: vec!["bounded formal metadata only".to_string()],
    });
    report.reproducibility = Some(ReproducibilityScore {
        reproducibility_score: Some(0.40),
        confidence: ScoreConfidence::High,
        notes: vec!["bounded reproducibility metadata only".to_string()],
    });
    report.adapter_portability = Some(AdapterPortabilityScore {
        portability_score: Some(0.60),
        confidence: ScoreConfidence::High,
        notes: vec!["bounded adapter metadata only".to_string()],
    });
    report.risk_penalties = vec![
        RiskPenalty::CapabilityGap {
            capability: "future backend timing".to_string(),
        },
        RiskPenalty::Inconclusive {
            reason: "future external replication absent".to_string(),
        },
    ];
    report.notes = vec!["bounded score report fixture".to_string()];
    report
}

#[test]
fn score_report_from_evidence_maps_higher_boundaries_to_confidence_levels() {
    let high = score_report_from_evidence(&[
        evidence(ClaimBoundary::Level1LocalReplay),
        evidence(ClaimBoundary::Level2ReproducibleBenchmarkArtifact),
    ]);
    assert_eq!(
        high.claim_boundary_max,
        ClaimBoundary::Level2ReproducibleBenchmarkArtifact
    );
    assert_eq!(high.confidence, ScoreConfidence::High);

    let cross_backend =
        score_report_from_evidence(&[evidence(ClaimBoundary::Level3CrossBackendReplay)]);
    assert_eq!(cross_backend.confidence, ScoreConfidence::High);

    let formal_statement =
        score_report_from_evidence(&[evidence(ClaimBoundary::Level4FormalPropertyStatement)]);
    assert_eq!(formal_statement.confidence, ScoreConfidence::ScopedProof);

    let machine_checked =
        score_report_from_evidence(&[evidence(ClaimBoundary::Level5MachineCheckedScopedProof)]);
    assert_eq!(machine_checked.confidence, ScoreConfidence::ScopedProof);

    let independent = score_report_from_evidence(&[evidence(
        ClaimBoundary::Level6IndependentlyReproducedEvidence,
    )]);
    assert_eq!(independent.confidence, ScoreConfidence::Independent);
}

#[test]
fn higher_boundary_score_axes_validate_when_values_and_text_are_bounded() {
    let report = all_axes_report(ClaimBoundary::Level2ReproducibleBenchmarkArtifact);

    let validation = validate_score_report(&report);

    assert!(validation.valid, "{:?}", validation.issues);
}

#[test]
fn local_score_report_rejects_every_populated_axis_path() {
    let report = all_axes_report(ClaimBoundary::Level1LocalReplay);

    let validation = validate_score_report(&report);

    assert!(!validation.valid);
    for path in [
        "performance",
        "correctness",
        "soundness_failure_detection",
        "recursion_stress",
        "formal_evidence",
        "reproducibility",
        "adapter_portability",
    ] {
        assert!(
            validation.issues.iter().any(|issue| issue.path == path),
            "missing local axis issue for {path}: {:?}",
            validation.issues
        );
    }
}

#[test]
fn score_report_reports_all_axis_value_and_text_rejections() {
    let mut report = all_axes_report(ClaimBoundary::Level2ReproducibleBenchmarkArtifact);
    report.risk_penalties.push(RiskPenalty::CapabilityGap {
        capability: "official benchmark evidence".to_string(),
    });
    report.correctness.as_mut().unwrap().alignment_score = Some(-0.01);
    report
        .correctness
        .as_mut()
        .unwrap()
        .notes
        .push("formal proof".to_string());
    report
        .soundness_failure_detection
        .as_mut()
        .unwrap()
        .negative_test_coverage = Some(1.01);
    report
        .soundness_failure_detection
        .as_mut()
        .unwrap()
        .notes
        .push("sota result".to_string());
    report
        .recursion_stress
        .as_mut()
        .unwrap()
        .recursion_depth_score = Some(f64::NAN);
    report
        .recursion_stress
        .as_mut()
        .unwrap()
        .notes
        .push("performance evidence".to_string());
    report.formal_evidence.as_mut().unwrap().scoped_proof_score = Some(2.0);
    report
        .formal_evidence
        .as_mut()
        .unwrap()
        .notes
        .push("machine-checked proof".to_string());
    report
        .reproducibility
        .as_mut()
        .unwrap()
        .reproducibility_score = Some(-1.0);
    report
        .reproducibility
        .as_mut()
        .unwrap()
        .notes
        .push("official benchmark result".to_string());
    report
        .adapter_portability
        .as_mut()
        .unwrap()
        .portability_score = Some(f64::INFINITY);
    report
        .adapter_portability
        .as_mut()
        .unwrap()
        .notes
        .push("proof-system soundness".to_string());

    let validation = validate_score_report(&report);

    assert!(!validation.valid);
    for path in [
        "risk_penalties[2].capability",
        "correctness.alignment_score",
        "correctness.notes[1]",
        "soundness_failure_detection.negative_test_coverage",
        "soundness_failure_detection.notes[1]",
        "recursion_stress.recursion_depth_score",
        "recursion_stress.notes[1]",
        "formal_evidence.scoped_proof_score",
        "formal_evidence.notes[1]",
        "reproducibility.reproducibility_score",
        "reproducibility.notes[1]",
        "adapter_portability.portability_score",
        "adapter_portability.notes[1]",
    ] {
        assert!(
            validation.issues.iter().any(|issue| issue.path == path),
            "missing validation issue for {path}: {:?}",
            validation.issues
        );
    }
}

use zkbench_core::{
    import_synthetic_result_candidate_json, score_report_from_evidence,
    serialize_synthetic_result_import_bundle_json, ClaimBoundary, ResultCandidateArtifactResolver,
};

fn resolver() -> ResultCandidateArtifactResolver {
    ResultCandidateArtifactResolver::from_in_memory_bytes(vec![(
        "artifacts/synthetic_metric_source.json".to_string(),
        b"synthetic metric source v1\n".to_vec(),
    )])
}

#[test]
fn valid_synthetic_candidate_imports_to_normalized_draft() {
    let json = include_str!("fixtures/synthetic_result_candidate_valid.json");
    let bundle = import_synthetic_result_candidate_json(json, &resolver())
        .expect("valid synthetic candidate should import");

    assert!(bundle.validation.valid, "{:?}", bundle.validation.issues);
    assert_eq!(bundle.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(bundle.report.candidates_imported, 1);
    assert_eq!(bundle.report.candidates_normalized, 1);
    assert_eq!(bundle.report.candidates_quarantined, 0);
    assert!(bundle.normalized_draft.is_some());
    assert!(bundle.quarantine_manifest.is_none());

    let draft = bundle
        .normalized_draft
        .as_ref()
        .expect("normalized draft should be present");
    assert_eq!(draft.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(draft.metrics.len(), 1);
    assert!(draft.metrics[0].candidate_only);
    assert!(draft.metrics[0].pending_review);
    assert_eq!(draft.artifact_refs.len(), 1);
    assert!(draft.artifact_refs[0].verified_by_importer);

    let serialized =
        serialize_synthetic_result_import_bundle_json(&bundle).expect("bundle serializes");
    assert!(serialized.contains("synthetic_import_bundle_synthetic_candidate_valid"));
}

#[test]
fn invalid_synthetic_candidate_imports_to_quarantine_manifest() {
    let json = include_str!("fixtures/synthetic_result_candidate_bad_digest.json");
    let bundle = import_synthetic_result_candidate_json(json, &resolver())
        .expect("bad synthetic candidate should still parse into a quarantine bundle");

    assert!(!bundle.validation.valid);
    assert_eq!(bundle.report.candidates_normalized, 0);
    assert_eq!(bundle.report.candidates_quarantined, 1);
    assert!(bundle.normalized_draft.is_none());
    assert!(bundle.quarantine_manifest.is_some());
    assert_eq!(
        bundle
            .quarantine_manifest
            .as_ref()
            .expect("quarantine manifest")
            .entries[0]
            .claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
}

#[test]
fn synthetic_metric_candidates_do_not_create_score_values() {
    let report = score_report_from_evidence(&[]);

    assert!(report.performance.is_none());
    assert!(report.formal_evidence.is_none());
}

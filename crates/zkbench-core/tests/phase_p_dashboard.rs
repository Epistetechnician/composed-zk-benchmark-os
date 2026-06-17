use zkbench_core::{
    build_dashboard_model_from_score_report, render_dashboard_markdown, score_report_from_evidence,
    validate_dashboard_model, ClaimBoundary, DashboardPanelKind, PerformanceScore, ScoreConfidence,
};

#[test]
fn dashboard_model_builds_from_empty_evidence_and_validates() {
    let report = score_report_from_evidence(&[]);
    let model = build_dashboard_model_from_score_report("empty_evidence_dashboard", &report);

    validate_dashboard_model(&model).expect("dashboard model should validate");
    assert_eq!(model.claim_boundary_max, ClaimBoundary::Level0DesignNote);
    assert!(!model.contains_zk_backend_performance_claims());

    let axis_panel = model
        .panels
        .iter()
        .find(|panel| panel.kind == DashboardPanelKind::AxisScores)
        .expect("axis panel should exist");
    assert_eq!(axis_panel.axis_rows.len(), 7);
    assert!(axis_panel.axis_rows.iter().all(|row| row.no_evidence));
    assert!(model
        .panels
        .iter()
        .any(|panel| panel.kind == DashboardPanelKind::ClaimBoundary));
}

#[test]
fn dashboard_renders_markdown_with_claim_boundaries() {
    let report = score_report_from_evidence(&[]);
    let model = build_dashboard_model_from_score_report("render_test_dashboard", &report);
    let markdown = render_dashboard_markdown(&model);

    assert!(markdown.contains("# Dashboard: render_test_dashboard"));
    assert!(markdown.contains("Maximum claim boundary: Level0DesignNote"));
    assert!(markdown.contains("| Axis | Score | Confidence | Evidence |"));
    assert!(markdown.contains("| performance | - | Low | none |"));
    assert!(markdown.contains("No ZK backend performance claims are displayed."));
}

#[test]
fn dashboard_validation_rejects_missing_claim_boundary_panel() {
    let report = score_report_from_evidence(&[]);
    let mut model = build_dashboard_model_from_score_report("invalid_dashboard", &report);
    model
        .panels
        .retain(|panel| panel.kind != DashboardPanelKind::ClaimBoundary);

    let error = validate_dashboard_model(&model).expect_err("missing claim panel should fail");
    assert!(error.to_string().contains("claim boundary panel"));
}

#[test]
fn dashboard_validation_rejects_panel_boundary_above_model_max() {
    let report = score_report_from_evidence(&[]);
    let mut model = build_dashboard_model_from_score_report("boundary_cap_dashboard", &report);
    model.panels[0].claim_boundary = ClaimBoundary::Level1LocalReplay;

    let error = validate_dashboard_model(&model).expect_err("panel boundary above max should fail");

    assert!(error.to_string().contains("exceeds the dashboard maximum"));
}

#[test]
fn dashboard_validation_rejects_local_populated_score_axes() {
    let mut report = score_report_from_evidence(&[]);
    report.claim_boundary_max = ClaimBoundary::Level1LocalReplay;
    report.performance = Some(PerformanceScore {
        normalized_score: Some(0.5),
        confidence: ScoreConfidence::Low,
        missing_metrics: Vec::new(),
    });
    let model = build_dashboard_model_from_score_report("local_score_axis_dashboard", &report);

    let error =
        validate_dashboard_model(&model).expect_err("local populated score axis should fail");

    assert!(error.to_string().contains("score axes"));
}

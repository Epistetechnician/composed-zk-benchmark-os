use zkbench_core::{
    build_dashboard_model_from_pack_readiness, build_dashboard_model_from_score_report,
    build_local_replay_manifest_for_instance, generate_instance, render_dashboard_markdown,
    run_local_replay, score_report_from_evidence, validate_dashboard_model,
    write_pack_readiness_outputs_for_pack, BenchmarkPackWriter, ClaimBoundary, DashboardPanelKind,
    EvidenceLedger, GeneratorConfig, InstanceParams, PerformanceScore, ScoreConfidence,
};

fn write_sample_pack(pack_id: &str) -> tempfile::TempDir {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(127),
        InstanceParams::default(),
    )
    .expect("baseline instance should generate");
    let replay_manifest =
        build_local_replay_manifest_for_instance(&instance).expect("replay manifest should build");
    let replay_result = run_local_replay(&replay_manifest).expect("local replay should run");

    let mut ledger = EvidenceLedger::new();
    ledger
        .append_replay_result(&replay_result)
        .expect("local replay evidence should append");

    let dir = tempfile::tempdir().expect("tempdir should be available for pack write");
    BenchmarkPackWriter::new(pack_id)
        .with_generated_instance(instance)
        .with_replay_manifest(replay_manifest)
        .with_replay_result(replay_result)
        .with_evidence_ledger(ledger)
        .write_to(dir.path())
        .expect("sample pack should write");
    dir
}

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
fn dashboard_model_builds_from_pack_readiness_outputs_and_validates() {
    let dir = write_sample_pack("phase_p_readiness_dashboard_pack");
    let output = write_pack_readiness_outputs_for_pack(dir.path())
        .expect("readiness outputs should write next to pack");

    let model = build_dashboard_model_from_pack_readiness(
        "pack_readiness_dashboard",
        &output.report,
        &output.readiness_validation,
    );

    validate_dashboard_model(&model).expect("pack-readiness dashboard should validate");
    assert_eq!(model.claim_boundary_max, ClaimBoundary::Level0DesignNote);
    assert!(!model.contains_zk_backend_performance_claims());
    assert!(model
        .panels
        .iter()
        .any(|panel| panel.kind == DashboardPanelKind::PackReadiness));
    assert!(model
        .panels
        .iter()
        .all(|panel| panel.claim_boundary == ClaimBoundary::Level0DesignNote));
}

#[test]
fn dashboard_renders_pack_readiness_without_claim_elevation() {
    let dir = write_sample_pack("phase_p_readiness_render_pack");
    let output = write_pack_readiness_outputs_for_pack(dir.path())
        .expect("readiness outputs should write next to pack");
    let model = build_dashboard_model_from_pack_readiness(
        "pack_readiness_render_dashboard",
        &output.report,
        &output.readiness_validation,
    );
    let markdown = render_dashboard_markdown(&model);

    assert!(markdown.contains("# Dashboard: pack_readiness_render_dashboard"));
    assert!(markdown.contains("## Pack Readiness"));
    assert!(markdown.contains("source pack: phase_p_readiness_render_pack"));
    assert!(markdown.contains("readiness validation: true"));
    assert!(markdown.contains("pack-readiness is not Level2 evidence"));
    assert!(markdown.contains("Claim boundary: Level0DesignNote"));
    assert!(!markdown.contains("creates Level2 evidence: true"));
    assert!(!markdown.contains("official benchmark evidence: true"));
    assert!(!markdown.contains("ZK backend performance claims: true"));
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
fn dashboard_validation_rejects_pack_readiness_boundary_above_level0() {
    let dir = write_sample_pack("phase_p_readiness_boundary_pack");
    let output = write_pack_readiness_outputs_for_pack(dir.path())
        .expect("readiness outputs should write next to pack");
    let mut model = build_dashboard_model_from_pack_readiness(
        "pack_readiness_boundary_dashboard",
        &output.report,
        &output.readiness_validation,
    );
    model.claim_boundary_max = ClaimBoundary::Level1LocalReplay;
    model
        .panels
        .iter_mut()
        .find(|panel| panel.kind == DashboardPanelKind::PackReadiness)
        .expect("pack-readiness panel should exist")
        .claim_boundary = ClaimBoundary::Level1LocalReplay;

    let error =
        validate_dashboard_model(&model).expect_err("pack readiness boundary drift should fail");

    assert!(error
        .to_string()
        .contains("pack-readiness panels must remain Level0DesignNote"));
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

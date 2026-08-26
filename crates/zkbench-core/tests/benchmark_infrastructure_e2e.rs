//! Local end-to-end composition coverage for the benchmark reporting chain.
//!
//! State slice: benchmark-os-local-reporting-chain-e2e-v1.

use tempfile::tempdir;
use zkbench_core::{
    build_local_audit_index_cross_bundle_view, build_local_audit_index_ergonomics_view,
    build_local_audit_index_manifest_from_report_bundles, build_local_replay_manifest_for_instance,
    build_report_bundle_manifest_from_reports, build_report_bundle_rendered_markdown_payloads,
    generate_instance, read_local_audit_index_cross_bundle_outputs,
    read_local_audit_index_ergonomics_outputs, read_local_audit_index_outputs,
    read_pack_readiness_report, read_pack_readiness_validation, read_report_bundle_outputs,
    run_local_replay, validate_local_audit_index_manifest, validate_report_bundle_manifest,
    write_local_audit_index_cross_bundle_outputs, write_local_audit_index_ergonomics_outputs,
    write_local_audit_index_outputs, write_pack_readiness_outputs_for_pack,
    write_report_bundle_outputs, BenchmarkPackReader, BenchmarkPackWriter, ClaimBoundary,
    EvidenceLedger, GeneratorConfig, InstanceParams, LocalAuditIndexCrossBundleGroupKey,
    LocalAuditIndexCrossBundleInput, LocalAuditIndexCrossBundleRequest,
    LocalAuditIndexCrossBundleSortKey, LocalAuditIndexErgonomicsRequest,
    ReportBundlePackReadinessInput,
};

#[test]
fn local_reporting_chain_round_trips_without_claim_escalation() {
    let workspace = tempdir().expect("temporary workspace should create");
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(907),
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

    let pack_root = workspace.path().join("pack");
    let pack_manifest = BenchmarkPackWriter::new("phase-e2e-local-reporting-chain")
        .with_generated_instance(instance)
        .with_replay_manifest(replay_manifest)
        .with_replay_result(replay_result)
        .with_evidence_ledger(ledger)
        .write_to(&pack_root)
        .expect("local benchmark pack should write");
    assert_eq!(
        pack_manifest.claim_boundary,
        ClaimBoundary::Level1LocalReplay
    );

    let pack_reader = BenchmarkPackReader::read(&pack_root).expect("pack should read");
    let pack_validation = pack_reader.validate();
    assert!(
        pack_validation.valid,
        "pack validation should pass: {:?}",
        pack_validation.errors
    );
    let score_report = pack_reader
        .load_score_report()
        .expect("score report read should succeed")
        .expect("pack should contain a score report");

    let readiness_output = write_pack_readiness_outputs_for_pack(&pack_root)
        .expect("pack readiness outputs should write");
    assert_eq!(
        readiness_output.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(readiness_output.readiness_validation.valid);
    assert_eq!(
        read_pack_readiness_report(&pack_root).expect("readiness report should read"),
        readiness_output.report
    );
    assert_eq!(
        read_pack_readiness_validation(&pack_root).expect("readiness validation should read"),
        readiness_output.readiness_validation
    );

    let readiness_input = ReportBundlePackReadinessInput {
        report: readiness_output.report.clone(),
        validation: readiness_output.readiness_validation.clone(),
    };
    let report_manifest = build_report_bundle_manifest_from_reports(
        "phase-e2e-report-bundle",
        &[score_report.clone()],
        &[readiness_input.clone()],
    )
    .expect("report-bundle manifest should build");
    assert_eq!(
        report_manifest.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    let rendered_payloads = build_report_bundle_rendered_markdown_payloads(
        &report_manifest,
        &[score_report],
        &[readiness_input],
    )
    .expect("report-bundle rendered payloads should build");

    let report_root = workspace.path().join("report-bundle");
    let report_output =
        write_report_bundle_outputs(&report_root, &report_manifest, &rendered_payloads, false)
            .expect("report bundle should write");
    assert_eq!(
        report_output.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    let report_readback =
        read_report_bundle_outputs(&report_root).expect("report bundle should read back");
    assert_eq!(report_readback.manifest, report_manifest);
    assert_eq!(
        report_readback.rendered_reports,
        report_output.rendered_reports
    );

    let audit_manifest = build_local_audit_index_manifest_from_report_bundles(
        "phase-e2e-audit-index",
        &pack_manifest.id,
        &[report_readback.manifest.clone()],
    )
    .expect("audit-index manifest should build");
    assert_eq!(
        audit_manifest.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    let audit_root = workspace.path().join("audit-index");
    let audit_output = write_local_audit_index_outputs(&audit_root, &audit_manifest, false)
        .expect("audit-index should write");
    assert_eq!(
        audit_output.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    let audit_readback =
        read_local_audit_index_outputs(&audit_root).expect("audit-index should read back");
    assert_eq!(audit_readback.manifest, audit_manifest);
    assert!(audit_readback
        .manifest
        .inputs
        .iter()
        .all(|input| input.claim_boundary <= ClaimBoundary::Level1LocalReplay));
    assert!(!audit_readback.manifest.official_benchmark_evidence);
    assert!(!audit_readback.manifest.creates_level2_evidence);
    assert!(!audit_readback.manifest.zk_backend_performance_claims);
    assert!(!audit_readback.manifest.mutates_accepted_evidence_ledger);
    // State slice: benchmark-os-local-reporting-chain-audit-views-e2e-v1.
    let ergonomics_request = LocalAuditIndexErgonomicsRequest::default();
    let ergonomics_view =
        build_local_audit_index_ergonomics_view(&audit_readback.manifest, &ergonomics_request)
            .expect("ergonomics view should build");
    let ergonomics_root = workspace.path().join("audit-index-ergonomics");
    let ergonomics_output = write_local_audit_index_ergonomics_outputs(
        &ergonomics_root,
        &audit_readback.manifest,
        &ergonomics_request,
        &ergonomics_view,
        false,
        &[audit_root.as_path()],
    )
    .expect("ergonomics output should write");
    let ergonomics_readback = read_local_audit_index_ergonomics_outputs(
        &ergonomics_root,
        &audit_readback.manifest,
        &ergonomics_request,
        &[audit_root.as_path()],
    )
    .expect("ergonomics output should read");
    assert_eq!(ergonomics_readback.view, ergonomics_view);
    assert_eq!(
        ergonomics_readback.view_digest,
        ergonomics_output.view_digest
    );
    assert_eq!(
        ergonomics_readback.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );

    let second_manifest = zkbench_core::LocalAuditIndexManifest {
        index_id: "phase-e2e-audit-index-second".to_string(),
        indexed_pack_id: "phase-e2e-local-reporting-chain-second".to_string(),
        ..audit_readback.manifest.clone()
    };
    let cross_request = LocalAuditIndexCrossBundleRequest {
        inputs: vec![
            LocalAuditIndexCrossBundleInput {
                source_id: "source-a".to_string(),
                manifest: audit_readback.manifest.clone(),
            },
            LocalAuditIndexCrossBundleInput {
                source_id: "source-b".to_string(),
                manifest: second_manifest,
            },
        ],
        group_by: LocalAuditIndexCrossBundleGroupKey::IndexedPackId,
        sort_by: LocalAuditIndexCrossBundleSortKey::SourceId,
    };
    let cross_view = build_local_audit_index_cross_bundle_view(&cross_request)
        .expect("cross-bundle view should build");
    let cross_root = workspace.path().join("cross-bundle-audit-index");
    let cross_output = write_local_audit_index_cross_bundle_outputs(
        &cross_root,
        &cross_request,
        &cross_view,
        false,
        &[audit_root.as_path(), ergonomics_root.as_path()],
    )
    .expect("cross-bundle output should write");
    let cross_readback = read_local_audit_index_cross_bundle_outputs(
        &cross_root,
        &cross_request,
        &[audit_root.as_path(), ergonomics_root.as_path()],
    )
    .expect("cross-bundle output should read");
    assert_eq!(cross_readback.view, cross_view);
    assert_eq!(cross_readback.view_digest, cross_output.view_digest);
    assert_eq!(
        cross_readback.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert_eq!(cross_readback.view.sources.len(), 2);
    assert_eq!(cross_readback.view.sources[0].source_id, "source-a");
    assert_eq!(cross_readback.view.sources[1].source_id, "source-b");
    assert!(cross_readback
        .view
        .sources
        .iter()
        .all(|source| source.max_input_claim_boundary <= ClaimBoundary::Level1LocalReplay));
}

#[test]
fn local_reporting_chain_preserves_failed_readiness_without_promotion() {
    // State slice: benchmark-os-local-reporting-chain-failed-readiness-e2e-v1.
    let workspace = tempdir().expect("temporary workspace should create");
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(908),
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

    let pack_root = workspace.path().join("pack");
    let pack_manifest = BenchmarkPackWriter::new("phase-e2e-local-reporting-chain-failure")
        .with_generated_instance(instance)
        .with_replay_manifest(replay_manifest)
        .with_replay_result(replay_result)
        .with_evidence_ledger(ledger)
        .write_to(&pack_root)
        .expect("local benchmark pack should write");
    assert_eq!(
        pack_manifest.claim_boundary,
        ClaimBoundary::Level1LocalReplay
    );

    std::fs::write(pack_root.join("reports/score_report.json"), b"{}")
        .expect("tampered score report should write");
    let pack_reader = BenchmarkPackReader::read(&pack_root).expect("pack should read");
    let pack_validation = pack_reader.validate();
    assert!(!pack_validation.valid);

    let readiness_output = write_pack_readiness_outputs_for_pack(&pack_root)
        .expect("failed pack readiness outputs should still write");
    assert!(!readiness_output.readiness_validation.valid);
    assert!(readiness_output
        .report
        .checks
        .iter()
        .any(|check| !check.passed));
    assert_eq!(
        readiness_output.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(!readiness_output.report.external_replay_authorized);
    assert!(!readiness_output.report.creates_level2_evidence);
    assert!(!readiness_output.report.official_benchmark_evidence);
    assert!(!readiness_output.report.zk_backend_performance_claims);
    assert_eq!(
        read_pack_readiness_report(&pack_root).expect("readiness report should read"),
        readiness_output.report
    );
    assert_eq!(
        read_pack_readiness_validation(&pack_root).expect("readiness validation should read"),
        readiness_output.readiness_validation
    );

    let readiness_input = ReportBundlePackReadinessInput {
        report: readiness_output.report.clone(),
        validation: readiness_output.readiness_validation.clone(),
    };
    let report_manifest = build_report_bundle_manifest_from_reports(
        "phase-e2e-report-bundle-failure",
        &[],
        &[readiness_input.clone()],
    )
    .expect("failed report-bundle manifest should build");
    assert_eq!(
        report_manifest.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(!report_manifest.external_replay_authorized);
    assert!(!report_manifest.creates_level2_evidence);
    assert!(!report_manifest.official_benchmark_evidence);
    assert!(!report_manifest.zk_backend_performance_claims);
    assert!(validate_report_bundle_manifest(&report_manifest).valid);
    let rendered_payloads =
        build_report_bundle_rendered_markdown_payloads(&report_manifest, &[], &[readiness_input])
            .expect("failed report-bundle rendered payloads should build");

    let report_root = workspace.path().join("report-bundle");
    let report_output =
        write_report_bundle_outputs(&report_root, &report_manifest, &rendered_payloads, false)
            .expect("failed report bundle should write");
    let report_readback =
        read_report_bundle_outputs(&report_root).expect("failed report bundle should read back");
    assert_eq!(report_readback.manifest, report_manifest);
    assert_eq!(
        report_readback.rendered_reports,
        report_output.rendered_reports
    );
    assert!(report_readback
        .manifest
        .inputs
        .iter()
        .any(|input| input.failed_readiness));
    assert!(report_readback
        .manifest
        .rendered_reports
        .iter()
        .filter(|rendered| rendered.source_input_ids.iter().any(|input_id| {
            report_readback
                .manifest
                .inputs
                .iter()
                .any(|input| input.input_id == *input_id && input.failed_readiness)
        }))
        .all(|rendered| rendered.failed_readiness_visible));
    assert!(!report_readback.manifest.external_replay_authorized);
    assert!(!report_readback.manifest.creates_level2_evidence);
    assert!(!report_readback.manifest.official_benchmark_evidence);
    assert!(!report_readback.manifest.zk_backend_performance_claims);

    let audit_manifest = build_local_audit_index_manifest_from_report_bundles(
        "phase-e2e-audit-index-failure",
        &pack_manifest.id,
        &[report_readback.manifest.clone()],
    )
    .expect("failed audit-index manifest should build");
    assert!(validate_local_audit_index_manifest(&audit_manifest).valid);
    assert!(audit_manifest.failed_readiness_visible);
    assert!(audit_manifest
        .inputs
        .iter()
        .any(|input| input.failed_readiness));
    assert_eq!(
        audit_manifest.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(!audit_manifest.external_replay_authorized);
    assert!(!audit_manifest.creates_level2_evidence);
    assert!(!audit_manifest.official_benchmark_evidence);
    assert!(!audit_manifest.zk_backend_performance_claims);

    let audit_root = workspace.path().join("audit-index");
    let audit_output = write_local_audit_index_outputs(&audit_root, &audit_manifest, false)
        .expect("failed audit-index should write");
    let audit_readback =
        read_local_audit_index_outputs(&audit_root).expect("failed audit-index should read back");
    assert_eq!(audit_readback.manifest, audit_manifest);
    assert!(audit_readback.validation.valid);
    assert_eq!(
        audit_readback.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(audit_readback.manifest.failed_readiness_visible);
    assert!(audit_readback
        .manifest
        .inputs
        .iter()
        .any(|input| input.failed_readiness));
    assert_eq!(audit_output.manifest, audit_readback.manifest);
    assert!(!audit_readback.manifest.external_replay_authorized);
    assert!(!audit_readback.manifest.creates_level2_evidence);
    assert!(!audit_readback.manifest.official_benchmark_evidence);
    assert!(!audit_readback.manifest.zk_backend_performance_claims);
}

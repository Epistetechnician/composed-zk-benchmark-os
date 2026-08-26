//! Local end-to-end composition coverage for the benchmark reporting chain.
//!
//! State slice: benchmark-os-local-reporting-chain-e2e-v1.

use tempfile::tempdir;
use zkbench_core::{
    build_local_audit_index_manifest_from_report_bundles, build_local_replay_manifest_for_instance,
    build_report_bundle_manifest_from_reports, build_report_bundle_rendered_markdown_payloads,
    generate_instance, read_local_audit_index_outputs, read_pack_readiness_report,
    read_pack_readiness_validation, read_report_bundle_outputs, run_local_replay,
    write_local_audit_index_outputs, write_pack_readiness_outputs_for_pack,
    write_report_bundle_outputs, BenchmarkPackReader, BenchmarkPackWriter, ClaimBoundary,
    EvidenceLedger, GeneratorConfig, InstanceParams, ReportBundlePackReadinessInput,
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
}

use std::fs;

use zkbench_core::{
    build_local_audit_index_ergonomics_view, compute_artifact_digest_bytes,
    read_local_audit_index_ergonomics_outputs, required_local_audit_index_ergonomics_limitations,
    serialize_local_audit_index_ergonomics_view_json,
    validate_local_audit_index_ergonomics_request, write_local_audit_index_ergonomics_outputs,
    ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole, ClaimBoundary,
    LocalAuditIndexErgonomicsFilter, LocalAuditIndexErgonomicsFilterField,
    LocalAuditIndexErgonomicsGroupKey, LocalAuditIndexErgonomicsIssueKind,
    LocalAuditIndexErgonomicsRequest, LocalAuditIndexErgonomicsSortKey, LocalAuditIndexInputKind,
    LocalAuditIndexInputRef, LocalAuditIndexManifest, LocalAuditIndexVersion,
    AUDIT_INDEX_ERGONOMICS_MARKDOWN_DIGEST_PATH, AUDIT_INDEX_ERGONOMICS_MARKDOWN_PATH,
    AUDIT_INDEX_ERGONOMICS_VIEW_DIGEST_PATH, AUDIT_INDEX_ERGONOMICS_VIEW_PATH,
};

fn digest(label: &str, kind: ArtifactKind, role: ArtifactRole) -> ArtifactDigest {
    let nibble = label
        .as_bytes()
        .iter()
        .fold(0_u8, |accumulator, byte| accumulator.wrapping_add(*byte))
        % 16;
    let hex_char = char::from_digit(nibble.into(), 16).expect("hex nibble");
    ArtifactDigest {
        algorithm: ArtifactDigestAlgorithm::Sha256,
        hex_digest: hex_char.to_string().repeat(64),
        byte_len: label.len().max(1),
        kind: Some(kind),
        role: Some(role),
    }
}

fn input(
    input_id: &str,
    artifact_uri: &str,
    kind: LocalAuditIndexInputKind,
    failed_readiness: bool,
    local_only_warnings_visible: bool,
) -> LocalAuditIndexInputRef {
    LocalAuditIndexInputRef {
        input_id: input_id.to_string(),
        artifact_uri: artifact_uri.to_string(),
        kind,
        digest: digest(input_id, ArtifactKind::Other, ArtifactRole::Report),
        claim_boundary: ClaimBoundary::Level0DesignNote,
        failed_readiness,
        local_only_warnings_visible,
        source_input_ids: Vec::new(),
        notes: vec!["local fixture metadata".to_string()],
    }
}

fn valid_manifest() -> LocalAuditIndexManifest {
    LocalAuditIndexManifest {
        index_id: "phase_s_audit_index".to_string(),
        version: LocalAuditIndexVersion::default(),
        indexed_pack_id: "sample_pack".to_string(),
        report_bundle_ids: vec!["bundle_0".to_string()],
        inputs: vec![
            input(
                "pack_manifest",
                "pack/pack.json",
                LocalAuditIndexInputKind::BenchmarkPackManifest,
                false,
                true,
            ),
            input(
                "readiness_report",
                "readiness/pack-readiness-report.json",
                LocalAuditIndexInputKind::PackReadinessReport,
                true,
                true,
            ),
            input(
                "bundle_manifest",
                "report-bundles/0/report-bundle-manifest.json",
                LocalAuditIndexInputKind::ReportBundleManifest,
                false,
                true,
            ),
        ],
        claim_boundary_summary: vec![
            "Audit indexes are not accepted evidence.".to_string(),
            "Audit indexes are local integrity summaries, not official benchmark evidence."
                .to_string(),
            "Audit indexes do not create Level2+ evidence.".to_string(),
            "Audit indexes do not prove ZK backend performance.".to_string(),
        ],
        failed_readiness_visible: true,
        local_only_warnings_visible: true,
        mutates_source_pack: false,
        mutates_source_report: false,
        mutates_report_bundle: false,
        replay_command_execution_output: false,
        external_replay_authorized: false,
        creates_level2_evidence: false,
        official_benchmark_evidence: false,
        zk_backend_performance_claims: false,
        mutates_accepted_evidence_ledger: false,
        populates_score_axes_from_local_only: false,
        output_claim_boundary: ClaimBoundary::Level0DesignNote,
        limitations: vec![
            "Audit indexes are not accepted evidence.".to_string(),
            "Audit indexes are local integrity summaries, not official benchmark evidence."
                .to_string(),
            "Audit indexes do not create Level2+ evidence.".to_string(),
            "Audit indexes do not prove ZK backend performance.".to_string(),
            "Audit indexes do not mutate source packs, source reports, report bundles, or the accepted Evidence Ledger.".to_string(),
        ],
        notes: vec!["phase s fixture".to_string()],
    }
}

#[test]
fn audit_index_ergonomics_builds_filtered_grouped_markdown_view() {
    let manifest = valid_manifest();
    let request = LocalAuditIndexErgonomicsRequest {
        filters: vec![LocalAuditIndexErgonomicsFilter {
            field: LocalAuditIndexErgonomicsFilterField::InputKind,
            value: "PackReadinessReport".to_string(),
        }],
        group_by: LocalAuditIndexErgonomicsGroupKey::FailedReadiness,
        sort_by: LocalAuditIndexErgonomicsSortKey::InputId,
    };

    let view = build_local_audit_index_ergonomics_view(&manifest, &request)
        .expect("valid ergonomics view builds");

    assert_eq!(view.output_claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(view.selected_input_ids, vec!["readiness_report"]);
    assert!(view.rejected_filters.is_empty());
    assert_eq!(view.groups.len(), 1);
    assert_eq!(view.groups[0].group_value, "true");
    assert_eq!(view.warning_summary.failed_readiness_input_count, 1);
    assert!(!view.warning_summary.source_mutation_claimed);
    assert_eq!(
        view.limitation_labels,
        required_local_audit_index_ergonomics_limitations()
    );
    assert!(view
        .markdown
        .contains("Audit-index ergonomics are local presentation metadata only."));
    assert!(view
        .markdown
        .contains("Audit-index ergonomics do not create Level2+ evidence."));
    assert!(view
        .markdown
        .contains("Internal timing telemetry is not ZK backend performance."));
    assert!(!view.markdown.contains("official_benchmark_evidence: true"));
    assert!(!view.markdown.contains("creates_level2_evidence: true"));
    assert!(!view
        .markdown
        .contains("zk_backend_performance_claims: true"));
}

#[test]
fn audit_index_ergonomics_filters_sorts_and_groups_remaining_variants() {
    let manifest = valid_manifest();

    let by_claim_boundary = build_local_audit_index_ergonomics_view(
        &manifest,
        &LocalAuditIndexErgonomicsRequest {
            filters: vec![LocalAuditIndexErgonomicsFilter {
                field: LocalAuditIndexErgonomicsFilterField::ClaimBoundary,
                value: "Level0DesignNote".to_string(),
            }],
            group_by: LocalAuditIndexErgonomicsGroupKey::ClaimBoundary,
            sort_by: LocalAuditIndexErgonomicsSortKey::ArtifactUri,
        },
    )
    .expect("claim-boundary ergonomics view should build");
    assert_eq!(by_claim_boundary.groups[0].group_value, "Level0DesignNote");
    assert_eq!(
        by_claim_boundary.selected_input_ids,
        vec!["pack_manifest", "readiness_report", "bundle_manifest"]
    );

    let by_local_warning_visibility = build_local_audit_index_ergonomics_view(
        &manifest,
        &LocalAuditIndexErgonomicsRequest {
            filters: vec![LocalAuditIndexErgonomicsFilter {
                field: LocalAuditIndexErgonomicsFilterField::LocalOnlyWarningsVisible,
                value: "true".to_string(),
            }],
            group_by: LocalAuditIndexErgonomicsGroupKey::LocalOnlyWarningsVisible,
            sort_by: LocalAuditIndexErgonomicsSortKey::InputKind,
        },
    )
    .expect("local-warning ergonomics view should build");
    assert_eq!(by_local_warning_visibility.groups[0].group_value, "true");

    let by_failed_readiness = build_local_audit_index_ergonomics_view(
        &manifest,
        &LocalAuditIndexErgonomicsRequest {
            filters: vec![LocalAuditIndexErgonomicsFilter {
                field: LocalAuditIndexErgonomicsFilterField::FailedReadiness,
                value: "false".to_string(),
            }],
            group_by: LocalAuditIndexErgonomicsGroupKey::InputKind,
            sort_by: LocalAuditIndexErgonomicsSortKey::ClaimBoundary,
        },
    )
    .expect("failed-readiness ergonomics view should build");
    assert_eq!(
        by_failed_readiness.selected_input_ids,
        vec!["bundle_manifest", "pack_manifest"]
    );
}

#[test]
fn audit_index_ergonomics_rejects_unsafe_and_invalid_boolean_filters() {
    let manifest = valid_manifest();
    let request = LocalAuditIndexErgonomicsRequest {
        filters: vec![
            LocalAuditIndexErgonomicsFilter {
                field: LocalAuditIndexErgonomicsFilterField::InputKind,
                value: "../PackReadinessReport".to_string(),
            },
            LocalAuditIndexErgonomicsFilter {
                field: LocalAuditIndexErgonomicsFilterField::FailedReadiness,
                value: "yes".to_string(),
            },
        ],
        ..LocalAuditIndexErgonomicsRequest::default()
    };

    let validation = validate_local_audit_index_ergonomics_request(&manifest, &request);
    let kinds = validation
        .issues
        .iter()
        .map(|issue| issue.kind)
        .collect::<Vec<_>>();

    assert!(!validation.valid);
    assert!(kinds.contains(&LocalAuditIndexErgonomicsIssueKind::InvalidFilterValue));
    assert!(kinds.contains(&LocalAuditIndexErgonomicsIssueKind::InvalidBooleanFilterValue));
    assert!(build_local_audit_index_ergonomics_view(&manifest, &request).is_err());
}

#[test]
fn audit_index_ergonomics_fail_closed_on_invalid_source_manifest() {
    let mut manifest = valid_manifest();
    manifest.failed_readiness_visible = false;
    manifest.mutates_source_pack = true;

    let validation = validate_local_audit_index_ergonomics_request(
        &manifest,
        &LocalAuditIndexErgonomicsRequest::default(),
    );

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.kind == LocalAuditIndexErgonomicsIssueKind::InvalidManifest));
    assert!(build_local_audit_index_ergonomics_view(
        &manifest,
        &LocalAuditIndexErgonomicsRequest::default()
    )
    .is_err());
}

#[test]
fn audit_index_ergonomics_outputs_write_and_read_declared_files_only() {
    let manifest = valid_manifest();
    let request = LocalAuditIndexErgonomicsRequest::default();
    let view = build_local_audit_index_ergonomics_view(&manifest, &request)
        .expect("valid ergonomics view");
    let dir = tempfile::tempdir().expect("tempdir");
    let source_root = dir.path().join("source");
    fs::create_dir_all(&source_root).expect("source root");
    let source_file = source_root.join("audit-index-manifest.json");
    fs::write(&source_file, b"{\"source\":true}\n").expect("source file");
    let source_before = fs::read(&source_file).expect("source before");
    let output_root = dir.path().join("audit-index-ergonomics");

    let output = write_local_audit_index_ergonomics_outputs(
        &output_root,
        &manifest,
        &request,
        &view,
        false,
        &[source_root.as_path()],
    )
    .expect("ergonomics outputs write");

    assert_eq!(
        output.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(output_root.join(AUDIT_INDEX_ERGONOMICS_VIEW_PATH).is_file());
    assert!(output_root
        .join(AUDIT_INDEX_ERGONOMICS_MARKDOWN_PATH)
        .is_file());
    assert!(output_root
        .join(AUDIT_INDEX_ERGONOMICS_VIEW_DIGEST_PATH)
        .is_file());
    assert!(output_root
        .join(AUDIT_INDEX_ERGONOMICS_MARKDOWN_DIGEST_PATH)
        .is_file());
    assert_eq!(
        fs::read_to_string(output_root.join(AUDIT_INDEX_ERGONOMICS_VIEW_PATH)).expect("view json"),
        serialize_local_audit_index_ergonomics_view_json(&view).expect("view json")
    );
    assert_eq!(
        fs::read_to_string(output_root.join(AUDIT_INDEX_ERGONOMICS_MARKDOWN_PATH))
            .expect("markdown"),
        view.markdown
    );

    let read_output = read_local_audit_index_ergonomics_outputs(
        &output_root,
        &manifest,
        &request,
        &[source_root.as_path()],
    )
    .expect("ergonomics outputs read");
    assert_eq!(read_output.view, view);
    assert_eq!(read_output.view_digest, output.view_digest);
    assert_eq!(read_output.markdown_digest, output.markdown_digest);
    assert_eq!(fs::read(source_file).expect("source after"), source_before);
}

#[test]
fn audit_index_ergonomics_outputs_reject_invalid_and_drifted_views() {
    let manifest = valid_manifest();
    let request = LocalAuditIndexErgonomicsRequest::default();
    let view = build_local_audit_index_ergonomics_view(&manifest, &request)
        .expect("valid ergonomics view");
    let dir = tempfile::tempdir().expect("tempdir");
    let protected_root = dir.path().join("source");
    fs::create_dir_all(&protected_root).expect("protected root");

    let mut invalid_manifest = manifest.clone();
    invalid_manifest.creates_level2_evidence = true;
    let validation_error = write_local_audit_index_ergonomics_outputs(
        dir.path().join("invalid-manifest"),
        &invalid_manifest,
        &request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect_err("invalid manifest should fail");
    assert!(validation_error
        .to_string()
        .contains("ergonomics validation failed"));

    let mut drifted_view = view.clone();
    drifted_view
        .selected_input_ids
        .push("not_derived".to_string());
    let drift_error = write_local_audit_index_ergonomics_outputs(
        dir.path().join("drifted-view"),
        &manifest,
        &request,
        &drifted_view,
        false,
        &[protected_root.as_path()],
    )
    .expect_err("drifted view should fail");
    assert!(drift_error
        .to_string()
        .contains("does not match deterministic source manifest/request derivation"));

    let mut escalated_view = view.clone();
    escalated_view.output_claim_boundary = ClaimBoundary::Level1LocalReplay;
    let claim_error = write_local_audit_index_ergonomics_outputs(
        dir.path().join("claim-escalation"),
        &manifest,
        &request,
        &escalated_view,
        false,
        &[protected_root.as_path()],
    )
    .expect_err("claim escalation should fail");
    assert!(claim_error
        .to_string()
        .contains("must remain Level0DesignNote"));

    let mut missing_limitation_view = view.clone();
    missing_limitation_view.limitation_labels.pop();
    let limitation_error = write_local_audit_index_ergonomics_outputs(
        dir.path().join("missing-limitation"),
        &manifest,
        &request,
        &missing_limitation_view,
        false,
        &[protected_root.as_path()],
    )
    .expect_err("missing limitation should fail");
    assert!(limitation_error
        .to_string()
        .contains("missing required ergonomics limitation label"));
}

#[test]
fn audit_index_ergonomics_outputs_reject_overwrite_and_materialized_drift() {
    let manifest = valid_manifest();
    let request = LocalAuditIndexErgonomicsRequest::default();
    let view = build_local_audit_index_ergonomics_view(&manifest, &request)
        .expect("valid ergonomics view");
    let dir = tempfile::tempdir().expect("tempdir");
    let protected_root = dir.path().join("source");
    fs::create_dir_all(&protected_root).expect("protected root");
    let output_root = dir.path().join("audit-index-ergonomics");

    write_local_audit_index_ergonomics_outputs(
        &output_root,
        &manifest,
        &request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect("initial write succeeds");

    let overwrite_error = write_local_audit_index_ergonomics_outputs(
        &output_root,
        &manifest,
        &request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect_err("non-empty root without overwrite should fail");
    assert!(overwrite_error
        .to_string()
        .contains("explicit overwrite approval is required"));

    fs::write(
        output_root.join(AUDIT_INDEX_ERGONOMICS_MARKDOWN_PATH),
        b"# tampered\n",
    )
    .expect("tamper markdown");
    let markdown_error = read_local_audit_index_ergonomics_outputs(
        &output_root,
        &manifest,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("tampered Markdown should fail");
    assert!(markdown_error
        .to_string()
        .contains("ergonomics Markdown bytes do not match digest sidecar"));

    let drift_overwrite_error = write_local_audit_index_ergonomics_outputs(
        &output_root,
        &manifest,
        &request,
        &view,
        true,
        &[protected_root.as_path()],
    )
    .expect_err("overwrite should reject materialized drift");
    assert!(drift_overwrite_error
        .to_string()
        .contains("ergonomics Markdown bytes do not match digest sidecar"));

    fs::remove_dir_all(&output_root).expect("remove drifted output");
    write_local_audit_index_ergonomics_outputs(
        &output_root,
        &manifest,
        &request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect("rewrite clean output");
    fs::write(
        output_root.join(AUDIT_INDEX_ERGONOMICS_VIEW_DIGEST_PATH),
        b"0000000000000000000000000000000000000000000000000000000000000000\n",
    )
    .expect("tamper view digest");
    let view_error = read_local_audit_index_ergonomics_outputs(
        &output_root,
        &manifest,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("stale view digest should fail");
    assert!(view_error
        .to_string()
        .contains("ergonomics view JSON bytes do not match digest sidecar"));
}

#[test]
fn audit_index_ergonomics_outputs_reject_readback_encoding_and_view_drift() {
    let manifest = valid_manifest();
    let request = LocalAuditIndexErgonomicsRequest::default();
    let view = build_local_audit_index_ergonomics_view(&manifest, &request)
        .expect("valid ergonomics view");
    let dir = tempfile::tempdir().expect("tempdir");
    let protected_root = dir.path().join("source");
    fs::create_dir_all(&protected_root).expect("protected root");

    let invalid_output_root = dir.path().join("bad;root");
    let invalid_root_error = write_local_audit_index_ergonomics_outputs(
        &invalid_output_root,
        &manifest,
        &request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect_err("shell-like output root should fail");
    assert!(invalid_root_error
        .to_string()
        .contains("invalid audit-index output root"));

    let invalid_protected = dir.path().join("bad;protected");
    let invalid_protected_error = write_local_audit_index_ergonomics_outputs(
        dir.path().join("invalid-protected"),
        &manifest,
        &request,
        &view,
        false,
        &[invalid_protected.as_path()],
    )
    .expect_err("shell-like protected root should fail");
    assert!(invalid_protected_error
        .to_string()
        .contains("invalid protected audit-index ergonomics path"));

    let file_root = dir.path().join("audit-index-ergonomics-file-root");
    fs::write(&file_root, b"not a directory\n").expect("file root");
    let file_root_error = write_local_audit_index_ergonomics_outputs(
        &file_root,
        &manifest,
        &request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect_err("file output root should fail");
    assert!(file_root_error
        .to_string()
        .contains("output root exists and is not a directory"));

    let non_utf8_view_sidecar = dir.path().join("non-utf8-view-sidecar");
    write_local_audit_index_ergonomics_outputs(
        &non_utf8_view_sidecar,
        &manifest,
        &request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect("fixture writes");
    fs::write(
        non_utf8_view_sidecar.join(AUDIT_INDEX_ERGONOMICS_VIEW_DIGEST_PATH),
        [0xff, 0xfe, 0xfd],
    )
    .expect("tamper view digest sidecar");
    let view_sidecar_error = read_local_audit_index_ergonomics_outputs(
        &non_utf8_view_sidecar,
        &manifest,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("non-UTF-8 view digest sidecar should fail");
    assert!(view_sidecar_error
        .to_string()
        .contains("ergonomics view digest sidecar is not UTF-8"));

    let non_utf8_markdown_sidecar = dir.path().join("non-utf8-markdown-sidecar");
    write_local_audit_index_ergonomics_outputs(
        &non_utf8_markdown_sidecar,
        &manifest,
        &request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect("fixture writes");
    fs::write(
        non_utf8_markdown_sidecar.join(AUDIT_INDEX_ERGONOMICS_MARKDOWN_DIGEST_PATH),
        [0xff, 0xfe, 0xfd],
    )
    .expect("tamper Markdown digest sidecar");
    let markdown_sidecar_error = read_local_audit_index_ergonomics_outputs(
        &non_utf8_markdown_sidecar,
        &manifest,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("non-UTF-8 Markdown digest sidecar should fail");
    assert!(markdown_sidecar_error
        .to_string()
        .contains("ergonomics Markdown digest sidecar is not UTF-8"));

    let non_utf8_view = dir.path().join("non-utf8-view");
    write_local_audit_index_ergonomics_outputs(
        &non_utf8_view,
        &manifest,
        &request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect("fixture writes");
    let invalid_view_bytes = vec![0xff, 0xfe, 0xfd];
    let invalid_view_digest = compute_artifact_digest_bytes(
        &invalid_view_bytes,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    );
    fs::write(
        non_utf8_view.join(AUDIT_INDEX_ERGONOMICS_VIEW_PATH),
        &invalid_view_bytes,
    )
    .expect("tamper view bytes");
    fs::write(
        non_utf8_view.join(AUDIT_INDEX_ERGONOMICS_VIEW_DIGEST_PATH),
        format!("{}\n", invalid_view_digest.hex_digest),
    )
    .expect("matching digest sidecar");
    let view_error = read_local_audit_index_ergonomics_outputs(
        &non_utf8_view,
        &manifest,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("non-UTF-8 view JSON should fail after digest check");
    assert!(view_error
        .to_string()
        .contains("ergonomics view JSON is not UTF-8"));

    let non_utf8_markdown = dir.path().join("non-utf8-markdown");
    write_local_audit_index_ergonomics_outputs(
        &non_utf8_markdown,
        &manifest,
        &request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect("fixture writes");
    let invalid_markdown_bytes = vec![0xff, 0xfe, 0xfd];
    let invalid_markdown_digest = compute_artifact_digest_bytes(
        &invalid_markdown_bytes,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    );
    fs::write(
        non_utf8_markdown.join(AUDIT_INDEX_ERGONOMICS_MARKDOWN_PATH),
        &invalid_markdown_bytes,
    )
    .expect("tamper Markdown bytes");
    fs::write(
        non_utf8_markdown.join(AUDIT_INDEX_ERGONOMICS_MARKDOWN_DIGEST_PATH),
        format!("{}\n", invalid_markdown_digest.hex_digest),
    )
    .expect("matching Markdown digest sidecar");
    let markdown_error = read_local_audit_index_ergonomics_outputs(
        &non_utf8_markdown,
        &manifest,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("non-UTF-8 Markdown should fail after digest check");
    assert!(markdown_error
        .to_string()
        .contains("ergonomics Markdown is not UTF-8"));

    let markdown_mismatch = dir.path().join("markdown-mismatch");
    write_local_audit_index_ergonomics_outputs(
        &markdown_mismatch,
        &manifest,
        &request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect("fixture writes");
    let mismatched_markdown = b"# different but digest-consistent\n";
    let mismatched_digest = compute_artifact_digest_bytes(
        mismatched_markdown,
        Some(ArtifactKind::Other),
        Some(ArtifactRole::Report),
    );
    fs::write(
        markdown_mismatch.join(AUDIT_INDEX_ERGONOMICS_MARKDOWN_PATH),
        mismatched_markdown,
    )
    .expect("tamper Markdown bytes");
    fs::write(
        markdown_mismatch.join(AUDIT_INDEX_ERGONOMICS_MARKDOWN_DIGEST_PATH),
        format!("{}\n", mismatched_digest.hex_digest),
    )
    .expect("matching Markdown digest");
    let mismatch_error = read_local_audit_index_ergonomics_outputs(
        &markdown_mismatch,
        &manifest,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("digest-consistent Markdown mismatch should fail");
    assert!(mismatch_error
        .to_string()
        .contains("ergonomics Markdown bytes do not match selected view"));
}

#[test]
fn audit_index_ergonomics_outputs_reject_partial_unexpected_and_protected_roots() {
    let manifest = valid_manifest();
    let request = LocalAuditIndexErgonomicsRequest::default();
    let view = build_local_audit_index_ergonomics_view(&manifest, &request)
        .expect("valid ergonomics view");
    let dir = tempfile::tempdir().expect("tempdir");
    let protected_root = dir.path().join("source");
    fs::create_dir_all(&protected_root).expect("protected root");

    let nested_error = write_local_audit_index_ergonomics_outputs(
        protected_root.join("audit-index-ergonomics"),
        &manifest,
        &request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect_err("nested protected root should fail");
    assert!(nested_error
        .to_string()
        .contains("must not overlap protected path"));

    let parent_root = dir.path().join("parent-output");
    let child_protected = parent_root.join("source.json");
    let parent_error = write_local_audit_index_ergonomics_outputs(
        &parent_root,
        &manifest,
        &request,
        &view,
        false,
        &[child_protected.as_path()],
    )
    .expect_err("parent of protected path should fail");
    assert!(parent_error
        .to_string()
        .contains("must not overlap protected path"));

    let output_root = dir.path().join("audit-index-ergonomics");
    write_local_audit_index_ergonomics_outputs(
        &output_root,
        &manifest,
        &request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect("initial write succeeds");
    fs::remove_file(output_root.join(AUDIT_INDEX_ERGONOMICS_MARKDOWN_PATH))
        .expect("remove Markdown");
    let partial_error = read_local_audit_index_ergonomics_outputs(
        &output_root,
        &manifest,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("partial bundle should fail");
    assert!(partial_error.to_string().contains("ergonomics-view.md"));

    fs::remove_dir_all(&output_root).expect("remove partial output");
    write_local_audit_index_ergonomics_outputs(
        &output_root,
        &manifest,
        &request,
        &view,
        true,
        &[protected_root.as_path()],
    )
    .expect("overwrite restores complete bundle");
    fs::write(output_root.join("unexpected.txt"), b"stale\n").expect("unexpected file");
    let unexpected_error = read_local_audit_index_ergonomics_outputs(
        &output_root,
        &manifest,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("unexpected file should fail");
    assert!(unexpected_error
        .to_string()
        .contains("contains an unexpected file"));
}

#[test]
fn audit_index_ergonomics_outputs_reject_relative_absolute_protected_overlap() {
    let manifest = valid_manifest();
    let request = LocalAuditIndexErgonomicsRequest::default();
    let view = build_local_audit_index_ergonomics_view(&manifest, &request)
        .expect("valid ergonomics view");
    let relative_protected_root =
        std::path::PathBuf::from("target/phase-s-ergonomics-overlap-source");
    let relative_output_root = relative_protected_root.join("audit-index-ergonomics");
    let absolute_protected_root = std::env::current_dir()
        .expect("current dir")
        .join(&relative_protected_root);
    let _ = fs::remove_dir_all(&relative_protected_root);
    fs::create_dir_all(&relative_protected_root).expect("protected root");

    let overlap_error = write_local_audit_index_ergonomics_outputs(
        &relative_output_root,
        &manifest,
        &request,
        &view,
        false,
        &[absolute_protected_root.as_path()],
    )
    .expect_err("relative output under absolute protected path should fail");
    assert!(overlap_error
        .to_string()
        .contains("must not overlap protected path"));
    assert!(
        !relative_output_root.exists(),
        "overlap rejection must happen before any output directory is written"
    );

    fs::remove_dir_all(&relative_protected_root).expect("cleanup protected root");
}

#[cfg(unix)]
#[test]
fn audit_index_ergonomics_outputs_reject_symlinks() {
    use std::os::unix::fs::symlink;

    let manifest = valid_manifest();
    let request = LocalAuditIndexErgonomicsRequest::default();
    let view = build_local_audit_index_ergonomics_view(&manifest, &request)
        .expect("valid ergonomics view");
    let dir = tempfile::tempdir().expect("tempdir");
    let protected_root = dir.path().join("source");
    fs::create_dir_all(&protected_root).expect("protected root");
    let output_root = dir.path().join("audit-index-ergonomics");
    fs::create_dir_all(&output_root).expect("output root");
    fs::write(dir.path().join("outside.json"), b"{}\n").expect("outside file");
    symlink(
        dir.path().join("outside.json"),
        output_root.join(AUDIT_INDEX_ERGONOMICS_VIEW_PATH),
    )
    .expect("symlink");

    let read_error = read_local_audit_index_ergonomics_outputs(
        &output_root,
        &manifest,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("symlink read should fail");
    assert!(read_error.to_string().contains("must not contain symlinks"));

    let write_error = write_local_audit_index_ergonomics_outputs(
        &output_root,
        &manifest,
        &request,
        &view,
        true,
        &[protected_root.as_path()],
    )
    .expect_err("symlink write should fail");
    assert!(write_error
        .to_string()
        .contains("must not contain symlinks"));
}

#[test]
fn audit_index_ergonomics_source_exposes_no_runtime_surface() {
    let source = include_str!("../src/audit_index.rs");

    for forbidden in [
        "Command::new",
        "std::net",
        "TcpStream",
        "package.json",
        "node_modules",
    ] {
        assert!(
            !source.contains(forbidden),
            "Phase S ergonomics must not expose {forbidden}"
        );
    }
}

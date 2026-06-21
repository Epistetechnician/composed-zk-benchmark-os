use zkbench_core::{
    build_local_audit_index_ergonomics_view, required_local_audit_index_ergonomics_limitations,
    validate_local_audit_index_ergonomics_request, ArtifactDigest, ArtifactDigestAlgorithm,
    ArtifactKind, ArtifactRole, ClaimBoundary, LocalAuditIndexErgonomicsFilter,
    LocalAuditIndexErgonomicsFilterField, LocalAuditIndexErgonomicsGroupKey,
    LocalAuditIndexErgonomicsIssueKind, LocalAuditIndexErgonomicsRequest,
    LocalAuditIndexErgonomicsSortKey, LocalAuditIndexInputKind, LocalAuditIndexInputRef,
    LocalAuditIndexManifest, LocalAuditIndexVersion,
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
fn audit_index_ergonomics_source_exposes_no_runtime_surface() {
    let source = include_str!("../src/audit_index.rs");

    for forbidden in [
        "write_local_audit_index_ergonomics",
        "read_local_audit_index_ergonomics",
        "Command::new",
        "std::net",
        "TcpStream",
    ] {
        assert!(
            !source.contains(forbidden),
            "Phase S ergonomics must not expose {forbidden}"
        );
    }
}

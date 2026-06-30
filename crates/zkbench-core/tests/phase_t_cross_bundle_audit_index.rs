use std::fs;

use zkbench_core::{
    build_local_audit_index_cross_bundle_view, compute_artifact_digest_bytes,
    deserialize_local_audit_index_cross_bundle_view_json,
    read_local_audit_index_cross_bundle_outputs,
    required_local_audit_index_cross_bundle_limitations,
    serialize_local_audit_index_cross_bundle_view_json,
    validate_local_audit_index_cross_bundle_request, write_local_audit_index_cross_bundle_outputs,
    ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind, ArtifactRole, ClaimBoundary,
    LocalAuditIndexCrossBundleGroupKey, LocalAuditIndexCrossBundleInput,
    LocalAuditIndexCrossBundleIssueKind, LocalAuditIndexCrossBundleRequest,
    LocalAuditIndexCrossBundleSignalKind, LocalAuditIndexCrossBundleSortKey,
    LocalAuditIndexInputKind, LocalAuditIndexInputRef, LocalAuditIndexManifest,
    LocalAuditIndexVersion, AUDIT_INDEX_CROSS_BUNDLE_MARKDOWN_DIGEST_PATH,
    AUDIT_INDEX_CROSS_BUNDLE_MARKDOWN_PATH, AUDIT_INDEX_CROSS_BUNDLE_VIEW_DIGEST_PATH,
    AUDIT_INDEX_CROSS_BUNDLE_VIEW_PATH,
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
    claim_boundary: ClaimBoundary,
    failed_readiness: bool,
) -> LocalAuditIndexInputRef {
    LocalAuditIndexInputRef {
        input_id: input_id.to_string(),
        artifact_uri: artifact_uri.to_string(),
        kind: LocalAuditIndexInputKind::PackReadinessReport,
        digest: digest(input_id, ArtifactKind::Other, ArtifactRole::Report),
        claim_boundary,
        failed_readiness,
        local_only_warnings_visible: true,
        source_input_ids: Vec::new(),
        notes: vec!["local fixture metadata".to_string()],
    }
}

fn valid_manifest(
    index_id: &str,
    indexed_pack_id: &str,
    inputs: Vec<LocalAuditIndexInputRef>,
) -> LocalAuditIndexManifest {
    let failed_readiness_visible = inputs.iter().any(|input| input.failed_readiness);
    LocalAuditIndexManifest {
        index_id: index_id.to_string(),
        version: LocalAuditIndexVersion::default(),
        indexed_pack_id: indexed_pack_id.to_string(),
        report_bundle_ids: vec![format!("{index_id}_bundle")],
        inputs,
        claim_boundary_summary: vec![
            "Audit indexes are not accepted evidence.".to_string(),
            "Audit indexes are local integrity summaries, not official benchmark evidence."
                .to_string(),
            "Audit indexes do not create Level2+ evidence.".to_string(),
            "Audit indexes do not prove ZK backend performance.".to_string(),
        ],
        failed_readiness_visible,
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
        notes: vec!["phase t fixture".to_string()],
    }
}

fn cross_bundle_request(
    left: LocalAuditIndexManifest,
    right: LocalAuditIndexManifest,
) -> LocalAuditIndexCrossBundleRequest {
    LocalAuditIndexCrossBundleRequest {
        inputs: vec![
            LocalAuditIndexCrossBundleInput {
                source_id: "source_a".to_string(),
                manifest: left,
            },
            LocalAuditIndexCrossBundleInput {
                source_id: "source_b".to_string(),
                manifest: right,
            },
        ],
        group_by: LocalAuditIndexCrossBundleGroupKey::IndexedPackId,
        sort_by: LocalAuditIndexCrossBundleSortKey::SourceId,
    }
}

fn simple_cross_bundle_request() -> LocalAuditIndexCrossBundleRequest {
    cross_bundle_request(
        valid_manifest(
            "audit_a",
            "pack_a",
            vec![input(
                "left",
                "reports/left.json",
                ClaimBoundary::Level0DesignNote,
                false,
            )],
        ),
        valid_manifest(
            "audit_b",
            "pack_b",
            vec![input(
                "right",
                "reports/right.json",
                ClaimBoundary::Level0DesignNote,
                false,
            )],
        ),
    )
}

#[test]
fn cross_bundle_builds_deterministic_local_view_with_audit_signals() {
    let left = valid_manifest(
        "audit_a",
        "pack_shared",
        vec![
            input(
                "shared_readiness",
                "reports/shared-readiness.json",
                ClaimBoundary::Level0DesignNote,
                true,
            ),
            input(
                "left_only",
                "reports/left-only.json",
                ClaimBoundary::Level0DesignNote,
                false,
            ),
        ],
    );
    let right = valid_manifest(
        "audit_b",
        "pack_shared",
        vec![
            input(
                "shared_readiness",
                "reports/shared-readiness.json",
                ClaimBoundary::Level1LocalReplay,
                true,
            ),
            input(
                "right_only",
                "reports/right-only.json",
                ClaimBoundary::Level1LocalReplay,
                false,
            ),
        ],
    );

    let view = build_local_audit_index_cross_bundle_view(&cross_bundle_request(left, right))
        .expect("valid cross-bundle view builds");

    assert_eq!(view.output_claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(view.sources.len(), 2);
    assert_eq!(view.sources[0].source_id, "source_a");
    assert_eq!(view.sources[1].source_id, "source_b");
    assert_eq!(view.groups.len(), 1);
    assert_eq!(view.groups[0].source_count, 2);
    assert_eq!(view.groups[0].input_count, 4);
    assert_eq!(view.warning_summary.failed_readiness_source_count, 2);
    assert_eq!(
        view.limitation_labels,
        required_local_audit_index_cross_bundle_limitations()
    );

    let signal_kinds = view
        .signals
        .iter()
        .map(|signal| signal.kind)
        .collect::<Vec<_>>();
    assert!(
        signal_kinds.contains(&LocalAuditIndexCrossBundleSignalKind::DuplicateInputIdSameArtifact)
    );
    assert!(signal_kinds.contains(&LocalAuditIndexCrossBundleSignalKind::RepeatedFailedReadiness));
    assert!(
        signal_kinds.contains(&LocalAuditIndexCrossBundleSignalKind::ClaimBoundaryCeilingMismatch)
    );

    assert!(view
        .markdown
        .contains("Cross-bundle audit indexes are local presentation metadata only."));
    assert!(view
        .markdown
        .contains("Duplicate local metadata is an audit signal, not independent confirmation."));
    assert!(!view.markdown.contains("official_benchmark_evidence: true"));
    assert!(!view.markdown.contains("creates_level2_evidence: true"));
    assert!(!view
        .markdown
        .contains("zk_backend_performance_claims: true"));
}

#[test]
fn cross_bundle_sorts_groups_and_signals_remaining_variants() {
    let mut left_manifest = valid_manifest(
        "audit_z",
        "pack_z",
        vec![input(
            "left",
            "reports/left.json",
            ClaimBoundary::Level0DesignNote,
            false,
        )],
    );
    left_manifest.inputs[0].local_only_warnings_visible = false;
    left_manifest
        .limitations
        .push("left-only limitation".to_string());
    let right_manifest = valid_manifest(
        "audit_a",
        "pack_a",
        vec![input(
            "right",
            "reports/right.json",
            ClaimBoundary::Level0DesignNote,
            false,
        )],
    );

    let by_index_id =
        build_local_audit_index_cross_bundle_view(&LocalAuditIndexCrossBundleRequest {
            inputs: vec![
                LocalAuditIndexCrossBundleInput {
                    source_id: "source_z".to_string(),
                    manifest: left_manifest.clone(),
                },
                LocalAuditIndexCrossBundleInput {
                    source_id: "source_a".to_string(),
                    manifest: right_manifest.clone(),
                },
            ],
            group_by: LocalAuditIndexCrossBundleGroupKey::LocalOnlyWarningsVisible,
            sort_by: LocalAuditIndexCrossBundleSortKey::IndexId,
        })
        .expect("index-id sorted cross-bundle view should build");
    assert_eq!(by_index_id.sources[0].index_id, "audit_a");
    assert_eq!(by_index_id.sources[1].index_id, "audit_z");
    assert!(by_index_id.groups.iter().any(|group| {
        group.group_key == LocalAuditIndexCrossBundleGroupKey::LocalOnlyWarningsVisible
            && group.group_value == "true"
    }));
    assert!(by_index_id.signals.iter().any(|signal| {
        signal.kind == LocalAuditIndexCrossBundleSignalKind::HiddenLocalOnlyWarnings
    }));
    assert!(by_index_id.signals.iter().any(|signal| {
        signal.kind == LocalAuditIndexCrossBundleSignalKind::LimitationLabelMismatch
    }));

    let by_pack_id =
        build_local_audit_index_cross_bundle_view(&LocalAuditIndexCrossBundleRequest {
            inputs: vec![
                LocalAuditIndexCrossBundleInput {
                    source_id: "source_z".to_string(),
                    manifest: left_manifest,
                },
                LocalAuditIndexCrossBundleInput {
                    source_id: "source_a".to_string(),
                    manifest: right_manifest,
                },
            ],
            group_by: LocalAuditIndexCrossBundleGroupKey::FailedReadinessVisible,
            sort_by: LocalAuditIndexCrossBundleSortKey::IndexedPackId,
        })
        .expect("pack-id sorted cross-bundle view should build");
    assert_eq!(by_pack_id.sources[0].indexed_pack_id, "pack_a");
    assert_eq!(by_pack_id.sources[1].indexed_pack_id, "pack_z");
    assert!(by_pack_id.groups.iter().any(|group| {
        group.group_key == LocalAuditIndexCrossBundleGroupKey::FailedReadinessVisible
            && group.group_value == "false"
    }));

    let by_output_claim_boundary =
        build_local_audit_index_cross_bundle_view(&LocalAuditIndexCrossBundleRequest {
            inputs: vec![
                LocalAuditIndexCrossBundleInput {
                    source_id: "source_z".to_string(),
                    manifest: valid_manifest(
                        "audit_z",
                        "pack_z",
                        vec![input(
                            "left",
                            "reports/left.json",
                            ClaimBoundary::Level0DesignNote,
                            false,
                        )],
                    ),
                },
                LocalAuditIndexCrossBundleInput {
                    source_id: "source_a".to_string(),
                    manifest: valid_manifest(
                        "audit_a",
                        "pack_a",
                        vec![input(
                            "right",
                            "reports/right.json",
                            ClaimBoundary::Level0DesignNote,
                            false,
                        )],
                    ),
                },
            ],
            group_by: LocalAuditIndexCrossBundleGroupKey::OutputClaimBoundary,
            sort_by: LocalAuditIndexCrossBundleSortKey::SourceId,
        })
        .expect("output-claim-boundary grouped view should build");
    assert!(by_output_claim_boundary.groups.iter().any(|group| {
        group.group_key == LocalAuditIndexCrossBundleGroupKey::OutputClaimBoundary
            && group.group_value == "Level0DesignNote"
    }));
}

#[test]
fn cross_bundle_distinguishes_duplicate_manifest_digest_cases() {
    let manifest = valid_manifest(
        "audit_same",
        "pack_a",
        vec![input(
            "readiness",
            "reports/readiness.json",
            ClaimBoundary::Level0DesignNote,
            false,
        )],
    );
    let same_digest_view = build_local_audit_index_cross_bundle_view(&cross_bundle_request(
        manifest.clone(),
        manifest.clone(),
    ))
    .expect("duplicate identical manifests build with signal");
    assert!(same_digest_view.signals.iter().any(|signal| {
        signal.kind == LocalAuditIndexCrossBundleSignalKind::DuplicateManifestIdSameDigest
    }));

    let mut conflicting = manifest.clone();
    conflicting.inputs.push(input(
        "other",
        "reports/other.json",
        ClaimBoundary::Level0DesignNote,
        false,
    ));
    let conflicting_view =
        build_local_audit_index_cross_bundle_view(&cross_bundle_request(manifest, conflicting))
            .expect("duplicate conflicting manifests build with signal");
    assert!(conflicting_view.signals.iter().any(|signal| {
        signal.kind == LocalAuditIndexCrossBundleSignalKind::DuplicateManifestIdConflictingDigest
    }));
}

#[test]
fn cross_bundle_distinguishes_conflicting_duplicate_input_refs() {
    let left = valid_manifest(
        "audit_left",
        "pack_a",
        vec![input(
            "shared_input",
            "reports/a.json",
            ClaimBoundary::Level0DesignNote,
            false,
        )],
    );
    let right = valid_manifest(
        "audit_right",
        "pack_b",
        vec![input(
            "shared_input",
            "reports/b.json",
            ClaimBoundary::Level0DesignNote,
            false,
        )],
    );

    let view = build_local_audit_index_cross_bundle_view(&cross_bundle_request(left, right))
        .expect("valid cross-bundle view builds");

    assert!(view.signals.iter().any(|signal| {
        signal.kind == LocalAuditIndexCrossBundleSignalKind::DuplicateInputIdConflictingArtifact
    }));
}

#[test]
fn cross_bundle_request_fails_closed_on_invalid_inputs() {
    let manifest = valid_manifest(
        "audit_a",
        "pack_a",
        vec![input(
            "readiness",
            "reports/readiness.json",
            ClaimBoundary::Level0DesignNote,
            true,
        )],
    );

    let too_few = LocalAuditIndexCrossBundleRequest {
        inputs: vec![LocalAuditIndexCrossBundleInput {
            source_id: "source_a".to_string(),
            manifest: manifest.clone(),
        }],
        group_by: LocalAuditIndexCrossBundleGroupKey::IndexedPackId,
        sort_by: LocalAuditIndexCrossBundleSortKey::SourceId,
    };
    let too_few_validation = validate_local_audit_index_cross_bundle_request(&too_few);
    assert!(!too_few_validation.valid);
    assert!(too_few_validation
        .issues
        .iter()
        .any(|issue| issue.kind == LocalAuditIndexCrossBundleIssueKind::TooFewManifests));
    assert!(build_local_audit_index_cross_bundle_view(&too_few).is_err());

    let mut invalid_manifest = manifest.clone();
    invalid_manifest.failed_readiness_visible = false;
    invalid_manifest.mutates_source_pack = true;
    let invalid_request = LocalAuditIndexCrossBundleRequest {
        inputs: vec![
            LocalAuditIndexCrossBundleInput {
                source_id: "source_a".to_string(),
                manifest: manifest.clone(),
            },
            LocalAuditIndexCrossBundleInput {
                source_id: "../source_b".to_string(),
                manifest: invalid_manifest,
            },
        ],
        group_by: LocalAuditIndexCrossBundleGroupKey::IndexedPackId,
        sort_by: LocalAuditIndexCrossBundleSortKey::SourceId,
    };
    let validation = validate_local_audit_index_cross_bundle_request(&invalid_request);
    let kinds = validation
        .issues
        .iter()
        .map(|issue| issue.kind)
        .collect::<Vec<_>>();
    assert!(!validation.valid);
    assert!(kinds.contains(&LocalAuditIndexCrossBundleIssueKind::InvalidSourceId));
    assert!(kinds.contains(&LocalAuditIndexCrossBundleIssueKind::InvalidManifest));
    assert!(build_local_audit_index_cross_bundle_view(&invalid_request).is_err());

    let duplicate_empty_source_ids = LocalAuditIndexCrossBundleRequest {
        inputs: vec![
            LocalAuditIndexCrossBundleInput {
                source_id: " ".to_string(),
                manifest: manifest.clone(),
            },
            LocalAuditIndexCrossBundleInput {
                source_id: " ".to_string(),
                manifest,
            },
        ],
        group_by: LocalAuditIndexCrossBundleGroupKey::IndexedPackId,
        sort_by: LocalAuditIndexCrossBundleSortKey::SourceId,
    };
    let source_id_validation =
        validate_local_audit_index_cross_bundle_request(&duplicate_empty_source_ids);
    let source_id_kinds = source_id_validation
        .issues
        .iter()
        .map(|issue| issue.kind)
        .collect::<Vec<_>>();
    assert!(source_id_kinds.contains(&LocalAuditIndexCrossBundleIssueKind::EmptySourceId));
    assert!(source_id_kinds.contains(&LocalAuditIndexCrossBundleIssueKind::DuplicateSourceId));
}

#[test]
fn cross_bundle_view_round_trips_as_local_metadata_only() {
    let left = valid_manifest(
        "audit_a",
        "pack_a",
        vec![input(
            "left",
            "reports/left.json",
            ClaimBoundary::Level0DesignNote,
            false,
        )],
    );
    let right = valid_manifest(
        "audit_b",
        "pack_b",
        vec![input(
            "right",
            "reports/right.json",
            ClaimBoundary::Level0DesignNote,
            false,
        )],
    );
    let request = LocalAuditIndexCrossBundleRequest {
        inputs: vec![
            LocalAuditIndexCrossBundleInput {
                source_id: "source_b".to_string(),
                manifest: right,
            },
            LocalAuditIndexCrossBundleInput {
                source_id: "source_a".to_string(),
                manifest: left,
            },
        ],
        group_by: LocalAuditIndexCrossBundleGroupKey::IndexedPackId,
        sort_by: LocalAuditIndexCrossBundleSortKey::SourceId,
    };

    let view = build_local_audit_index_cross_bundle_view(&request).expect("view builds");
    let json = serialize_local_audit_index_cross_bundle_view_json(&view).expect("serialize");
    let round_trip =
        deserialize_local_audit_index_cross_bundle_view_json(&json).expect("deserialize");

    assert_eq!(view, round_trip);
    assert_eq!(round_trip.sources[0].source_id, "source_a");
    assert_eq!(round_trip.sources[1].source_id, "source_b");
    assert_eq!(
        round_trip.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
}

#[test]
fn cross_bundle_outputs_write_and_read_declared_files_only() {
    let request = cross_bundle_request(
        valid_manifest(
            "audit_a",
            "pack_shared",
            vec![input(
                "shared_readiness",
                "reports/shared-readiness.json",
                ClaimBoundary::Level0DesignNote,
                true,
            )],
        ),
        valid_manifest(
            "audit_b",
            "pack_shared",
            vec![input(
                "shared_readiness",
                "reports/shared-readiness.json",
                ClaimBoundary::Level1LocalReplay,
                true,
            )],
        ),
    );
    let view = build_local_audit_index_cross_bundle_view(&request).expect("view builds");
    let dir = tempfile::tempdir().expect("tempdir");
    let source_root = dir.path().join("source-audit-index");
    fs::create_dir_all(&source_root).expect("source root");
    let source_file = source_root.join("audit-index-manifest.json");
    fs::write(&source_file, b"{\"source\":true}\n").expect("source file");
    let source_before = fs::read(&source_file).expect("source before");
    let output_root = dir.path().join("cross-bundle-audit-index");

    let output = write_local_audit_index_cross_bundle_outputs(
        &output_root,
        &request,
        &view,
        false,
        &[source_root.as_path()],
    )
    .expect("cross-bundle outputs write");

    assert_eq!(
        output.output_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert!(output_root
        .join(AUDIT_INDEX_CROSS_BUNDLE_VIEW_PATH)
        .is_file());
    assert!(output_root
        .join(AUDIT_INDEX_CROSS_BUNDLE_MARKDOWN_PATH)
        .is_file());
    assert!(output_root
        .join(AUDIT_INDEX_CROSS_BUNDLE_VIEW_DIGEST_PATH)
        .is_file());
    assert!(output_root
        .join(AUDIT_INDEX_CROSS_BUNDLE_MARKDOWN_DIGEST_PATH)
        .is_file());
    assert_eq!(
        fs::read_to_string(output_root.join(AUDIT_INDEX_CROSS_BUNDLE_VIEW_PATH))
            .expect("view json"),
        serialize_local_audit_index_cross_bundle_view_json(&view).expect("view json")
    );
    assert_eq!(
        fs::read_to_string(output_root.join(AUDIT_INDEX_CROSS_BUNDLE_MARKDOWN_PATH))
            .expect("markdown"),
        view.markdown
    );

    let read_output = read_local_audit_index_cross_bundle_outputs(
        &output_root,
        &request,
        &[source_root.as_path()],
    )
    .expect("cross-bundle outputs read");
    assert_eq!(read_output.view, view);
    assert_eq!(read_output.view_digest, output.view_digest);
    assert_eq!(read_output.markdown_digest, output.markdown_digest);
    assert_eq!(fs::read(source_file).expect("source after"), source_before);
}

#[test]
fn cross_bundle_outputs_reject_invalid_and_drifted_views() {
    let valid_left = valid_manifest(
        "audit_a",
        "pack_a",
        vec![input(
            "left",
            "reports/left.json",
            ClaimBoundary::Level0DesignNote,
            false,
        )],
    );
    let valid_right = valid_manifest(
        "audit_b",
        "pack_b",
        vec![input(
            "right",
            "reports/right.json",
            ClaimBoundary::Level0DesignNote,
            false,
        )],
    );
    let request = cross_bundle_request(valid_left.clone(), valid_right.clone());
    let view = build_local_audit_index_cross_bundle_view(&request).expect("view builds");
    let dir = tempfile::tempdir().expect("tempdir");
    let protected_root = dir.path().join("source");
    fs::create_dir_all(&protected_root).expect("protected root");

    let mut invalid_manifest = valid_left;
    invalid_manifest.creates_level2_evidence = true;
    let invalid_request = cross_bundle_request(invalid_manifest, valid_right);
    let validation_error = write_local_audit_index_cross_bundle_outputs(
        dir.path().join("invalid-request"),
        &invalid_request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect_err("invalid request should fail");
    assert!(validation_error
        .to_string()
        .contains("cross-bundle validation failed"));

    let mut drifted_view = view.clone();
    drifted_view.sources.pop();
    let drift_error = write_local_audit_index_cross_bundle_outputs(
        dir.path().join("drifted-view"),
        &request,
        &drifted_view,
        false,
        &[protected_root.as_path()],
    )
    .expect_err("drifted view should fail");
    assert!(drift_error
        .to_string()
        .contains("does not match deterministic source request derivation"));

    let mut escalated_view = view.clone();
    escalated_view.output_claim_boundary = ClaimBoundary::Level1LocalReplay;
    let claim_error = write_local_audit_index_cross_bundle_outputs(
        dir.path().join("claim-escalation"),
        &request,
        &escalated_view,
        false,
        &[protected_root.as_path()],
    )
    .expect_err("claim escalation should fail");
    assert!(claim_error
        .to_string()
        .contains("must remain Level0DesignNote"));

    let mut missing_limitation_view = view;
    missing_limitation_view.limitation_labels.pop();
    let limitation_error = write_local_audit_index_cross_bundle_outputs(
        dir.path().join("missing-limitation"),
        &request,
        &missing_limitation_view,
        false,
        &[protected_root.as_path()],
    )
    .expect_err("missing limitation should fail");
    assert!(limitation_error
        .to_string()
        .contains("missing required cross-bundle limitation label"));
}

#[test]
fn cross_bundle_outputs_reject_overwrite_and_materialized_drift() {
    let request = simple_cross_bundle_request();
    let view = build_local_audit_index_cross_bundle_view(&request).expect("view builds");
    let dir = tempfile::tempdir().expect("tempdir");
    let protected_root = dir.path().join("source");
    fs::create_dir_all(&protected_root).expect("protected root");
    let output_root = dir.path().join("cross-bundle-audit-index");

    write_local_audit_index_cross_bundle_outputs(
        &output_root,
        &request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect("initial write succeeds");

    let overwrite_error = write_local_audit_index_cross_bundle_outputs(
        &output_root,
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
        output_root.join(AUDIT_INDEX_CROSS_BUNDLE_MARKDOWN_PATH),
        b"# tampered\n",
    )
    .expect("tamper markdown");
    let markdown_error = read_local_audit_index_cross_bundle_outputs(
        &output_root,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("tampered Markdown should fail");
    assert!(markdown_error
        .to_string()
        .contains("cross-bundle Markdown bytes do not match digest sidecar"));

    let drift_overwrite_error = write_local_audit_index_cross_bundle_outputs(
        &output_root,
        &request,
        &view,
        true,
        &[protected_root.as_path()],
    )
    .expect_err("overwrite should reject materialized drift");
    assert!(drift_overwrite_error
        .to_string()
        .contains("cross-bundle Markdown bytes do not match digest sidecar"));

    fs::remove_dir_all(&output_root).expect("remove drifted output");
    write_local_audit_index_cross_bundle_outputs(
        &output_root,
        &request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect("rewrite clean output");
    fs::write(
        output_root.join(AUDIT_INDEX_CROSS_BUNDLE_VIEW_DIGEST_PATH),
        b"0000000000000000000000000000000000000000000000000000000000000000\n",
    )
    .expect("tamper view digest");
    let view_error = read_local_audit_index_cross_bundle_outputs(
        &output_root,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("stale view digest should fail");
    assert!(view_error
        .to_string()
        .contains("cross-bundle view JSON bytes do not match digest sidecar"));
}

#[test]
fn cross_bundle_outputs_reject_readback_encoding_and_view_drift() {
    let request = simple_cross_bundle_request();
    let view = build_local_audit_index_cross_bundle_view(&request).expect("view builds");
    let dir = tempfile::tempdir().expect("tempdir");
    let protected_root = dir.path().join("source");
    fs::create_dir_all(&protected_root).expect("protected root");

    let file_root = dir.path().join("cross-bundle-file-root");
    fs::write(&file_root, b"not a directory\n").expect("file root");
    let file_root_error = write_local_audit_index_cross_bundle_outputs(
        &file_root,
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
    write_local_audit_index_cross_bundle_outputs(
        &non_utf8_view_sidecar,
        &request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect("fixture writes");
    fs::write(
        non_utf8_view_sidecar.join(AUDIT_INDEX_CROSS_BUNDLE_VIEW_DIGEST_PATH),
        [0xff, 0xfe, 0xfd],
    )
    .expect("tamper view digest sidecar");
    let view_sidecar_error = read_local_audit_index_cross_bundle_outputs(
        &non_utf8_view_sidecar,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("non-UTF-8 view digest sidecar should fail");
    assert!(view_sidecar_error
        .to_string()
        .contains("cross-bundle view digest sidecar is not UTF-8"));

    let non_utf8_markdown_sidecar = dir.path().join("non-utf8-markdown-sidecar");
    write_local_audit_index_cross_bundle_outputs(
        &non_utf8_markdown_sidecar,
        &request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect("fixture writes");
    fs::write(
        non_utf8_markdown_sidecar.join(AUDIT_INDEX_CROSS_BUNDLE_MARKDOWN_DIGEST_PATH),
        [0xff, 0xfe, 0xfd],
    )
    .expect("tamper Markdown digest sidecar");
    let markdown_sidecar_error = read_local_audit_index_cross_bundle_outputs(
        &non_utf8_markdown_sidecar,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("non-UTF-8 Markdown digest sidecar should fail");
    assert!(markdown_sidecar_error
        .to_string()
        .contains("cross-bundle Markdown digest sidecar is not UTF-8"));

    let non_utf8_view = dir.path().join("non-utf8-view");
    write_local_audit_index_cross_bundle_outputs(
        &non_utf8_view,
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
        non_utf8_view.join(AUDIT_INDEX_CROSS_BUNDLE_VIEW_PATH),
        &invalid_view_bytes,
    )
    .expect("tamper view bytes");
    fs::write(
        non_utf8_view.join(AUDIT_INDEX_CROSS_BUNDLE_VIEW_DIGEST_PATH),
        format!("{}\n", invalid_view_digest.hex_digest),
    )
    .expect("matching digest sidecar");
    let view_error = read_local_audit_index_cross_bundle_outputs(
        &non_utf8_view,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("non-UTF-8 view JSON should fail after digest check");
    assert!(view_error
        .to_string()
        .contains("cross-bundle view JSON is not UTF-8"));

    let non_utf8_markdown = dir.path().join("non-utf8-markdown");
    write_local_audit_index_cross_bundle_outputs(
        &non_utf8_markdown,
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
        non_utf8_markdown.join(AUDIT_INDEX_CROSS_BUNDLE_MARKDOWN_PATH),
        &invalid_markdown_bytes,
    )
    .expect("tamper Markdown bytes");
    fs::write(
        non_utf8_markdown.join(AUDIT_INDEX_CROSS_BUNDLE_MARKDOWN_DIGEST_PATH),
        format!("{}\n", invalid_markdown_digest.hex_digest),
    )
    .expect("matching Markdown digest sidecar");
    let markdown_error = read_local_audit_index_cross_bundle_outputs(
        &non_utf8_markdown,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("non-UTF-8 Markdown should fail after digest check");
    assert!(markdown_error
        .to_string()
        .contains("cross-bundle Markdown is not UTF-8"));

    let markdown_mismatch = dir.path().join("markdown-mismatch");
    write_local_audit_index_cross_bundle_outputs(
        &markdown_mismatch,
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
        markdown_mismatch.join(AUDIT_INDEX_CROSS_BUNDLE_MARKDOWN_PATH),
        mismatched_markdown,
    )
    .expect("tamper Markdown bytes");
    fs::write(
        markdown_mismatch.join(AUDIT_INDEX_CROSS_BUNDLE_MARKDOWN_DIGEST_PATH),
        format!("{}\n", mismatched_digest.hex_digest),
    )
    .expect("matching Markdown digest");
    let mismatch_error = read_local_audit_index_cross_bundle_outputs(
        &markdown_mismatch,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("digest-consistent Markdown mismatch should fail");
    assert!(mismatch_error
        .to_string()
        .contains("cross-bundle Markdown bytes do not match selected view"));
}

#[test]
fn cross_bundle_outputs_reject_partial_unexpected_and_protected_roots() {
    let request = simple_cross_bundle_request();
    let view = build_local_audit_index_cross_bundle_view(&request).expect("view builds");
    let dir = tempfile::tempdir().expect("tempdir");
    let protected_root = dir.path().join("source");
    fs::create_dir_all(&protected_root).expect("protected root");

    let nested_error = write_local_audit_index_cross_bundle_outputs(
        protected_root.join("cross-bundle-audit-index"),
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
    let parent_error = write_local_audit_index_cross_bundle_outputs(
        &parent_root,
        &request,
        &view,
        false,
        &[child_protected.as_path()],
    )
    .expect_err("parent of protected path should fail");
    assert!(parent_error
        .to_string()
        .contains("must not overlap protected path"));

    let output_root = dir.path().join("cross-bundle-audit-index");
    write_local_audit_index_cross_bundle_outputs(
        &output_root,
        &request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect("initial write succeeds");
    fs::remove_file(output_root.join(AUDIT_INDEX_CROSS_BUNDLE_MARKDOWN_PATH))
        .expect("remove Markdown");
    let partial_error = read_local_audit_index_cross_bundle_outputs(
        &output_root,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("partial bundle should fail");
    assert!(partial_error.to_string().contains("cross-bundle-view.md"));

    fs::remove_dir_all(&output_root).expect("remove partial output");
    write_local_audit_index_cross_bundle_outputs(
        &output_root,
        &request,
        &view,
        true,
        &[protected_root.as_path()],
    )
    .expect("overwrite restores complete bundle");
    fs::write(output_root.join("unexpected.txt"), b"stale\n").expect("unexpected file");
    let unexpected_error = read_local_audit_index_cross_bundle_outputs(
        &output_root,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("unexpected file should fail");
    assert!(unexpected_error
        .to_string()
        .contains("contains an unexpected file"));
}

#[test]
fn cross_bundle_outputs_reject_relative_absolute_protected_overlap() {
    let request = simple_cross_bundle_request();
    let view = build_local_audit_index_cross_bundle_view(&request).expect("view builds");
    let relative_protected_root = std::path::PathBuf::from("target/phase-t-cross-bundle-source");
    let relative_output_root = relative_protected_root.join("cross-bundle-audit-index");
    let absolute_protected_root = std::env::current_dir()
        .expect("current dir")
        .join(&relative_protected_root);
    let _ = fs::remove_dir_all(&relative_protected_root);
    fs::create_dir_all(&relative_protected_root).expect("protected root");

    let overlap_error = write_local_audit_index_cross_bundle_outputs(
        &relative_output_root,
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
fn cross_bundle_outputs_reject_symlinks() {
    use std::os::unix::fs::symlink;

    let request = simple_cross_bundle_request();
    let view = build_local_audit_index_cross_bundle_view(&request).expect("view builds");
    let dir = tempfile::tempdir().expect("tempdir");
    let protected_root = dir.path().join("source");
    fs::create_dir_all(&protected_root).expect("protected root");
    let output_root = dir.path().join("cross-bundle-audit-index");
    fs::create_dir_all(&output_root).expect("output root");
    fs::write(dir.path().join("outside.json"), b"{}\n").expect("outside file");
    symlink(
        dir.path().join("outside.json"),
        output_root.join(AUDIT_INDEX_CROSS_BUNDLE_VIEW_PATH),
    )
    .expect("symlink");

    let read_error = read_local_audit_index_cross_bundle_outputs(
        &output_root,
        &request,
        &[protected_root.as_path()],
    )
    .expect_err("symlink read should fail");
    assert!(read_error.to_string().contains("must not contain symlinks"));

    let write_error = write_local_audit_index_cross_bundle_outputs(
        &output_root,
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

#[cfg(unix)]
#[test]
fn cross_bundle_outputs_reject_symlink_parent_into_protected_root() {
    use std::os::unix::fs::symlink;

    let request = simple_cross_bundle_request();
    let view = build_local_audit_index_cross_bundle_view(&request).expect("view builds");
    let dir = tempfile::tempdir().expect("tempdir");
    let protected_root = dir.path().join("source");
    fs::create_dir_all(&protected_root).expect("protected root");
    fs::write(protected_root.join("audit-index.json"), b"{}\n").expect("protected file");

    let linked_root = dir.path().join("linked-source");
    symlink(&protected_root, &linked_root).expect("symlink protected root");
    let output_root = linked_root.join("cross-bundle-audit-index");

    let write_error = write_local_audit_index_cross_bundle_outputs(
        &output_root,
        &request,
        &view,
        false,
        &[protected_root.as_path()],
    )
    .expect_err("symlink parent into protected root should fail");
    assert!(write_error
        .to_string()
        .contains("must not overlap protected path"));
    assert!(!output_root.exists());
}

#[test]
fn cross_bundle_audit_index_source_exposes_no_runtime_surface() {
    let source = include_str!("../src/audit_index.rs");
    for forbidden in [
        "std::process::Command",
        "Command::new",
        "tokio::process",
        "reqwest",
        "ureq",
        "std::net",
        "TcpStream",
        "package.json",
        "node_modules",
    ] {
        assert!(
            !source.contains(forbidden),
            "audit_index.rs must not expose {forbidden}"
        );
    }
}

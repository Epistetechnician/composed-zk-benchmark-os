use zkbench_core::{
    build_local_audit_index_cross_bundle_view,
    deserialize_local_audit_index_cross_bundle_view_json,
    required_local_audit_index_cross_bundle_limitations,
    serialize_local_audit_index_cross_bundle_view_json,
    validate_local_audit_index_cross_bundle_request, ArtifactDigest, ArtifactDigestAlgorithm,
    ArtifactKind, ArtifactRole, ClaimBoundary, LocalAuditIndexCrossBundleGroupKey,
    LocalAuditIndexCrossBundleInput, LocalAuditIndexCrossBundleIssueKind,
    LocalAuditIndexCrossBundleRequest, LocalAuditIndexCrossBundleSignalKind,
    LocalAuditIndexCrossBundleSortKey, LocalAuditIndexInputKind, LocalAuditIndexInputRef,
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
                manifest,
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
fn cross_bundle_audit_index_source_exposes_no_phase_t_output_surface() {
    let source = include_str!("../src/audit_index.rs");
    assert!(!source.contains("write_local_audit_index_cross_bundle"));
    assert!(!source.contains("read_local_audit_index_cross_bundle"));
    assert!(!source.contains("AUDIT_INDEX_CROSS_BUNDLE"));
    for forbidden in ["std::process::Command", "tokio::process", "reqwest", "ureq"] {
        assert!(
            !source.contains(forbidden),
            "audit_index.rs must not expose {forbidden}"
        );
    }
}

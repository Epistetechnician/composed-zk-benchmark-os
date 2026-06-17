use tempfile::tempdir;
use zkbench_core::{
    apply_mutation_pass, build_local_replay_manifest_for_instance,
    build_local_replay_manifest_for_mutation, compute_artifact_digest_bytes, generate_instance,
    run_local_replay, score_report_from_local_mutation_evidence, ArtifactKind, ArtifactRole,
    BadCountersPass, BenchmarkPackFileRole, BenchmarkPackReader, BenchmarkPackWriter,
    ClaimBoundary, EvidenceAppendPolicy, EvidenceClass, EvidenceLedger, EvidenceRecord,
    GeneratorConfig, InstanceParams, LocalMutationEvidenceSummary, PerformanceScore,
    ProvenanceRecord, ScoreConfidence,
};

#[test]
fn benchmark_pack_writer_creates_valid_local_pack() {
    let instance = generate_instance(
        GeneratorConfig::bounded_counter_loop()
            .seed(47)
            .loop_bound(3),
        InstanceParams::default(),
    )
    .expect("bounded instance should generate");
    let mutated = apply_mutation_pass(&instance, &BadCountersPass)
        .expect("bad counter mutation should apply");

    let manifest = build_local_replay_manifest_for_instance(&instance)
        .expect("generated replay manifest should build");
    let mutation_manifest = build_local_replay_manifest_for_mutation(&mutated)
        .expect("mutated replay manifest should build");
    let result = run_local_replay(&manifest).expect("generated local replay should run");
    let mutation_result =
        run_local_replay(&mutation_manifest).expect("mutated local replay should run");

    let mut ledger = EvidenceLedger::new();
    ledger
        .append_replay_result(&result)
        .expect("generated evidence should append");
    ledger
        .append_replay_result(&mutation_result)
        .expect("mutated evidence should append");

    let dir = tempdir().expect("tempdir should be available for pack write");
    let pack_manifest = BenchmarkPackWriter::new("phase_f_local_pack_test")
        .with_generated_instance(instance)
        .with_mutated_instance(mutated)
        .with_replay_manifest(manifest)
        .with_replay_manifest(mutation_manifest)
        .with_replay_result(result)
        .with_replay_result(mutation_result)
        .with_evidence_ledger(ledger)
        .write_to(dir.path())
        .expect("pack should write");

    assert_eq!(
        pack_manifest.claim_boundary,
        ClaimBoundary::Level1LocalReplay
    );
    assert!(pack_manifest.uses_relative_paths_only());
    assert_eq!(pack_manifest.generated_instance_ids.len(), 1);
    assert_eq!(pack_manifest.mutation_ids.len(), 1);
    assert_eq!(pack_manifest.replay_manifest_ids.len(), 2);
    assert_eq!(pack_manifest.replay_result_ids.len(), 2);
    assert_eq!(
        pack_manifest.evidence_ledger_ref.as_deref(),
        Some("evidence/ledger.json")
    );
    assert!(pack_manifest
        .files
        .iter()
        .any(|file| file.role == BenchmarkPackFileRole::Readme));
    assert!(pack_manifest
        .files
        .iter()
        .any(|file| file.role == BenchmarkPackFileRole::EvidenceLedger));
    assert_eq!(pack_manifest.summary.score_report_count, 1);

    let readme = std::fs::read_to_string(dir.path().join("README.md"))
        .expect("pack README should be readable");
    assert!(readme.contains("This pack contains local replay artifacts only."));
    assert!(readme.contains("local replay is not official benchmark evidence"));
    assert!(readme.contains("a benchmark pass is not proof"));
    assert!(readme.contains("recursion proof is not semantic proof"));
    assert!(readme.contains("no external backend was invoked by this pack"));
    assert!(readme.contains("claim boundary is Level1LocalReplay or lower"));

    let reader = BenchmarkPackReader::read(dir.path()).expect("pack reader should load pack.json");
    let validation = reader.validate();
    assert!(
        validation.valid,
        "pack validation errors: {:?}",
        validation.errors
    );
    assert_eq!(reader.manifest(), &pack_manifest);
}

#[test]
fn benchmark_pack_writer_refuses_non_empty_directory_without_overwrite() {
    let dir = tempdir().expect("tempdir should be available");
    std::fs::write(dir.path().join("existing.txt"), "keep this file\n")
        .expect("test should be able to create existing file");

    let error = BenchmarkPackWriter::new("phase_f_non_empty")
        .write_to(dir.path())
        .expect_err("writer should reject non-empty directory by default");
    assert!(error.to_string().contains("non-empty"));
}

#[test]
fn benchmark_pack_validation_detects_file_tampering() {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(53),
        InstanceParams::default(),
    )
    .expect("baseline instance should generate");
    let manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    let result = run_local_replay(&manifest).expect("local replay should run");

    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_f_tamper_test")
        .with_generated_instance(instance)
        .with_replay_manifest(manifest)
        .with_replay_result(result)
        .write_to(dir.path())
        .expect("pack should write");

    std::fs::write(
        dir.path().join("README.md"),
        "local replay is not official benchmark evidence\nmodified\n",
    )
    .expect("test should be able to tamper with README");

    let reader = BenchmarkPackReader::read(dir.path()).expect("pack should load");
    let validation = reader.validate();
    assert!(!validation.valid);
    assert!(validation
        .errors
        .iter()
        .any(|error| error.path == "README.md" && error.message.contains("digest mismatch")));
}

#[test]
fn benchmark_pack_validation_rejects_invalid_nested_ledger() {
    let mut ledger = EvidenceLedger::new();
    let record = EvidenceRecord {
        evidence_class: EvidenceClass::ReproducibleBenchmarkArtifact,
        claim_boundary: ClaimBoundary::Level2ReproducibleBenchmarkArtifact,
        provenance: ProvenanceRecord {
            source: "future-metadata-placeholder".to_string(),
            captured_at: None,
            command: None,
            notes: vec!["future metadata only; not accepted pack evidence".to_string()],
        },
        artifact_digest: None,
        notes: Vec::new(),
        backend_target: None,
    };
    ledger
        .append_with_policy(record, EvidenceAppendPolicy::AllowFutureMetadata)
        .expect("future metadata policy can record candidate metadata");

    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_f_invalid_nested_ledger")
        .with_evidence_ledger(ledger)
        .write_to(dir.path())
        .expect("pack with nested invalid ledger should write for validation");

    let reader = BenchmarkPackReader::read(dir.path()).expect("pack should load");
    let validation = reader.validate();

    assert!(!validation.valid);
    assert!(validation.errors.iter().any(|error| {
        error.path == "evidence/ledger.json#0"
            && error.message.contains("exceeds Level1LocalReplay")
    }));
}

#[test]
fn benchmark_pack_writer_rejects_invalid_score_report() {
    let dir = tempdir().expect("tempdir should be available");
    let mut report = score_report_from_local_mutation_evidence(LocalMutationEvidenceSummary {
        local_accepted_traces: 1,
        local_rejected_traces: 1,
        mutation_variants_generated: 1,
        outcome_changes_observed: 0,
        unsound_acceptance_candidates: 0,
    });
    report.performance = Some(PerformanceScore {
        normalized_score: Some(1.0),
        confidence: ScoreConfidence::Low,
        missing_metrics: Vec::new(),
    });

    let error = BenchmarkPackWriter::new("phase_f_invalid_score_report")
        .with_score_report(report)
        .write_to(dir.path())
        .expect_err("invalid score report should be rejected");

    assert!(error.to_string().contains("score report validation failed"));
}

#[test]
fn benchmark_pack_reader_rejects_digest_consistent_invalid_score_report() {
    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_f_digest_consistent_invalid_score_report")
        .write_to(dir.path())
        .expect("valid local pack should write");

    let reader = BenchmarkPackReader::read(dir.path()).expect("pack should load");
    let mut manifest = reader.manifest().clone();
    let mut report = reader
        .load_score_report()
        .expect("score report should deserialize")
        .expect("score report should exist");
    report.performance = Some(PerformanceScore {
        normalized_score: Some(1.0),
        confidence: ScoreConfidence::Low,
        missing_metrics: Vec::new(),
    });
    let score_report_bytes =
        serde_json::to_vec_pretty(&report).expect("invalid score report should serialize");
    std::fs::write(
        dir.path().join("reports/score_report.json"),
        &score_report_bytes,
    )
    .expect("test should be able to rewrite score report");

    let score_report_file = manifest
        .files
        .iter_mut()
        .find(|file| file.role == BenchmarkPackFileRole::ScoreReport)
        .expect("pack should include score report file entry");
    score_report_file.digest = compute_artifact_digest_bytes(
        &score_report_bytes,
        Some(ArtifactKind::ScoreReport),
        Some(ArtifactRole::Report),
    );
    let manifest_bytes =
        serde_json::to_vec_pretty(&manifest).expect("pack manifest should serialize");
    std::fs::write(dir.path().join("pack.json"), manifest_bytes)
        .expect("test should be able to rewrite pack manifest");

    let reader = BenchmarkPackReader::read(dir.path()).expect("tampered pack should load");
    let validation = reader.validate();

    assert!(!validation.valid);
    assert!(validation.errors.iter().any(|error| {
        error.path == "reports/score_report.json#performance"
            && error.message.contains("leave score axes unpopulated")
    }));
}

#[test]
fn benchmark_pack_validation_rejects_forbidden_claim_text_in_manifest_notes() {
    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_f_forbidden_manifest_note")
        .write_to(dir.path())
        .expect("valid local pack should write");

    let reader = BenchmarkPackReader::read(dir.path()).expect("pack should load");
    let mut manifest = reader.manifest().clone();
    manifest
        .notes
        .push("this is official benchmark evidence".to_string());
    manifest
        .files
        .iter_mut()
        .find(|file| file.role == BenchmarkPackFileRole::ScoreReport)
        .expect("pack should include score report file entry")
        .notes
        .push("contains official benchmark evidence".to_string());
    let manifest_bytes =
        serde_json::to_vec_pretty(&manifest).expect("pack manifest should serialize");
    std::fs::write(dir.path().join("pack.json"), manifest_bytes)
        .expect("test should be able to rewrite pack manifest");

    let reader = BenchmarkPackReader::read(dir.path()).expect("tampered pack should load");
    let validation = reader.validate();

    assert!(!validation.valid);
    assert!(validation.errors.iter().any(|error| {
        error.path.starts_with("pack.json#notes[")
            && error
                .message
                .contains("pack metadata contains forbidden claim language")
    }));
    assert!(validation.errors.iter().any(|error| {
        error.path == "reports/score_report.json#notes[0]"
            && error
                .message
                .contains("pack metadata contains forbidden claim language")
    }));
}

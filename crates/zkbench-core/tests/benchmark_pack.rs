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
fn benchmark_pack_writer_rejects_file_root_and_dynamic_artifact_path_drift() {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(61),
        InstanceParams::default(),
    )
    .expect("baseline instance should generate");
    let mutated = apply_mutation_pass(&instance, &BadCountersPass)
        .expect("bad counter mutation should apply");
    let manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    let result = run_local_replay(&manifest).expect("local replay should run");

    let file_root = tempdir().expect("tempdir should be available");
    let file_root_path = file_root.path().join("pack-file-root");
    std::fs::write(&file_root_path, "not a directory\n")
        .expect("test should be able to create file root");
    let error = BenchmarkPackWriter::new("phase_f_file_root")
        .write_to(&file_root_path)
        .expect_err("writer should reject file roots");
    assert!(error.to_string().contains("not a directory"));

    let mut invalid_generated = instance.clone();
    invalid_generated.id = "../generated_escape".to_string();
    let dir = tempdir().expect("tempdir should be available");
    let error = BenchmarkPackWriter::new("phase_f_invalid_generated_path")
        .with_generated_instance(instance.clone())
        .with_generated_instance(invalid_generated)
        .write_to(dir.path())
        .expect_err("invalid generated id should fail path validation");
    assert!(error.to_string().contains("invalid pack relative path"));

    let mut invalid_mutated = mutated;
    invalid_mutated.id = "../mutated_escape".to_string();
    let dir = tempdir().expect("tempdir should be available");
    let error = BenchmarkPackWriter::new("phase_f_invalid_mutated_path")
        .with_mutated_instance(invalid_mutated)
        .write_to(dir.path())
        .expect_err("invalid mutated id should fail path validation");
    assert!(error.to_string().contains("invalid pack relative path"));

    let mut invalid_manifest = manifest.clone();
    invalid_manifest.id = "../manifest_escape".to_string();
    let dir = tempdir().expect("tempdir should be available");
    let error = BenchmarkPackWriter::new("phase_f_invalid_manifest_path")
        .with_replay_manifest(invalid_manifest)
        .write_to(dir.path())
        .expect_err("invalid replay manifest id should fail path validation");
    assert!(error.to_string().contains("invalid pack relative path"));

    let mut invalid_result = result;
    invalid_result.id = "../result_escape".to_string();
    let dir = tempdir().expect("tempdir should be available");
    let error = BenchmarkPackWriter::new("phase_f_invalid_result_path")
        .with_replay_result(invalid_result)
        .write_to(dir.path())
        .expect_err("invalid replay result id should fail path validation");
    assert!(error.to_string().contains("invalid pack relative path"));
}

#[test]
fn benchmark_pack_writer_reports_parent_conflicts_for_artifact_families() {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(62),
        InstanceParams::default(),
    )
    .expect("baseline instance should generate");
    let mutated = apply_mutation_pass(&instance, &BadCountersPass)
        .expect("bad counter mutation should apply");
    let manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    let result = run_local_replay(&manifest).expect("local replay should run");
    let mut ledger = EvidenceLedger::new();
    ledger
        .append_replay_result(&result)
        .expect("result should append to ledger");

    let root_parent_dir = tempdir().expect("tempdir should be available");
    let root_parent_file = root_parent_dir.path().join("pack-parent-file");
    std::fs::write(&root_parent_file, "not a directory\n")
        .expect("test should create root parent conflict");
    let error = BenchmarkPackWriter::new("phase_f_root_parent_conflict")
        .write_to(root_parent_file.join("child-pack"))
        .expect_err("root parent conflict should fail");
    assert!(error.to_string().contains("pack-parent-file"));

    let readme_dir = tempdir().expect("tempdir should be available");
    std::fs::create_dir(readme_dir.path().join("README.md"))
        .expect("test should create README path conflict");
    let error = BenchmarkPackWriter::new("phase_f_readme_path_conflict")
        .overwrite(true)
        .write_to(readme_dir.path())
        .expect_err("README path conflict should fail");
    assert!(error.to_string().contains("README.md"));

    let generated_dir = tempdir().expect("tempdir should be available");
    std::fs::write(generated_dir.path().join("specs"), "not a directory\n")
        .expect("test should create specs parent conflict");
    let error = BenchmarkPackWriter::new("phase_f_generated_parent_conflict")
        .with_generated_instance(instance)
        .overwrite(true)
        .write_to(generated_dir.path())
        .expect_err("generated parent conflict should fail");
    assert!(error.to_string().contains("specs"));

    let mutated_dir = tempdir().expect("tempdir should be available");
    std::fs::write(mutated_dir.path().join("specs"), "not a directory\n")
        .expect("test should create specs parent conflict");
    let error = BenchmarkPackWriter::new("phase_f_mutated_parent_conflict")
        .with_mutated_instance(mutated)
        .overwrite(true)
        .write_to(mutated_dir.path())
        .expect_err("mutated parent conflict should fail");
    assert!(error.to_string().contains("specs"));

    let manifest_dir = tempdir().expect("tempdir should be available");
    std::fs::write(manifest_dir.path().join("replay"), "not a directory\n")
        .expect("test should create replay parent conflict");
    let error = BenchmarkPackWriter::new("phase_f_manifest_parent_conflict")
        .with_replay_manifest(manifest)
        .overwrite(true)
        .write_to(manifest_dir.path())
        .expect_err("manifest parent conflict should fail");
    assert!(error.to_string().contains("replay"));

    let result_dir = tempdir().expect("tempdir should be available");
    std::fs::write(result_dir.path().join("replay"), "not a directory\n")
        .expect("test should create replay parent conflict");
    let error = BenchmarkPackWriter::new("phase_f_result_parent_conflict")
        .with_replay_result(result)
        .overwrite(true)
        .write_to(result_dir.path())
        .expect_err("result parent conflict should fail");
    assert!(error.to_string().contains("replay"));

    let ledger_dir = tempdir().expect("tempdir should be available");
    std::fs::write(ledger_dir.path().join("evidence"), "not a directory\n")
        .expect("test should create evidence parent conflict");
    let error = BenchmarkPackWriter::new("phase_f_ledger_parent_conflict")
        .with_evidence_ledger(ledger)
        .overwrite(true)
        .write_to(ledger_dir.path())
        .expect_err("ledger parent conflict should fail");
    assert!(error.to_string().contains("evidence"));

    let report_dir = tempdir().expect("tempdir should be available");
    std::fs::write(report_dir.path().join("reports"), "not a directory\n")
        .expect("test should create reports parent conflict");
    let error = BenchmarkPackWriter::new("phase_f_report_parent_conflict")
        .overwrite(true)
        .write_to(report_dir.path())
        .expect_err("score report parent conflict should fail");
    assert!(error.to_string().contains("reports"));
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

#[test]
fn benchmark_pack_validation_rejects_stale_manifest_summary() {
    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_f_stale_manifest_summary")
        .write_to(dir.path())
        .expect("valid local pack should write");

    let reader = BenchmarkPackReader::read(dir.path()).expect("pack should load");
    let mut manifest = reader.manifest().clone();
    manifest.summary.generated_instance_count = 1;
    manifest.summary.score_report_count = 0;
    manifest.summary.evidence_record_count = 10;
    manifest.summary.local_only = false;
    let manifest_bytes =
        serde_json::to_vec_pretty(&manifest).expect("pack manifest should serialize");
    std::fs::write(dir.path().join("pack.json"), manifest_bytes)
        .expect("test should be able to rewrite pack manifest");

    let reader = BenchmarkPackReader::read(dir.path()).expect("tampered pack should load");
    let validation = reader.validate();

    assert!(!validation.valid);
    assert!(validation
        .errors
        .iter()
        .any(|error| error.path == "pack.json#summary.generated_instance_count"));
    assert!(validation
        .errors
        .iter()
        .any(|error| error.path == "pack.json#summary.score_report_count"));
    assert!(validation
        .errors
        .iter()
        .any(|error| error.path == "pack.json#summary.evidence_record_count"));
    assert!(validation
        .errors
        .iter()
        .any(|error| error.path == "pack.json#summary.local_only"));
}

#[test]
fn benchmark_pack_validation_checks_every_score_report_file() {
    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_f_extra_invalid_score_report")
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
    let extra_report_bytes =
        serde_json::to_vec_pretty(&report).expect("extra score report should serialize");
    let extra_report_path = "reports/score_report_extra.json";
    std::fs::write(dir.path().join(extra_report_path), &extra_report_bytes)
        .expect("test should be able to write extra score report");
    let score_report_file = manifest
        .files
        .iter()
        .find(|file| file.role == BenchmarkPackFileRole::ScoreReport)
        .expect("pack should include score report file entry");
    let mut extra_file = score_report_file.clone();
    extra_file.relative_path = extra_report_path.to_string();
    extra_file.digest = compute_artifact_digest_bytes(
        &extra_report_bytes,
        Some(ArtifactKind::ScoreReport),
        Some(ArtifactRole::Report),
    );
    manifest.files.push(extra_file);
    manifest.summary.score_report_count = 2;
    let manifest_bytes =
        serde_json::to_vec_pretty(&manifest).expect("pack manifest should serialize");
    std::fs::write(dir.path().join("pack.json"), manifest_bytes)
        .expect("test should be able to rewrite pack manifest");

    let reader = BenchmarkPackReader::read(dir.path()).expect("tampered pack should load");
    let validation = reader.validate();

    assert!(!validation.valid);
    assert!(validation.errors.iter().any(|error| {
        error.path == "reports/score_report_extra.json#performance"
            && error.message.contains("leave score axes unpopulated")
    }));
}

#[test]
fn benchmark_pack_validation_rejects_duplicate_file_entries() {
    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_f_duplicate_file_entry")
        .write_to(dir.path())
        .expect("valid local pack should write");

    let reader = BenchmarkPackReader::read(dir.path()).expect("pack should load");
    let mut manifest = reader.manifest().clone();
    let duplicate_file = manifest
        .files
        .iter()
        .find(|file| file.role == BenchmarkPackFileRole::ScoreReport)
        .expect("pack should include score report file entry")
        .clone();
    manifest.files.push(duplicate_file);
    manifest.summary.score_report_count = 2;
    let manifest_bytes =
        serde_json::to_vec_pretty(&manifest).expect("pack manifest should serialize");
    std::fs::write(dir.path().join("pack.json"), manifest_bytes)
        .expect("test should be able to rewrite pack manifest");

    let reader = BenchmarkPackReader::read(dir.path()).expect("tampered pack should load");
    let validation = reader.validate();

    assert!(!validation.valid);
    assert!(validation.errors.iter().any(|error| {
        error.path == "reports/score_report.json"
            && error
                .message
                .contains("duplicate benchmark pack file entry")
    }));
}

#[test]
fn benchmark_pack_validation_rejects_stale_manifest_refs_and_ids() {
    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_f_stale_manifest_refs")
        .write_to(dir.path())
        .expect("valid local pack should write");

    let reader = BenchmarkPackReader::read(dir.path()).expect("pack should load");
    let mut manifest = reader.manifest().clone();
    manifest.evidence_ledger_ref = Some("evidence/other-ledger.json".to_string());
    manifest
        .generated_instance_ids
        .push("fake-instance".to_string());
    manifest
        .replay_result_ids
        .push("fake-replay-result".to_string());
    let manifest_bytes =
        serde_json::to_vec_pretty(&manifest).expect("pack manifest should serialize");
    std::fs::write(dir.path().join("pack.json"), manifest_bytes)
        .expect("test should be able to rewrite pack manifest");

    let reader = BenchmarkPackReader::read(dir.path()).expect("tampered pack should load");
    let validation = reader.validate();

    assert!(!validation.valid);
    assert!(validation
        .errors
        .iter()
        .any(|error| error.path == "pack.json#evidence_ledger_ref"));
    assert!(validation
        .errors
        .iter()
        .any(|error| error.path == "pack.json#generated_instance_ids"));
    assert!(validation
        .errors
        .iter()
        .any(|error| error.path == "pack.json#replay_result_ids"));
}

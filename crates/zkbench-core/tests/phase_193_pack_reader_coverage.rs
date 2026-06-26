use std::path::Path;

use tempfile::tempdir;
use zkbench_core::{
    compute_artifact_digest_bytes, ArtifactDigest, BenchmarkPackFile, BenchmarkPackFileRole,
    BenchmarkPackManifest, BenchmarkPackReader, BenchmarkPackWriter, ClaimBoundary,
};

fn write_manifest(root: &Path, manifest: &BenchmarkPackManifest) {
    let bytes = serde_json::to_vec_pretty(manifest).expect("pack manifest serializes");
    std::fs::write(root.join("pack.json"), bytes).expect("pack manifest writes");
}

fn digest(bytes: &[u8], role: BenchmarkPackFileRole) -> ArtifactDigest {
    compute_artifact_digest_bytes(
        bytes,
        Some(role.artifact_kind()),
        Some(role.artifact_role()),
    )
}

fn fresh_pack_manifest(root: &Path, pack_id: &str) -> BenchmarkPackManifest {
    BenchmarkPackWriter::new(pack_id)
        .write_to(root)
        .expect("valid local pack writes")
}

fn assert_error_contains(errors: &[zkbench_core::BenchmarkPackValidationError], needle: &str) {
    assert!(
        errors
            .iter()
            .any(|error| error.path.contains(needle) || error.message.contains(needle)),
        "expected validation error containing {needle:?}, got {errors:?}"
    );
}

#[test]
fn phase_193_pack_reader_reports_missing_malformed_and_invalid_manifest_inputs() {
    let dir = tempdir().expect("tempdir is available");
    let error = BenchmarkPackReader::read(dir.path()).expect_err("missing pack.json is rejected");
    assert!(error.to_string().contains("pack.json"));

    std::fs::write(dir.path().join("pack.json"), "{not json")
        .expect("malformed pack manifest writes");
    let error = BenchmarkPackReader::read(dir.path()).expect_err("malformed pack.json is rejected");
    assert!(error.to_string().contains("benchmark_pack.pack_json"));

    let valid_dir = tempdir().expect("tempdir is available");
    let manifest = fresh_pack_manifest(valid_dir.path(), "phase_193_invalid_manifest_path");
    let mut invalid_manifest = manifest.clone();
    invalid_manifest.files[0].relative_path = "../escape.json".to_string();
    write_manifest(valid_dir.path(), &invalid_manifest);

    let reader =
        BenchmarkPackReader::read(valid_dir.path()).expect("syntactically valid pack loads");
    let validation = reader.validate();

    assert!(!validation.valid);
    assert_error_contains(&validation.errors, "pack.json");
    assert_error_contains(&validation.errors, "../escape.json");
}

#[test]
fn phase_193_pack_reader_rejects_invalid_direct_ledger_and_score_report_paths() {
    let dir = tempdir().expect("tempdir is available");
    let manifest = fresh_pack_manifest(dir.path(), "phase_193_invalid_direct_paths");

    let mut invalid_ledger_manifest = manifest.clone();
    let ledger_file = invalid_ledger_manifest
        .files
        .iter_mut()
        .find(|file| file.role == BenchmarkPackFileRole::EvidenceLedger)
        .expect("default pack includes evidence ledger file");
    ledger_file.relative_path = "../ledger.json".to_string();
    write_manifest(dir.path(), &invalid_ledger_manifest);
    let reader = BenchmarkPackReader::read(dir.path()).expect("pack loads");
    let error = reader
        .load_evidence_ledger()
        .expect_err("invalid evidence ledger path is rejected");
    assert!(error.to_string().contains("../ledger.json"));

    let mut invalid_score_manifest = manifest;
    let score_file = invalid_score_manifest
        .files
        .iter_mut()
        .find(|file| file.role == BenchmarkPackFileRole::ScoreReport)
        .expect("default pack includes score report file");
    score_file.relative_path = "/absolute-score.json".to_string();
    write_manifest(dir.path(), &invalid_score_manifest);
    let reader = BenchmarkPackReader::read(dir.path()).expect("pack loads");
    let error = reader
        .load_score_report()
        .expect_err("invalid score report path is rejected");
    assert!(error.to_string().contains("/absolute-score.json"));
}

#[test]
fn phase_193_pack_reader_treats_missing_optional_files_as_nonblocking() {
    let dir = tempdir().expect("tempdir is available");
    let mut manifest = fresh_pack_manifest(dir.path(), "phase_193_optional_missing");

    manifest.files.push(BenchmarkPackFile {
        relative_path: "optional/missing.md".to_string(),
        role: BenchmarkPackFileRole::Readme,
        digest: digest(b"missing optional", BenchmarkPackFileRole::Readme),
        required: false,
        notes: vec!["not official benchmark evidence".to_string()],
    });
    write_manifest(dir.path(), &manifest);

    let reader = BenchmarkPackReader::read(dir.path()).expect("pack loads");
    let validation = reader.validate();

    assert!(
        validation.valid,
        "optional missing file should not invalidate pack: {:?}",
        validation.errors
    );
}

#[test]
fn phase_193_pack_reader_reports_missing_required_files() {
    let dir = tempdir().expect("tempdir is available");
    let mut manifest = fresh_pack_manifest(dir.path(), "phase_193_required_missing");

    manifest.files.push(BenchmarkPackFile {
        relative_path: "required/missing.md".to_string(),
        role: BenchmarkPackFileRole::Readme,
        digest: digest(b"missing required", BenchmarkPackFileRole::Readme),
        required: true,
        notes: Vec::new(),
    });
    write_manifest(dir.path(), &manifest);

    let reader = BenchmarkPackReader::read(dir.path()).expect("pack loads");
    let validation = reader.validate();

    assert!(!validation.valid);
    assert_error_contains(&validation.errors, "required/missing.md");
}

#[test]
fn phase_193_pack_reader_reports_missing_and_malformed_evidence_ledger() {
    let dir = tempdir().expect("tempdir is available");
    let manifest = fresh_pack_manifest(dir.path(), "phase_193_bad_ledger");

    let mut missing_ref_manifest = manifest.clone();
    missing_ref_manifest
        .files
        .retain(|file| file.role != BenchmarkPackFileRole::EvidenceLedger);
    missing_ref_manifest.evidence_ledger_ref = None;
    write_manifest(dir.path(), &missing_ref_manifest);
    let reader = BenchmarkPackReader::read(dir.path()).expect("pack loads");
    assert!(reader
        .load_evidence_ledger()
        .expect("missing ledger file role returns none")
        .is_none());
    let validation = reader.validate();
    assert!(!validation.valid);
    assert_error_contains(&validation.errors, "evidence/ledger.json");
    assert_error_contains(&validation.errors, "pack.json#evidence_ledger_ref");

    let mut unreadable_manifest = manifest.clone();
    std::fs::remove_file(dir.path().join("evidence/ledger.json"))
        .expect("ledger file can be removed");
    write_manifest(dir.path(), &unreadable_manifest);
    let reader = BenchmarkPackReader::read(dir.path()).expect("pack loads");
    let error = reader
        .load_evidence_ledger()
        .expect_err("missing required ledger is rejected by direct load");
    assert!(error.to_string().contains("evidence/ledger.json"));

    let malformed = b"{not ledger json";
    std::fs::write(dir.path().join("evidence/ledger.json"), malformed)
        .expect("malformed ledger writes");
    let ledger_file = unreadable_manifest
        .files
        .iter_mut()
        .find(|file| file.role == BenchmarkPackFileRole::EvidenceLedger)
        .expect("ledger file entry exists");
    ledger_file.digest = digest(malformed, BenchmarkPackFileRole::EvidenceLedger);
    write_manifest(dir.path(), &unreadable_manifest);
    let reader = BenchmarkPackReader::read(dir.path()).expect("pack loads");
    let error = reader
        .load_evidence_ledger()
        .expect_err("malformed ledger is rejected");
    assert!(error.to_string().contains("benchmark_pack.evidence_ledger"));
    let validation = reader.validate();
    assert!(!validation.valid);
    assert_error_contains(&validation.errors, "benchmark_pack.evidence_ledger");
}

#[test]
fn phase_193_pack_reader_reports_missing_and_malformed_score_report() {
    let dir = tempdir().expect("tempdir is available");
    let mut manifest = fresh_pack_manifest(dir.path(), "phase_193_bad_score_report");

    std::fs::remove_file(dir.path().join("reports/score_report.json"))
        .expect("score report file can be removed");
    write_manifest(dir.path(), &manifest);
    let reader = BenchmarkPackReader::read(dir.path()).expect("pack loads");
    let error = reader
        .load_score_report()
        .expect_err("missing score report is rejected by direct load");
    assert!(error.to_string().contains("reports/score_report.json"));
    let validation = reader.validate();
    assert!(!validation.valid);
    assert_error_contains(&validation.errors, "reports/score_report.json");

    let malformed = b"{not score json";
    std::fs::write(dir.path().join("reports/score_report.json"), malformed)
        .expect("malformed score report writes");
    let score_file = manifest
        .files
        .iter_mut()
        .find(|file| file.role == BenchmarkPackFileRole::ScoreReport)
        .expect("score report file entry exists");
    score_file.digest = digest(malformed, BenchmarkPackFileRole::ScoreReport);
    write_manifest(dir.path(), &manifest);

    let reader = BenchmarkPackReader::read(dir.path()).expect("pack loads");
    let error = reader
        .load_score_report()
        .expect_err("malformed score report is rejected");
    assert!(error.to_string().contains("benchmark_pack.score_report"));
    let validation = reader.validate();
    assert!(!validation.valid);
    assert_error_contains(&validation.errors, "reports/score_report.json");
}

#[test]
fn phase_193_pack_reader_reports_claim_boundary_and_remaining_summary_drifts() {
    let dir = tempdir().expect("tempdir is available");
    let mut manifest = fresh_pack_manifest(dir.path(), "phase_193_boundary_and_counts");

    manifest.claim_boundary = ClaimBoundary::Level2ReproducibleBenchmarkArtifact;
    manifest.summary.mutated_instance_count = 2;
    manifest.summary.replay_manifest_count = 2;
    manifest.summary.replay_result_count = 1;
    manifest.mutation_ids.push("missing-mutation".to_string());
    manifest
        .replay_manifest_ids
        .push("missing-replay-manifest".to_string());
    write_manifest(dir.path(), &manifest);

    let reader = BenchmarkPackReader::read(dir.path()).expect("pack loads");
    let validation = reader.validate();

    assert!(!validation.valid);
    assert_error_contains(
        &validation.errors,
        "pack.json#summary.mutated_instance_count",
    );
    assert_error_contains(
        &validation.errors,
        "pack.json#summary.replay_manifest_count",
    );
    assert_error_contains(&validation.errors, "pack.json#summary.replay_result_count");
    assert_error_contains(&validation.errors, "pack.json#mutation_ids");
    assert_error_contains(&validation.errors, "pack.json#replay_manifest_ids");
    assert_error_contains(&validation.errors, "exceeds Level1LocalReplay");
}

#[test]
fn phase_193_pack_reader_allows_explicit_safe_nonclaim_notes() {
    let dir = tempdir().expect("tempdir is available");
    let mut manifest = fresh_pack_manifest(dir.path(), "phase_193_safe_nonclaims");
    let safe_notes = vec![
        "not official benchmark evidence".to_string(),
        "not official benchmark result".to_string(),
        "no official benchmark evidence".to_string(),
        "no official benchmark result".to_string(),
        "does not create official benchmark evidence".to_string(),
        "does not create official benchmark result".to_string(),
        "no external backend artifacts, proof-system results, or formal evidence are included"
            .to_string(),
    ];
    manifest.notes.extend(safe_notes.clone());
    let readme_file = manifest
        .files
        .iter_mut()
        .find(|file| file.role == BenchmarkPackFileRole::Readme)
        .expect("readme file entry exists");
    readme_file.notes.extend(safe_notes);
    write_manifest(dir.path(), &manifest);

    let reader = BenchmarkPackReader::read(dir.path()).expect("pack loads");
    let validation = reader.validate();

    assert!(
        validation.valid,
        "safe nonclaim notes should remain valid: {:?}",
        validation.errors
    );
}

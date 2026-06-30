use tempfile::tempdir;
use zkbench_core::{
    build_local_replay_manifest_for_instance, generate_instance, run_local_replay, ClaimBoundary,
    EvidenceAppendPolicy, EvidenceClass, EvidenceLedger, EvidenceRecord, GeneratorConfig,
    InstanceParams, ProvenanceRecord,
};

fn local_record(source: &str) -> EvidenceRecord {
    EvidenceRecord {
        evidence_class: EvidenceClass::LocalReplay,
        claim_boundary: ClaimBoundary::Level1LocalReplay,
        provenance: ProvenanceRecord {
            source: source.to_string(),
            captured_at: None,
            command: None,
            notes: Vec::new(),
        },
        artifact_digest: None,
        notes: Vec::new(),
        backend_target: None,
    }
}

#[test]
fn empty_evidence_ledger_validates() {
    let ledger = EvidenceLedger::new();
    let validation = ledger.validate();
    assert!(validation.valid);
    assert_eq!(validation.summary.entry_count, 0);
}

#[test]
fn default_evidence_ledger_matches_new() {
    assert_eq!(EvidenceLedger::default(), EvidenceLedger::new());
}

#[test]
fn evidence_ledger_persists_replay_records_and_validates_chain() {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(41),
        InstanceParams::default(),
    )
    .expect("generated instance should be available");
    let manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    let result = run_local_replay(&manifest).expect("local replay should run");

    let mut ledger = EvidenceLedger::new();
    ledger
        .append_replay_result(&result)
        .expect("replay evidence should append");
    assert!(ledger
        .entries
        .iter()
        .all(|entry| entry.evidence_record.claim_boundary <= ClaimBoundary::Level1LocalReplay));
    assert!(ledger.validate().valid);

    let dir = tempdir().expect("tempdir should be available for ledger persistence");
    let path = dir.path().join("ledger.json");
    ledger.save_json(&path).expect("ledger should save as JSON");
    let loaded = EvidenceLedger::load_json(&path).expect("ledger should load from JSON");

    assert_eq!(ledger, loaded);
    assert!(loaded.validate().valid);
    assert_eq!(loaded.summary.entry_count, result.evidence_records.len());
    assert!(loaded
        .summary
        .evidence_class_counts
        .iter()
        .any(|count| count.name == "LocalReplay"));
    assert!(loaded
        .summary
        .claim_boundary_counts
        .iter()
        .any(|count| count.name == "Level1LocalReplay"));
}

#[test]
fn evidence_ledger_json_file_errors_are_reported() {
    let dir = tempdir().expect("tempdir should be available for file error checks");
    let ledger = EvidenceLedger::new();
    let directory_path = dir.path();

    let save_error = ledger
        .save_json(directory_path)
        .expect_err("saving JSON to a directory should fail");
    assert!(save_error
        .to_string()
        .contains(directory_path.to_string_lossy().as_ref()));

    let missing_path = dir.path().join("missing-ledger.json");
    let load_error =
        EvidenceLedger::load_json(&missing_path).expect_err("missing ledger should fail to load");
    assert!(load_error
        .to_string()
        .contains(missing_path.to_string_lossy().as_ref()));

    let malformed_path = dir.path().join("malformed-ledger.json");
    std::fs::write(&malformed_path, b"{not-json").expect("malformed fixture should write");
    let malformed_error =
        EvidenceLedger::load_json(&malformed_path).expect_err("malformed ledger should fail");
    assert!(malformed_error
        .to_string()
        .contains("evidence_ledger.load_json"));
}

#[test]
fn evidence_ledger_detects_tampered_evidence_record() {
    let instance = generate_instance(
        GeneratorConfig::baseline_fsm().seed(43),
        InstanceParams::default(),
    )
    .expect("generated instance should be available");
    let manifest =
        build_local_replay_manifest_for_instance(&instance).expect("manifest should build");
    let result = run_local_replay(&manifest).expect("local replay should run");

    let mut ledger = EvidenceLedger::new();
    ledger
        .append_replay_result(&result)
        .expect("replay evidence should append");
    ledger.entries[0]
        .evidence_record
        .notes
        .push("tampered after digest".to_string());

    let validation = ledger.validate();
    assert!(!validation.valid);
    assert!(validation
        .errors
        .iter()
        .any(|error| error.message.contains("digest mismatch")));
}

#[test]
fn evidence_ledger_detects_sequence_previous_digest_and_summary_drift() {
    let mut ledger = EvidenceLedger::new();
    ledger
        .append(local_record("phase-239-first"))
        .expect("first record should append");
    ledger
        .append(local_record("phase-239-second"))
        .expect("second record should append");

    ledger.entries[0].sequence_number = 7;
    ledger.entries[1].previous_digest = ledger.entries[1].entry_digest.clone().into();
    ledger.summary.entry_count = 99;

    let validation = ledger.validate();

    assert!(!validation.valid);
    assert!(validation
        .errors
        .iter()
        .any(|error| error.message.contains("sequence number 7")));
    assert!(validation
        .errors
        .iter()
        .any(|error| error.message.contains("previous digest")));
    assert!(validation
        .errors
        .iter()
        .any(|error| error.message.contains("cached summary")));
}

#[test]
fn evidence_ledger_rejects_level2_actual_evidence_in_phase_f() {
    let mut ledger = EvidenceLedger::new();
    let record = EvidenceRecord {
        evidence_class: EvidenceClass::ReproducibleBenchmarkArtifact,
        claim_boundary: ClaimBoundary::Level2ReproducibleBenchmarkArtifact,
        provenance: ProvenanceRecord {
            source: "future-placeholder".to_string(),
            captured_at: None,
            command: None,
            notes: vec!["not actual Phase F evidence".to_string()],
        },
        artifact_digest: None,
        notes: Vec::new(),
        backend_target: None,
    };

    let error = ledger
        .append(record)
        .expect_err("Phase F ledger must reject actual Level2 evidence");
    assert!(error.to_string().contains("exceeds Level1LocalReplay"));
}

#[test]
fn evidence_ledger_allows_explicit_nonclaim_language() {
    let mut ledger = EvidenceLedger::new();
    let mut record = local_record("phase-239-nonclaim");
    record
        .notes
        .push("local replay only; not official benchmark evidence".to_string());
    record
        .provenance
        .notes
        .push("does not create official benchmark result".to_string());

    ledger
        .append(record)
        .expect("nonclaim record should append");
    ledger
        .notes
        .push("no official benchmark evidence is created here".to_string());
    ledger.entries[0]
        .notes
        .push("not official benchmark result".to_string());

    assert!(ledger.validate().valid);
}

#[test]
fn evidence_ledger_rejects_forbidden_claim_text_in_notes() {
    let mut ledger = EvidenceLedger::new();
    let record = EvidenceRecord {
        evidence_class: EvidenceClass::LocalReplay,
        claim_boundary: ClaimBoundary::Level1LocalReplay,
        provenance: ProvenanceRecord {
            source: "local-replay".to_string(),
            captured_at: None,
            command: None,
            notes: vec!["this provenance is official benchmark evidence".to_string()],
        },
        artifact_digest: None,
        notes: vec!["this record is a machine-checked proof".to_string()],
        backend_target: None,
    };

    ledger.append(record).expect("local record should append");
    ledger
        .notes
        .push("this ledger is an official zk-harness result".to_string());
    ledger.entries[0]
        .notes
        .push("this entry is performance evidence".to_string());

    let validation = ledger.validate();

    assert!(!validation.valid);
    assert!(validation
        .errors
        .iter()
        .any(|error| error.message.contains("ledger.notes[1]")));
    assert!(validation
        .errors
        .iter()
        .any(|error| error.message.contains("ledger.entries[0].notes[0]")));
    assert!(validation.errors.iter().any(|error| error
        .message
        .contains("ledger.entries[0].evidence_record.notes[0]")));
    assert!(validation.errors.iter().any(|error| error
        .message
        .contains("ledger.entries[0].evidence_record.provenance.notes[0]")));
}

#[test]
fn future_metadata_policy_does_not_make_level2_actual_evidence_valid() {
    let mut ledger = EvidenceLedger::new();
    let record = EvidenceRecord {
        evidence_class: EvidenceClass::ReproducibleBenchmarkArtifact,
        claim_boundary: ClaimBoundary::Level2ReproducibleBenchmarkArtifact,
        provenance: ProvenanceRecord {
            source: "future-metadata-placeholder".to_string(),
            captured_at: None,
            command: None,
            notes: vec!["future metadata only; not accepted Phase F evidence".to_string()],
        },
        artifact_digest: None,
        notes: vec!["must remain invalid as actual evidence".to_string()],
        backend_target: None,
    };

    ledger
        .append_with_policy(record, EvidenceAppendPolicy::AllowFutureMetadata)
        .expect("future metadata policy records the candidate for validation");

    let validation = ledger.validate();
    assert!(!validation.valid);
    assert!(validation
        .errors
        .iter()
        .any(|error| error.message.contains("exceeds Level1LocalReplay")));
}

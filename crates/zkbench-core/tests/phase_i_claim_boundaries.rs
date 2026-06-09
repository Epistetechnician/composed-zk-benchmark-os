use std::fs;
use std::path::Path;

use zkbench_core::{
    create_evidence_append_proposal, deserialize_external_result_candidate_json,
    import_synthetic_result_candidate_json, normalize_synthetic_result_candidate,
    quarantine_synthetic_result_candidate, validate_synthetic_result_candidate, ClaimBoundary,
    EvidenceAppendProposalLedger, QuarantineReason, ResultCandidateArtifactResolver,
};

fn resolver() -> ResultCandidateArtifactResolver {
    ResultCandidateArtifactResolver::from_in_memory_bytes(vec![(
        "artifacts/synthetic_metric_source.json".to_string(),
        b"synthetic metric source v1\n".to_vec(),
    )])
}

#[test]
fn phase_i_artifacts_remain_level0_design_notes() {
    let candidate = deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_valid.json"
    ))
    .expect("fixture should parse");
    let resolver = resolver();
    let validation = validate_synthetic_result_candidate(&candidate, &resolver);
    let draft = normalize_synthetic_result_candidate(&candidate, &validation, &resolver)
        .expect("valid candidate should normalize");
    let proposal = create_evidence_append_proposal(&draft).expect("proposal should build");
    let mut ledger = EvidenceAppendProposalLedger::new();
    ledger
        .append(proposal.clone())
        .expect("proposal append should work");
    let bundle = import_synthetic_result_candidate_json(
        include_str!("fixtures/synthetic_result_candidate_valid.json"),
        &resolver,
    )
    .expect("valid candidate should import");

    assert_eq!(validation.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(draft.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(
        proposal.proposed_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
    assert_eq!(bundle.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert_eq!(
        ledger.entries[0].proposal.proposed_claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
}

#[test]
fn official_claim_candidate_is_quarantined_not_normalized() {
    let candidate = deserialize_external_result_candidate_json(include_str!(
        "fixtures/synthetic_result_candidate_official_claim.json"
    ))
    .expect("fixture should parse");
    let validation = validate_synthetic_result_candidate(&candidate, &resolver());
    let manifest = quarantine_synthetic_result_candidate(&candidate, &validation);

    assert!(!validation.valid);
    assert!(validation.official_claim_detection.detected);
    assert_eq!(
        manifest.entries[0].reason,
        QuarantineReason::OfficialClaimDetected
    );
    assert_eq!(
        manifest.entries[0].claim_boundary,
        ClaimBoundary::Level0DesignNote
    );
}

#[test]
fn phase_i_source_contains_no_process_command_api() {
    let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let source = read_source_tree(&manifest_dir.join("src/external_runner"));

    assert!(!source.contains("std::process::Command"));
    assert!(!source.contains("Command::new"));
}

#[test]
fn synthetic_fixtures_do_not_use_external_performance_metric_keys() {
    let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let fixture_dir = manifest_dir.join("tests/fixtures");
    let source = read_source_tree(&fixture_dir);

    assert!(!source.contains("prover_time"));
    assert!(!source.contains("verifier_time"));
    assert!(!source.contains("proof_size"));
    assert!(!source.contains("memory_usage"));
    assert!(!source.contains("constraint_count"));
}

fn read_source_tree(root: &Path) -> String {
    let mut combined = String::new();
    read_source_tree_into(root, &mut combined);
    combined
}

fn read_source_tree_into(path: &Path, combined: &mut String) {
    if path.is_file() {
        let text = fs::read_to_string(path).expect("source file should be readable");
        combined.push_str(&text);
        combined.push('\n');
        return;
    }
    for entry in fs::read_dir(path).expect("source directory should be readable") {
        let entry = entry.expect("source directory entry should be readable");
        read_source_tree_into(&entry.path(), combined);
    }
}

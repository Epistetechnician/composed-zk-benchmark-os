use zkbench_core::{
    build_failure_corpus_entry, deserialize_failure_corpus_index_json,
    serialize_failure_corpus_index_json, validate_failure_corpus_index, ClaimBoundary,
    FailureCorpus, FailureCorpusEntryInput, FailureCorpusKind, FailureTriageStatus, FamilyKind,
    GeneratorTunables, MutationClass, SoakShardId,
};

#[test]
fn failure_corpus_starts_empty_and_validates() {
    let corpus = FailureCorpus::empty("empty_failure_corpus");
    validate_failure_corpus_index(&corpus.index).expect("empty corpus should validate");
    assert_eq!(corpus.index.summary.entry_count, 0);
    assert_eq!(corpus.index.claim_boundary, ClaimBoundary::Level0DesignNote);
}

#[test]
fn simulated_failures_create_reproducible_entries() {
    let mut corpus = FailureCorpus::empty("simulated_failure_corpus");
    let mutation = build_failure_corpus_entry(FailureCorpusEntryInput {
        shard_id: SoakShardId::from_index(0),
        case_id: "case_mutation".to_string(),
        family_kind: FamilyKind::BaselineFsm,
        generator_seed: 7,
        tunables: GeneratorTunables::default(),
        mutation_class: Some(MutationClass::MissingConstraints),
        trace_id: None,
        failure_kind: FailureCorpusKind::MutationFailure,
        local_error_summary: "simulated mutation failure".to_string(),
    });
    let replay = build_failure_corpus_entry(FailureCorpusEntryInput {
        shard_id: SoakShardId::from_index(0),
        case_id: "case_replay".to_string(),
        family_kind: FamilyKind::BaselineFsm,
        generator_seed: 8,
        tunables: GeneratorTunables::default(),
        mutation_class: None,
        trace_id: Some("trace_a".to_string()),
        failure_kind: FailureCorpusKind::ReplayFailure,
        local_error_summary: "simulated replay failure".to_string(),
    });
    let boundary = build_failure_corpus_entry(FailureCorpusEntryInput {
        shard_id: SoakShardId::from_index(0),
        case_id: "case_boundary".to_string(),
        family_kind: FamilyKind::BaselineFsm,
        generator_seed: 9,
        tunables: GeneratorTunables::default(),
        mutation_class: None,
        trace_id: None,
        failure_kind: FailureCorpusKind::ClaimBoundaryViolation,
        local_error_summary: "simulated boundary violation".to_string(),
    });
    corpus.push(mutation);
    corpus.push(replay);
    corpus.push(boundary);

    validate_failure_corpus_index(&corpus.index).expect("corpus should validate");
    assert_eq!(corpus.index.summary.entry_count, 3);
    assert_eq!(corpus.index.summary.mutation_failure_count, 1);
    assert_eq!(corpus.index.summary.replay_failure_count, 1);
    assert_eq!(corpus.index.summary.claim_boundary_violation_count, 1);
    assert!(corpus.index.entries.iter().all(|entry| {
        entry.claim_boundary == ClaimBoundary::Level0DesignNote
            && entry.triage_status == FailureTriageStatus::New
            && !entry.minimization_hints.is_empty()
            && entry.reproduction_manifest.claim_boundary == ClaimBoundary::Level0DesignNote
    }));
}

#[test]
fn failure_corpus_roundtrips_and_does_not_claim_acceptance() {
    let mut corpus = FailureCorpus::empty("roundtrip_failure_corpus");
    corpus.push(build_failure_corpus_entry(FailureCorpusEntryInput {
        shard_id: SoakShardId::from_index(1),
        case_id: "case_roundtrip".to_string(),
        family_kind: FamilyKind::BoundedCounterLoop,
        generator_seed: 11,
        tunables: GeneratorTunables::default(),
        mutation_class: Some(MutationClass::BadCounters),
        trace_id: Some("trace_b".to_string()),
        failure_kind: FailureCorpusKind::ReplayFailure,
        local_error_summary: "simulated local replay failure".to_string(),
    }));
    let json = serialize_failure_corpus_index_json(&corpus.index).expect("corpus should serialize");
    assert!(!json.contains("accepted evidence\":true"));
    assert!(json.contains("Failure corpus entries are reproduction aids"));
    let roundtrip =
        deserialize_failure_corpus_index_json(&json).expect("corpus should deserialize");
    assert_eq!(roundtrip, corpus.index);
}

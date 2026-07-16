use statebook_e2e_harness::{
    labeled_semantic_pairs_v1, replay_semantic_equivalence_corpus_v1, EquivalenceLabelV1,
};

#[test]
fn labeled_corpus_includes_equivalent_and_distinct_pairs() {
    let pairs = labeled_semantic_pairs_v1().expect("pairs");
    let equivalent = pairs
        .iter()
        .filter(|pair| pair.label == EquivalenceLabelV1::Equivalent)
        .count();
    let distinct = pairs
        .iter()
        .filter(|pair| pair.label == EquivalenceLabelV1::Distinct)
        .count();
    assert!(
        equivalent >= 2,
        "expected lineage + profile equivalent labels"
    );
    assert_eq!(distinct, 27, "expected all P1 material mutations");
    assert!(pairs.iter().any(|pair| pair.id == "equiv_lineage_only"));
    assert!(pairs
        .iter()
        .any(|pair| pair.id == "distinct_reference_namespace"));
}

#[test]
fn semantic_equivalence_metrics_are_perfect_on_fixture_corpus() {
    let metrics = replay_semantic_equivalence_corpus_v1().expect("metrics");
    assert_eq!(metrics.false_equivalence_numerator, 0);
    assert_eq!(metrics.precision_numerator, metrics.precision_denominator);
    assert_eq!(metrics.recall_numerator, metrics.recall_denominator);
    assert_eq!(metrics.true_positive, metrics.labeled_equivalent);
    assert_eq!(metrics.true_negative, metrics.labeled_distinct);
    assert_eq!(metrics.false_positive, 0);
    assert_eq!(metrics.false_negative, 0);
}

#[test]
fn false_equivalence_is_impossible_on_material_mutations() {
    let pairs = labeled_semantic_pairs_v1().unwrap();
    for pair in pairs
        .iter()
        .filter(|pair| pair.label == EquivalenceLabelV1::Distinct)
    {
        assert!(
            !pair.predicted_equivalent,
            "{} falsely shared StateKey",
            pair.id
        );
        assert_ne!(pair.left_state_key, pair.right_state_key, "{}", pair.id);
    }
}

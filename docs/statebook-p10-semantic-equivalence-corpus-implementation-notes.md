# Statebook P10 Semantic Equivalence Corpus Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p10-semantic-equivalence-corpus`.

## Outcome

`crates/statebook-e2e-harness` now hosts:

- `labeled_semantic_pairs_v1` over lineage-equivalent, profile-version-equivalent,
  and all 27 P1 material-mutation distinct pairs;
- `evaluate_semantic_metrics_v1` / `replay_semantic_equivalence_corpus_v1` with
  fixture-local acceptance: precision=1, recall=1, false-equivalence rate=0.

No P1–P9 crate mutation. No AI oracle. No value moves.

## Local validation evidence

```text
cargo fmt -p statebook-e2e-harness -- --check
cargo test -p statebook-e2e-harness --tests
cargo clippy -p statebook-e2e-harness --all-targets -- -D warnings
```

Sixteen focused harness tests pass after this slice.

## Claim ceiling

Local hermetic labeled-fixture StateKey equivalence metrics only. Not automatic
economic-equivalence discovery, legal fungibility, production thresholds, SOTA,
independent audit, or full security. No value moves.

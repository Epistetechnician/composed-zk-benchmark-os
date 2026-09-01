# Gemma3 FineWeb-Edu replication V5 independent review packet

State slice: `continual-learning-gemma3-fineweb-edu-replication-v5`

Review scope is exact and read-only. The reviewer must read the seven files in
the V5 implementation manifest and recompute all digests. The reviewer must
not load the model, acquire data, execute effects, modify files, or create an
ACCEPT receipt. The caller records the reviewer’s canonical decision only
after the independent response is returned.

Required decision fields:

- `review_decision`: exactly `ACCEPT` or `REJECT`.
- `reviewer`: nonblank independent identity.
- `reviewed_at_utc`: canonical UTC timestamp with second precision.
- `effects_run`: exactly `false`.
- exact protocol, packet, and implementation-manifest SHA-256 values.
- `reviewed_files`: exact implementation file list in contract order.
- exactly these seven findings, all `true`:

  1. `custody_exact_pinned_data_identity`
  2. `fit_assessment_prior_pilot_disjointness`
  3. `locked_configuration_and_paper_target_treatment`
  4. `controls_and_frozen_weight_behavior`
  5. `exact_bootstrap_and_uncertainty_rule`
  6. `aggregate_per_document_retention_and_validator_behavior`
  7. `v1_v2_v3_v4_rejections_preserved_and_prohibited_actions_enforced`

The reviewer must reject if any condition is fail-open, optional through a
public API, dependent on a stale digest, or asserted without independent
recomputation. In particular, inspect these V5-specific gates:

1. Raw, prior, source, corpus, result, and model trees have exact expected
   file sets, reject symlink components and entries, and use exact lexical
   paths. Model manifest equality is checked before tokenizer/model loading.
2. Source validation requires a review receipt; there is no `None` or default
   bypass. The source and prior IDs and complete normalized records are
   re-derived from the two pinned Parquet inputs, with fresh row ranges and
   split disjointness enforced.
3. Corpus parsing recomputes tokenizer IDs from the actual text file and
   enforces all 128 exact 1024-token windows, round-trip equality, source and
   text hashes, and fit/assessment separation.
4. Public CLI modes require explicit roots and bindings. Result validation
   checks every common provenance field, every candidate and locked pair,
   every control configuration, all retained per-document identities, strict
   non-boolean numeric types, and exact aggregate recomputation.
5. Result validation independently loads the reviewed runner only after
   structural checks, recomputes native, zero-alpha, candidates, selected,
   temperature, repeat, parity, metrics, and frozen parameter custody, and
   compares them exactly with the retained result.
6. The native network boundary is mandatory and the Python block covers socket
   connect/send, DNS, URL, child process, shell, and spawn paths. The runner’s
   sandbox re-entry cannot loop or treat an environment flag as proof.
7. Code, protocol, packet, review receipt, source, raw, prior, corpus, and
   model snapshots are asserted immediately before model loading/effects and
   immediately before no-overwrite publication. The publication function
   snapshots every expected staged output path and digest inside its boundary,
   then rechecks the final tree after moves. Publication cannot replace a
   final root or silently clean up a partial final root.
8. The exact bootstrap algorithm uses finite non-boolean values, SHA-256
   counter draws, 10,000 resamples, seed 20260829, nearest-rank endpoints,
   and strict negative mean/upper decision. `(11,4)` is an expected target,
   never a selection override.
9. V1, V2, V3, and V4 rejection records remain untouched and V5 contains no
   forbidden model/data download, training, provider, GiveMeANode, H100,
   benchmark, production, Astral, ledger, or self-modeling path.

An ACCEPT is valid only if all seven named findings are true and the reviewer
finds no material gap. A REJECT remains terminal for V5; no effect execution
or adaptive repair follows it.

# Independent review packet: Gemma3 FineWeb-Edu replication V4

State slice: `continual-learning-gemma3-fineweb-edu-replication-v4`

V1, V2, and V3 remain immutable rejected records. Review V4 only. The reviewer
must not modify any file, access external artifacts, load a model or tokenizer,
run data effects, use network, or mutate an Evidence Ledger.

## Exact review set

Review exactly these seven files:

- `docs/research/continual-learning/151-gemma3-fineweb-edu-replication-v4-protocol.md`
- `docs/research/continual-learning/152-gemma3-fineweb-edu-replication-v4-review-packet.md`
- `experiments/continual_learning/gemma3_fineweb_edu_replication_v4_contract.py`
- `experiments/continual_learning/prepare_gemma3_fineweb_edu_replication_v4.py`
- `experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v4.py`
- `experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v4.py`
- `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_v4.py`

Recompute the protocol SHA-256, packet SHA-256, and implementation-manifest
SHA-256 from the exact bytes. Acceptance is valid only if the receipt contains
the exact seven findings below, all `true`.

## Required receipt

The schema is
`gemma3-fineweb-edu-replication-v4-independent-review`; state slice is
`continual-learning-gemma3-fineweb-edu-replication-v4`; claim ceiling is
`LocalDevelopmentGemma3FineWebEduReplicationV4`. The receipt must contain
`review_status` `ACCEPT` or `REJECT`, reviewer identity, canonical
`reviewed_at_utc` in UTC ending `Z`, `effects_run:false`, protocol, packet, and
implementation hashes, the exact reviewed-file list, and a canonical
`receipt_digest_sha256` self-digest. The digest removes only that field and
uses sorted compact JSON.

Required findings, exactly:

- `custody_exact_pinned_data_identity`
- `fit_assessment_prior_pilot_disjointness`
- `locked_configuration_and_paper_target_treatment`
- `controls_and_frozen_weight_behavior`
- `exact_bootstrap_and_uncertainty_rule`
- `aggregate_per_document_retention_and_validator_behavior`
- `v1_v2_v3_rejections_preserved_and_prohibited_actions_enforced`

## Acceptance standard

Reject if any path can accept altered raw lineage, altered prior content,
cross-split identities, duplicate or unsafe paths, wrong exact roots, model or
dependency substitution, symlink content, stale protocol/packet/code/review
snapshots, missing reviewer identity, malformed timestamp, missing or
post-load model custody checks, missing candidate/control metric, mismatched
temperature or normalization, selected/locked mismatch, nonfinite or
non-exact metrics, incorrect bootstrap, incomplete per-document retention, or
an execution path outside the native offline proof. The validator must
independently recompute corpus token shape, all model controls, aggregates,
parameter custody, and the final decision. Static and hermetic checks only;
do not use V4 external roots or model-bearing execution.

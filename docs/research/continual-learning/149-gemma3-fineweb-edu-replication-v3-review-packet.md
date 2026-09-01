# Independent review packet: Gemma3 FineWeb-Edu replication V3

State slice: `continual-learning-gemma3-fineweb-edu-replication-v3`

V1 and V2 remain rejected and immutable. This packet requests a new review of
V3 only. The reviewer must not modify any file, stage data, load a model,
tokenize corpus data, run effects, contact a provider, or mutate an Evidence
Ledger.

## Files and frozen hash

Review exactly these files:

- `docs/research/continual-learning/148-gemma3-fineweb-edu-replication-v3-protocol.md`
- `docs/research/continual-learning/149-gemma3-fineweb-edu-replication-v3-review-packet.md`
- `experiments/continual_learning/gemma3_fineweb_edu_replication_v3_contract.py`
- `experiments/continual_learning/prepare_gemma3_fineweb_edu_replication_v3.py`
- `experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v3.py`
- `experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v3.py`
- `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_v3.py`

Protocol SHA-256: `5c9c8e0b6ede43bde9fa66a98fb515b597fafa2f3ebcd811c1925ca5a457b8f7`

The reviewer must recompute the protocol hash, packet hash, and implementation
manifest hash. The canonical receipt must contain `review_status` `ACCEPT` or
`REJECT`; acceptance is valid only when all required findings are true.

## Required receipt fields

The receipt schema is
`gemma3-fineweb-edu-replication-v3-independent-review`, with state slice
`continual-learning-gemma3-fineweb-edu-replication-v3`, claim ceiling
`LocalDevelopmentGemma3FineWebEduReplicationV3`, reviewer identity,
`reviewed_at_utc`, `effects_run:false`, protocol/packet/implementation hashes,
and a canonical self-digest field `receipt_digest_sha256`.

Its `findings` object must contain exactly these seven keys, all `true` for
`ACCEPT`:

- `custody_exact_pinned_data_identity`
- `fit_assessment_prior_pilot_disjointness`
- `locked_configuration_and_paper_target_treatment`
- `controls_and_frozen_weight_behavior`
- `exact_bootstrap_and_uncertainty_rule`
- `aggregate_per_document_retention_and_validator_behavior`
- `v1_v2_rejections_preserved_and_prohibited_actions_enforced`

The receipt's self-digest is SHA-256 of the UTF-8 canonical JSON object after
removing `receipt_digest_sha256`, with sorted keys and compact separators.

## Review standard

Reject if any validator can accept a corpus with altered token count, duplicate
or cross-split paths, wrong source row, prior-pilot document, wrong model path,
symlink, altered protocol/packet, missing reviewer identity, stale review
snapshot, mismatched selected/locked pair, missing control metrics, changed
model-parameter digest, nonfinite metric, or incorrect bootstrap. Pure/unit
and static checks only; no V3 external artifact or model-bearing execution.

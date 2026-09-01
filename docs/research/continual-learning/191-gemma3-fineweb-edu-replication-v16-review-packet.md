# Gemma3 FineWeb-Edu replication V16 independent-review packet

State slice: `continual-learning-gemma3-fineweb-edu-replication-v16`.

Read exactly these seven files and no others:

1. `docs/research/continual-learning/190-gemma3-fineweb-edu-replication-v16-protocol.md`
2. `docs/research/continual-learning/191-gemma3-fineweb-edu-replication-v16-review-packet.md`
3. `experiments/continual_learning/gemma3_fineweb_edu_replication_v16_contract.py`
4. `experiments/continual_learning/prepare_gemma3_fineweb_edu_replication_v16.py`
5. `experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v16.py`
6. `experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v16.py`
7. `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_v16.py`

Do not edit, create, delete, stage, format, or mutate any file. Do not access
external `/Volumes/PrimaryED` artifacts or model contents. Do not load a
model/tokenizer, acquire data, use network, run effects, or mutate any ledger.

Recompute the protocol SHA-256, packet SHA-256, and exact implementation
manifest SHA-256. Return one valid JSON object with reviewer identity,
canonical UTC `reviewed_at_utc`, `effects_run:false`, the three hashes, exactly
these seven finding keys each explicitly set to `true` or `false`,
`material_findings`, and `review_decision` exactly `ACCEPT` only if every gate
is closed:

- `custody_exact_pinned_data_identity`
- `fit_assessment_prior_pilot_disjointness`
- `locked_configuration_and_paper_target_treatment`
- `controls_and_frozen_weight_behavior`
- `exact_bootstrap_and_uncertainty_rule`
- `aggregate_per_document_retention_and_validator_behavior`
- `v1_v2_v3_v4_rejections_preserved_and_prohibited_actions_enforced`

The V16 review must verify that:

- The V14 protocol, packet, `ACCEPT` receipt, and stale-review failure record
  are pinned in history, and the V15 protocol, packet, and parent-authored
  rejection closure are also pinned. Neither V14 nor V15 approval is current
  V16 approval; no old scientific artifact is reused.
- The fresh source interval is `[18432,34816)` per pinned shard and is
  disjoint from the prior pilot `[0,2048)` and discarded V14 interval
  `[2048,18432)`.
- The protocol digest in the V16 contract matches the protocol file and the
  implementation manifest covers exactly these seven current files.
- The BF16 custody repair is preserved, with qualified dtype recognition and
  materialized float32 conversion used only for representation.
- Candidate selection, controls, frozen model behavior, canonical
  per-document retention, and nearest-rank bootstrap are all fail-closed and
  independently rederived.
- The source, corpus, and result publication helper performs a post-move
  code/input custody check and rolls back the tentative final root on failure.
- The independent validator does not import the runner or call runner
  parity/evaluation/recurrence functions; its measurement seam is local and
  separately executable.
- Review ordering, native network denial, exact external paths, prohibited
  actions, and terminal `NoCandidate` handling are mechanically enforced.

The reviewer must not require or synthesize undocumented V2–V6 rejection
receipts. The parent creates the V16 receipt only after a valid independent
`ACCEPT`. A rejection or malformed report is not acceptance.

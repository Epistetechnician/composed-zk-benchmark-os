# Gemma3 FineWeb-Edu replication V17 independent-review packet

State slice: `continual-learning-gemma3-fineweb-edu-replication-v17`.

Read exactly these seven files and no others:

1. `docs/research/continual-learning/193-gemma3-fineweb-edu-replication-v17-protocol.md`
2. `docs/research/continual-learning/194-gemma3-fineweb-edu-replication-v17-review-packet.md`
3. `experiments/continual_learning/gemma3_fineweb_edu_replication_v17_contract.py`
4. `experiments/continual_learning/prepare_gemma3_fineweb_edu_replication_v17.py`
5. `experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v17.py`
6. `experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v17.py`
7. `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_v17.py`

Do not edit, create, delete, stage, format, or mutate any file. Do not access
external `/Volumes/PrimaryED` artifacts or model contents. Do not load a
model/tokenizer, acquire data, use network, run effects, or mutate any ledger.

Recompute the protocol SHA-256, packet SHA-256, and the implementation
manifest SHA-256 over the seven files in the contract's declared order. Return
exactly one syntactically valid JSON object and no prose with nonempty
`reviewer`, canonical UTC `reviewed_at_utc`, `effects_run:false`, the three
hashes, exactly the seven boolean finding keys below, `material_findings`, and
`review_decision`. Every field and every finding must have an explicit JSON
value. Use `ACCEPT` only if all findings are true and all hashes match.

Required finding keys:

- `custody_exact_pinned_data_identity`
- `fit_assessment_prior_pilot_disjointness`
- `locked_configuration_and_paper_target_treatment`
- `controls_and_frozen_weight_behavior`
- `exact_bootstrap_and_uncertainty_rule`
- `aggregate_per_document_retention_and_validator_behavior`
- `v1_v2_v3_v4_rejections_preserved_and_prohibited_actions_enforced`

Verify that:

- V14 protocol, packet, accepted receipt, stale-review failure; all V15
  protocol, packet, rejection closure; and all V16 protocol, packet,
  rejection closure are pinned with exact bytes. V2–V6 undocumented receipts
  must not be invented.
- The fresh interval is `[18432,34816)` and disjoint from the pilot and V14.
- Model, runtime, raw data, exact paths, BF16 handling, and no-network gates
  are exact and fail-closed.
- Candidates, controls, frozen parameters, per-document provenance, nearest-
  rank bootstrap, uncertainty, and paper target treatment are locked.
- Source, corpus, and result publication perform a post-move code/input
  custody check and roll back on mismatch.
- The validator contains its own model/evaluation/parity seam and neither
  imports the stage runner nor calls `runner.*` measurement functions.
- Review occurs before model/tokenizer load and effects; final validation and
  publication require unchanged reviewed bytes and inputs.

The parent creates the V17 receipt only after a valid independent `ACCEPT`.

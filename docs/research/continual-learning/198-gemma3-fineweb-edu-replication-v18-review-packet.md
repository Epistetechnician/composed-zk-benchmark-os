# Gemma3 FineWeb-Edu replication V18 independent-review packet

State slice: `continual-learning-gemma3-fineweb-edu-replication-v18`.

Read exactly these seven files and no others:

1. `docs/research/continual-learning/197-gemma3-fineweb-edu-replication-v18-protocol.md`
2. `docs/research/continual-learning/198-gemma3-fineweb-edu-replication-v18-review-packet.md`
3. `experiments/continual_learning/gemma3_fineweb_edu_replication_v18_contract.py`
4. `experiments/continual_learning/prepare_gemma3_fineweb_edu_replication_v18.py`
5. `experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v18.py`
6. `experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v18.py`
7. `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_v18.py`

Do not edit, create, delete, stage, format, or mutate any file. Do not access
external `/Volumes/PrimaryED` artifacts or model contents. Do not load a
model/tokenizer, acquire data, use network, run effects, or mutate any ledger.

Recompute the protocol SHA-256, packet SHA-256, and implementation manifest
SHA-256 over the seven files in the contract's declared order. Return exactly
one syntactically valid JSON object and no prose. It must contain nonempty
`reviewer`, canonical UTC `reviewed_at_utc`, literal `effects_run:false`, the
three hashes, a `findings` object with exactly the seven keys below and
explicit boolean values, `material_findings`, and `review_decision`. Use
`ACCEPT` only if every finding is true and all hashes match.

Required finding keys:

- `custody_exact_pinned_data_identity`
- `fit_assessment_prior_pilot_disjointness`
- `locked_configuration_and_paper_target_treatment`
- `controls_and_frozen_weight_behavior`
- `exact_bootstrap_and_uncertainty_rule`
- `aggregate_per_document_retention_and_validator_behavior`
- `v1_v2_v3_v4_rejections_preserved_and_prohibited_actions_enforced`

Verify that:

- V14 protocol, packet, accepted receipt, stale-review failure; all V15 and
  V16 protocol/packet/rejection artifacts; and all V17 protocol/packet/
  rejection artifacts are exact and pinned. V2–V6 undocumented receipts are
  not invented.
- The fresh interval is `[18432,34816)` and disjoint from the pilot and V14.
- Model, runtime, raw data, exact paths, BF16 handling, and no-network gates
  are exact and fail-closed.
- Candidates, controls, frozen parameters, per-document provenance, nearest-
  rank bootstrap, uncertainty, and paper target treatment are locked.
- Source, corpus, and result publication perform a post-move code/input
  custody check and roll back on mismatch.
- Failed nonzero intervention reach raises before result publication and is
  independently rejected by the validator.
- The pre-validation flow permits no validator receipt, then binds the exact
  returned validator object into the post-validation receipt. The final
  validator checks validity, decision, bootstrap, code/input snapshots, and
  custody recomputation—not only a runner-authored flag.
- The validator contains its own model/evaluation/parity seam and neither
  imports the stage runner nor calls `runner.*` measurement functions.
- Review occurs before model/tokenizer load and effects; final validation and
  publication require unchanged reviewed bytes and inputs.

The parent creates the V18 receipt only after a valid independent `ACCEPT`.

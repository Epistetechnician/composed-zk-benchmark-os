# Gemma3 FineWeb-Edu replication V19 independent-review packet

State slice: `continual-learning-gemma3-fineweb-edu-replication-v19`.

Read exactly these seven files and no others:

1. `docs/research/continual-learning/201-gemma3-fineweb-edu-replication-v19-protocol.md`
2. `docs/research/continual-learning/202-gemma3-fineweb-edu-replication-v19-review-packet.md`
3. `experiments/continual_learning/gemma3_fineweb_edu_replication_v19_contract.py`
4. `experiments/continual_learning/prepare_gemma3_fineweb_edu_replication_v19.py`
5. `experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v19.py`
6. `experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v19.py`
7. `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_v19.py`

Do not edit, create, delete, stage, format, or mutate any file. Do not access
external `/Volumes/PrimaryED` artifacts or model contents. Do not load a
model/tokenizer, acquire data, use network, run effects, or mutate any ledger.

Recompute protocol SHA-256, packet SHA-256, and implementation manifest
SHA-256 over the seven files in the contract's declared order. Return exactly
one syntactically valid JSON object and no prose, with nonempty `reviewer`,
canonical UTC `reviewed_at_utc`, literal `effects_run:false`, the three hashes,
exactly these seven finding keys with explicit boolean values, a
`material_findings` array, and `review_decision`. Use `ACCEPT` only if every
finding is true and all hashes match; otherwise use `REJECT`.

Required finding keys:

- `custody_exact_pinned_data_identity`
- `fit_assessment_prior_pilot_disjointness`
- `locked_configuration_and_paper_target_treatment`
- `controls_and_frozen_weight_behavior`
- `exact_bootstrap_and_uncertainty_rule`
- `aggregate_per_document_retention_and_validator_behavior`
- `v1_v2_v3_v4_rejections_preserved_and_prohibited_actions_enforced`

Verify complete V1–V18 history, including V15/V16/V17/V18 protocol, packet,
and rejection artifacts; exact fresh `[18432,34816)` disjointness; model,
runtime, raw-data, path, BF16, and offline custody; fixed candidates, target,
controls, parameter freeze, provenance, bootstrap, and claim ceiling; and
transactional publication rollback.

Specifically verify that failed nonzero reach raises before result creation and
is independently required; that the first validator pass may omit only the
receipt; that the runner then binds the exact returned validation object into
the receipt; and that it invokes a second full `validate_result` pass with the
receipt required before publication. The second pass must bind result bytes,
validity, decision, bootstrap, code/input snapshots, and custody recomputation.
Verify the validator has a local measurement seam and no runner import or
`runner.*` calls. Review must precede model/tokenizer load and effects.

The parent creates the V19 receipt only after a valid independent `ACCEPT`.

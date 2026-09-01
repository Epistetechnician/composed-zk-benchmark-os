# Gemma3 FineWeb-Edu replication V27 independent-review packet

State slice: `continual-learning-gemma3-fineweb-edu-replication-v27`.

Read exactly these seven files and no others:

1. `docs/research/continual-learning/233-gemma3-fineweb-edu-replication-v27-protocol.md`
2. `docs/research/continual-learning/234-gemma3-fineweb-edu-replication-v27-review-packet.md`
3. `experiments/continual_learning/gemma3_fineweb_edu_replication_v27_contract.py`
4. `experiments/continual_learning/prepare_gemma3_fineweb_edu_replication_v27.py`
5. `experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v27.py`
6. `experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v27.py`
7. `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_v27.py`

Do not edit, create, delete, stage, format, or mutate any file. Do not access
external `/Volumes/PrimaryED` artifacts or model contents. Do not load a
model/tokenizer, acquire data, use network, run effects, or mutate any ledger.

Recompute protocol SHA-256, packet SHA-256, and implementation manifest
SHA-256 over the seven files in the contract's declared order. Return exactly
one syntactically valid JSON object and no prose, with nonempty `reviewer`,
canonical UTC `reviewed_at_utc`, literal `effects_run:false`, the three hashes,
exactly the seven finding keys below with explicit boolean values,
`material_findings`, and `review_decision`. Use `ACCEPT` only if every finding
is true and all hashes match; otherwise use `REJECT`.

Required finding keys:

- `custody_exact_pinned_data_identity`
- `fit_assessment_prior_pilot_disjointness`
- `locked_configuration_and_paper_target_treatment`
- `controls_and_frozen_weight_behavior`
- `exact_bootstrap_and_uncertainty_rule`
- `aggregate_per_document_retention_and_validator_behavior`
- `v1_v2_v3_v4_rejections_preserved_and_prohibited_actions_enforced`

Verify every extant V1–V26 artifact is exact and pinned, including V14’s
accepted receipt/stale failure and the V15–V24 protocol, packet, and rejection
closures, plus the V25 and V26 protocol, packet, and rejection closures. Verify
that the contract explicitly checks the documented absence of
canonical V2–V6 rejection receipts and does not synthesize them. Then verify
fresh `[18432,34816)` disjointness; exact model/runtime/raw/path/BF16/offline
custody; fixed candidates, target, controls, uncertainty, and provenance;
transactional publication rollback; hard nonzero reach; post-validation
receipt binding; the final full `validate_result` pass with receipt required;
descriptor-bound file and Parquet custody; the byte-identical external V27
model snapshot and snapshot-only model loading; explicit false
`config.evidence_ledger_mutation`; and the local independent validator seam
with no runner import or `runner.*` calls.

Review must precede model/tokenizer load and effects, including the validator
CLI corpus-mode tokenizer construction. Existing snapshots must have exact
read-only file and directory modes. The parent creates the
V27 receipt only after a valid independent `ACCEPT`.

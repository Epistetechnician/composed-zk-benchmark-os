# Gemma3 FineWeb-Edu replication V30 independent-review packet

State slice: `continual-learning-gemma3-fineweb-edu-replication-v30`.

Read exactly these seven files and no others:

1. `docs/research/continual-learning/245-gemma3-fineweb-edu-replication-v30-protocol.md`
2. `docs/research/continual-learning/246-gemma3-fineweb-edu-replication-v30-review-packet.md`
3. `experiments/continual_learning/gemma3_fineweb_edu_replication_v30_contract.py`
4. `experiments/continual_learning/prepare_gemma3_fineweb_edu_replication_v30.py`
5. `experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v30.py`
6. `experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v30.py`
7. `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_v30.py`

Do not edit, create, delete, stage, format, or mutate any file. Do not access
external `/Volumes/PrimaryED` artifacts or model contents. Do not load a
model/tokenizer, acquire data, use network, run effects, or mutate any ledger.

Recompute protocol SHA-256, packet SHA-256, and implementation manifest
SHA-256 over the seven files in the contract's declared order. Return exactly
one syntactically valid JSON object and no prose. The object must contain
nonempty `reviewer`, canonical UTC `reviewed_at_utc`, literal boolean
`effects_run:false`, the three hashes, exactly the seven finding keys below
with explicit boolean values, `material_findings`, and `review_decision`.
Use `ACCEPT` only if every finding is true and all hashes and scope checks
match. A malformed response is not an acceptance.

Required finding keys:

- `custody_exact_pinned_data_identity`
- `fit_assessment_prior_pilot_disjointness`
- `locked_configuration_and_paper_target_treatment`
- `controls_and_frozen_weight_behavior`
- `exact_bootstrap_and_uncertainty_rule`
- `aggregate_per_document_retention_and_validator_behavior`
- `v1_v2_v3_v4_rejections_preserved_and_prohibited_actions_enforced`

Verify every extant V1-V29 artifact is exact and pinned, including V14's
accepted receipt/stale failure, V15-V24 protocol/packet/rejection closures,
V25-V27 protocol/packet/rejection closures, and V28-V29 protocol/packet/
rejection closures. Verify documented absence checks for canonical V2-V6
rejection receipts without synthesizing them. Verify that this packet's
allowlist names the actual V30 protocol and packet and that its history scope
reaches V29.

Then verify fresh `[18432,34816)` disjointness; exact model/runtime/raw/path/
BF16/offline custody; fixed candidates, expected `(11,4)` target treatment,
controls, uncertainty, and provenance; transactional publication rollback;
hard nonzero reach; post-validation receipt binding; final full
`validate_result` pass with receipt required; descriptor-bound file and
Parquet custody; byte-identical external V30 model snapshot and snapshot-only
model loading; read-only snapshot modes with permission-safe rollback cleanup;
explicit false `config.evidence_ledger_mutation`; and the local independent
validator seam with no runner import or `runner.*` calls.

Review must precede model/tokenizer load and effects, including validator CLI
corpus-mode tokenizer construction. Existing snapshots must have exact
read-only file and directory modes. The parent creates the V30 receipt only
after a valid independent `ACCEPT`.

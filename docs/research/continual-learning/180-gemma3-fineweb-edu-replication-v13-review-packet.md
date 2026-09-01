# Gemma3 FineWeb-Edu replication V13 independent-review packet

State slice: `continual-learning-gemma3-fineweb-edu-replication-v13`.

Read exactly these seven files and no others:

1. `docs/research/continual-learning/179-gemma3-fineweb-edu-replication-v13-protocol.md`
2. `docs/research/continual-learning/180-gemma3-fineweb-edu-replication-v13-review-packet.md`
3. `experiments/continual_learning/gemma3_fineweb_edu_replication_v13_contract.py`
4. `experiments/continual_learning/prepare_gemma3_fineweb_edu_replication_v13.py`
5. `experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v13.py`
6. `experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v13.py`
7. `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_v13.py`

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

The V13 reviewer must verify that the complete extant V1-V12 history is
included in the contract's pinned history, including the V1 protocol and
packet, the V10 rejection, the V11 acceptance and pre-effect failure, and the
V12 rejection. The reviewer must not require or synthesize undocumented V2-V6
rejection receipts. The reviewer must also verify that the two V10 findings
are closed by the source-prefix/path checks and canonical metric/bootstrap
order checks, and that the BF16 digest conversion is representation-only with
no model update or scientific-artifact reuse.

The parent creates the V13 receipt only after a valid `ACCEPT`. A rejection or
missing report is not acceptance. Do not create a V13 receipt.

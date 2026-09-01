# Gemma3 FineWeb-Edu replication V6 independent-review packet

State slice: `continual-learning-gemma3-fineweb-edu-replication-v6`.

The independent reviewer must read exactly these seven files and no other
files. The reviewer must not edit, create, delete, stage, or execute effects;
must not access external raw, source, corpus, result, or model contents; and
must return one canonical JSON report. The parent creates the receipt only
after a report with `review_decision: "ACCEPT"` exists.

1. `docs/research/continual-learning/157-gemma3-fineweb-edu-replication-v6-protocol.md`
2. `docs/research/continual-learning/158-gemma3-fineweb-edu-replication-v6-review-packet.md`
3. `experiments/continual_learning/gemma3_fineweb_edu_replication_v6_contract.py`
4. `experiments/continual_learning/prepare_gemma3_fineweb_edu_replication_v6.py`
5. `experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v6.py`
6. `experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v6.py`
7. `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_v6.py`

Recompute the protocol SHA-256, packet SHA-256, and exact implementation
manifest SHA-256 from those files. Return exactly these finding keys:

- `custody_exact_pinned_data_identity`
- `fit_assessment_prior_pilot_disjointness`
- `locked_configuration_and_paper_target_treatment`
- `controls_and_frozen_weight_behavior`
- `exact_bootstrap_and_uncertainty_rule`
- `aggregate_per_document_retention_and_validator_behavior`
- `v1_v2_v3_v4_rejections_preserved_and_prohibited_actions_enforced`

`ACCEPT` is valid only when all seven are true, `effects_run` is false, the
files and digests are exact, and no material fail-open path remains. Otherwise
return `REJECT` with file/line evidence and a minimal remedy. Do not create a
V6 receipt from a rejection, and do not treat V5's invalid review or clean
rejection as an acceptance.


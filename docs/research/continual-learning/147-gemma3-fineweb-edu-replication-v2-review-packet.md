# Independent review packet: Gemma3 FineWeb-Edu replication V2

State slice: `continual-learning-gemma3-fineweb-edu-replication-v2`

This packet requests a fresh, independent review of protocol revision V2. The
prior V1 review returned `REJECT` and remains immutable. The reviewer must not
reinterpret V1 as approval and must not run model effects while reviewing.

## Frozen protocol binding

- Protocol: `docs/research/continual-learning/146-gemma3-fineweb-edu-replication-v2-protocol.md`
- Protocol SHA-256: `580d3890668303e870184e910e0c0cd2098ddb6064b89da565385489e7e71564`
- Claim ceiling: `LocalDevelopmentGemma3FineWebEduReplicationV2`
- Required status: `ACCEPT` or `REJECT`; no partial approval

## Review scope

Review these files as a single V2 contract:

- `docs/research/continual-learning/146-gemma3-fineweb-edu-replication-v2-protocol.md`
- `docs/research/continual-learning/147-gemma3-fineweb-edu-replication-v2-review-packet.md`
- `experiments/continual_learning/prepare_gemma3_fineweb_edu_replication_v2.py`
- `experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v2.py`
- `experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v2.py`
- `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_v2.py`

Run only pure/unit checks and static inspection. Do not stage the fresh corpus,
load Gemma3, run a forward pass, inspect assessment effects, contact a
provider, mutate the Evidence Ledger, or write experiment output.

## Required findings

The canonical receipt must contain a boolean `findings` object with all of
these keys set to `true`:

- `custody_exact_pinned_data_identity`
- `fit_assessment_prior_pilot_disjointness`
- `locked_configuration_and_paper_target_treatment`
- `controls_and_frozen_weight_behavior`
- `exact_bootstrap_and_uncertainty_rule`
- `aggregate_per_document_retention_and_validator_behavior`
- `v1_rejection_preserved_and_prohibited_actions_enforced`

The receipt must also bind:

- `protocol_sha256` to the frozen protocol hash above;
- `review_packet_sha256` to this packet's actual SHA-256;
- `implementation_manifest_sha256` to the V2 validator's computed manifest;
- `review_status` to `ACCEPT` only when every finding is true;
- a concise `reviewer` identity and `reviewed_at_utc` timestamp;
- `effects_run` to `false`.

The receipt is self-digested with canonical JSON: SHA-256 of the object after
removing `receipt_digest_sha256`, sorted keys, compact separators, UTF-8.

Any missing executable guard, ambiguous bootstrap step, incorrect binding,
or untested validator path is a `REJECT`. No assessment authorization is
implied by a review of the protocol alone; the runner must enforce the receipt
at runtime.

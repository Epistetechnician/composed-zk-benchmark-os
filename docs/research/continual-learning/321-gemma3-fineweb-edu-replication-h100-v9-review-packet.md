# Independent review packet — Gemma3 FineWeb-Edu H100 V9

State slice: `continual-learning-gemma3-fineweb-edu-replication-h100-v9`.

This is an implementation-only, closed-world review. The reviewer must read
exactly the allowlist below, recompute every digest, and inspect the protocol,
implementation, tests, provider bundle, runtime lock, and current `AGENTS.md`.
The reviewer must not read external custody, load a model, contact
GiveMeANode, build an image, submit a job, spend money, or create an execution
or provider receipt.

The reviewer must return exactly the following JSON keys:

`schema`, `state_slice`, `review_decision`, `reviewer`, `reviewed_at_utc`,
`reviewed_files`, `reviewed_file_sha256`, `protocol_sha256`,
`review_packet_sha256`, `implementation_manifest_sha256`, `findings`,
`effects_run`, `review_thread_id`, `reviewer_key_id`, `reviewer_public_key`,
`review_signature`, and `receipt_sha256`.

The only gate-opening result is a non-empty, packet-bound signed Ed25519
`ACCEPT`. The signature covers the canonical receipt payload excluding
`review_signature` and `receipt_sha256`. The operator must not fabricate the
manifest, receipt, key, signature, or reviewer identity.

Every finding must be `true`:

- `custody_and_fresh_disjoint_cohort`
- `provider_shape_and_hard_budget_gate`
- `runtime_and_model_freeze`
- `qualification_and_network_boundary`
- `locked_recurrence_controls_and_uncertainty`
- `independent_validator_and_publication_order`
- `v1_v2_identity_preserved_without_scientific_reuse`

## Exact allowlist

1. `docs/research/continual-learning/320-gemma3-fineweb-edu-replication-h100-v9-protocol.md`
2. `docs/research/continual-learning/321-gemma3-fineweb-edu-replication-h100-v9-review-packet.md`
3. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_preflight.py`
4. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9.py`
5. `experiments/continual_learning/validate_gemma3_fineweb_edu_replication_h100_v9.py`
6. `experiments/continual_learning/pack_gemma3_fineweb_edu_replication_h100_v9.py`
7. `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v9_preflight.py`
8. `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v9.py`
9. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_provider/Dockerfile`
10. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_provider/requirements.lock`
11. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_provider/runtime-lock.json`
12. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_provider/run_h100_v9.sh`
13. `AGENTS.md`
14. `docs/research/continual-learning/322-gemma3-fineweb-edu-replication-h100-v9-implementation-manifest.json`

The implementation manifest excludes itself from its file list but binds the
other 13 allowlisted files in this exact order. Any byte change after review
invalidates the receipt. A static local check is not independent acceptance.

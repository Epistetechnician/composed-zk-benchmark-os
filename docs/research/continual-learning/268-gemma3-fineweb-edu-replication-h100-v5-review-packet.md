# Independent review packet — Gemma3 FineWeb-Edu H100 V5

State slice: `continual-learning-gemma3-fineweb-edu-replication-h100-v5`.

This is a closed-world, implementation-only review. The reviewer must read
exactly the files listed below, recompute every listed SHA-256 digest, and
inspect the protocol, implementation, tests, provider image contract,
dependency closure, runtime lock, and current `AGENTS.md` bytes together.
The reviewer must not read unrelated files, access external custody, load a
model, contact GiveMeANode, build an image, submit a job, spend money, or
create any scientific or provider receipt.

The reviewer must return one canonical JSON object with exactly these keys:

`schema`, `state_slice`, `review_decision`, `reviewer`, `reviewed_at_utc`,
`reviewed_files`, `reviewed_file_sha256`, `protocol_sha256`,
`review_packet_sha256`, `implementation_manifest_sha256`, `findings`,
`effects_run`, `review_thread_id`, `reviewer_key_id`, `reviewer_public_key`,
`review_signature`, and `receipt_sha256`.

The only acceptable decision for opening later gates is a non-empty,
packet-bound signed Ed25519 `ACCEPT`. The reviewer must sign the canonical
receipt payload formed by excluding `review_signature` and `receipt_sha256`.
The signature is checked by both the no-spend preflight and the independent
result validator. The reviewer thread ID is provenance; the operator cannot
generate, copy, or alter a receipt and call it independent.

Every finding below must be `true`:

- `custody_and_fresh_disjoint_cohort`
- `provider_shape_and_hard_budget_gate`
- `runtime_and_model_freeze`
- `qualification_and_network_boundary`
- `locked_recurrence_controls_and_uncertainty`
- `independent_validator_and_publication_order`
- `v1_v2_identity_preserved_without_scientific_reuse`

Reject if any path is stale, any digest fails, any gate is fail-open, the
exact USD 100.00 ceiling is not enforced, the estimate is not exactly quote
times minutes, the provider trust-root/certificate chain is not checked, the
dependency closure is not installed from lock, model identity is generic,
network proof is incomplete, the selected pair or controls are not
rederived, the result can omit custody bindings, publication can precede
provider-receipt validation, or V1/V2/V3/V4 scientific material can enter V5.

## Exact allowlist

1. `docs/research/continual-learning/267-gemma3-fineweb-edu-replication-h100-v5-protocol.md`
2. `docs/research/continual-learning/268-gemma3-fineweb-edu-replication-h100-v5-review-packet.md`
3. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v5_preflight.py`
4. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v5.py`
5. `experiments/continual_learning/validate_gemma3_fineweb_edu_replication_h100_v5.py`
6. `experiments/continual_learning/pack_gemma3_fineweb_edu_replication_h100_v5.py`
7. `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v5_preflight.py`
8. `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v5.py`
9. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v5_provider/Dockerfile`
10. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v5_provider/requirements.lock`
11. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v5_provider/runtime-lock.json`
12. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v5_provider/run_h100_v5.sh`
13. `AGENTS.md`
14. `docs/research/continual-learning/269-gemma3-fineweb-edu-replication-h100-v5-implementation-manifest.json`

The implementation manifest excludes itself from its file list but binds the
other 13 allowlisted files exactly. It is itself bound by this packet and the
future signed receipt. A receipt is stale if any allowlisted byte changes
after review. A missing, malformed, unsigned, or operator-generated receipt
is failure.

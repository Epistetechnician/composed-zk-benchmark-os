# Independent review packet — Gemma3 FineWeb-Edu H100 V4

State slice: `continual-learning-gemma3-fineweb-edu-replication-h100-v4`.

This packet is a closed-world, implementation-only review. The reviewer must
read exactly the files listed below, recompute every listed SHA-256 digest,
and inspect the protocol, implementation, tests, provider image contract,
runtime lock, and current `AGENTS.md` bytes together. The reviewer must not
read unrelated files, access external custody, load a model, contact
GiveMeANode, build an image, submit a job, spend money, or create a receipt.

The reviewer must return one canonical JSON object with exactly these keys:

`schema`, `state_slice`, `review_decision`, `reviewer`, `reviewed_at_utc`,
`reviewed_files`, `reviewed_file_sha256`, `protocol_sha256`,
`review_packet_sha256`, `implementation_manifest_sha256`, `findings`,
`effects_run`, and `receipt_sha256`.

The only acceptable decision for opening later gates is a non-empty,
packet-bound signed Ed25519 `ACCEPT`. Every finding below must be `true`:

- `custody_and_fresh_disjoint_cohort`
- `provider_shape_and_hard_budget_gate`
- `runtime_and_model_freeze`
- `qualification_and_network_boundary`
- `locked_recurrence_controls_and_uncertainty`
- `independent_validator_and_publication_order`
- `v1_v2_identity_preserved_without_scientific_reuse`

The reviewer must reject if any path is stale, any digest fails, any gate is
fail-open, the exact USD 100.00 ceiling is not enforced, the estimate is not
exactly quote times minutes, provider attestation cannot be independently
verified, the model/runtime is not exact, the network proof is incomplete,
the selected pair or controls are not rederived, the result can omit custody
bindings, publication can precede provider-receipt validation, or V1/V2/V3
scientific material can enter V4.

## Exact allowlist

1. `docs/research/continual-learning/264-gemma3-fineweb-edu-replication-h100-v4-protocol.md`
2. `docs/research/continual-learning/265-gemma3-fineweb-edu-replication-h100-v4-review-packet.md`
3. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v4_preflight.py`
4. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v4.py`
5. `experiments/continual_learning/validate_gemma3_fineweb_edu_replication_h100_v4.py`
6. `experiments/continual_learning/pack_gemma3_fineweb_edu_replication_h100_v4.py`
7. `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v4_preflight.py`
8. `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v4.py`
9. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v4_provider/Dockerfile`
10. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v4_provider/requirements.lock`
11. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v4_provider/runtime-lock.json`
12. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v4_provider/run_h100_v4.sh`
13. `AGENTS.md`
14. `docs/research/continual-learning/266-gemma3-fineweb-edu-replication-h100-v4-implementation-manifest.json`

The implementation manifest excludes itself from its file list but binds the
other 13 allowlisted files exactly and is itself bound by this packet and the
future receipt. A receipt is stale if any allowlisted byte changes after
review. The operator cannot self-sign or infer acceptance from a missing or
malformed reviewer response.

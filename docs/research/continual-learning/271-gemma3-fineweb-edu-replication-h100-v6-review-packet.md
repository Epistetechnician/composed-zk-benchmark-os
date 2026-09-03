# Independent review packet — Gemma3 FineWeb-Edu H100 V6

State slice: `continual-learning-gemma3-fineweb-edu-replication-h100-v6`.

This is a closed-world, implementation-only review. The reviewer must read
exactly the files listed below, recompute every SHA-256 digest, and inspect
the protocol, implementation, tests, provider image contract, dependency
closure, runtime lock, and current `AGENTS.md` together. The reviewer must
not read unrelated files, access external custody, load a model, contact
GiveMeANode, build an image, submit a job, spend money, or create a scientific
or provider receipt.

The reviewer must return one canonical JSON object with exactly these keys:

`schema`, `state_slice`, `review_decision`, `reviewer`, `reviewed_at_utc`,
`reviewed_files`, `reviewed_file_sha256`, `protocol_sha256`,
`review_packet_sha256`, `implementation_manifest_sha256`, `findings`,
`effects_run`, `review_thread_id`, `reviewer_key_id`, `reviewer_public_key`,
`review_signature`, and `receipt_sha256`.

The only decision that opens later gates is a non-empty packet-bound signed
Ed25519 `ACCEPT`. The reviewer signs the canonical receipt payload formed by
excluding `review_signature` and `receipt_sha256`. Silence, an empty response,
stale bytes, malformed output, or operator-generated signing is not
acceptance.

Every finding below must be `true`:

- `custody_and_fresh_disjoint_cohort`
- `provider_shape_and_hard_budget_gate`
- `runtime_and_model_freeze`
- `qualification_and_network_boundary`
- `locked_recurrence_controls_and_uncertainty`
- `independent_validator_and_publication_order`
- `v1_v2_identity_preserved_without_scientific_reuse`

Reject if any digest or path is stale, the exact USD 100.00 ceiling is not
enforced with exact decimal arithmetic, the provider trust chain is not
verified, dependencies are not installed from the lock, model identity is
generic, network proof is incomplete, candidate or control behavior is
fail-open, the final result retains per-document scalars, the temporary ledger
is not digest-bound and deleted after validation, provider fields are absent
from result binding, or V1/V2/V3/V4/V5 scientific material can enter V6.

## Exact allowlist

1. `docs/research/continual-learning/270-gemma3-fineweb-edu-replication-h100-v6-protocol.md`
2. `docs/research/continual-learning/271-gemma3-fineweb-edu-replication-h100-v6-review-packet.md`
3. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v6_preflight.py`
4. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v6.py`
5. `experiments/continual_learning/validate_gemma3_fineweb_edu_replication_h100_v6.py`
6. `experiments/continual_learning/pack_gemma3_fineweb_edu_replication_h100_v6.py`
7. `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v6_preflight.py`
8. `experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v6.py`
9. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v6_provider/Dockerfile`
10. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v6_provider/requirements.lock`
11. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v6_provider/runtime-lock.json`
12. `experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v6_provider/run_h100_v6.sh`
13. `AGENTS.md`
14. `docs/research/continual-learning/272-gemma3-fineweb-edu-replication-h100-v6-implementation-manifest.json`

The implementation manifest excludes itself from its file list but binds the
other 13 allowlisted files exactly. A receipt is stale if any allowlisted
byte changes after review. The implementation manifest and signed receipt are
not to be fabricated by the operator.

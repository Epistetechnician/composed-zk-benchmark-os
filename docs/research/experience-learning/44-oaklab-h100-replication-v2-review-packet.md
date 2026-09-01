# Oak Lab H100 replication V2 independent-review packet

State slice: `oaklab-experience-learning-h100-replication-v2`.

This packet requests an independent static review only. It does not authorize
implementation, model/data acquisition, provider access, spend, or effects.

The reviewer must read exactly the following files, recompute every SHA-256
from stable bytes, and reject any missing, changed, undeclared, or ambiguous
input:

1. `docs/research/experience-learning/43-oaklab-h100-replication-v2-protocol.md`
2. `docs/research/experience-learning/44-oaklab-h100-replication-v2-review-packet.md`
3. `experiments/experience_learning/oaklab_h100_v2_protocol.json`
4. `experiments/experience_learning/compile_oaklab_h100_v2_protocol.py`
5. `experiments/experience_learning/validate_oaklab_h100_v2_protocol.py`
6. `experiments/experience_learning/tests/test_oaklab_h100_v2_protocol.py`
7. `experiments/experience_learning/oaklab_h100_v2_compiled_protocol.json`
8. `AGENTS.md`

The reviewer receipt must contain exactly these top-level keys:
`schema`, `state_slice`, `review_decision`, `reviewer`, `reviewed_at_utc`,
`reviewed_files`, `reviewed_file_sha256`, `protocol_sha256`,
`review_packet_sha256`, `compiled_sha256`, `findings`, `effects_run`, and
`receipt_sha256`.

The findings set is closed and must contain exactly:

- `fresh_estimand_and_carryover_controls`
- `canonical_manifest_hashing`
- `provider_cost_stop_receipts`
- `closed_world_result_root`
- `fit_tune_assessment_locking`
- `resource_and_energy_gate`
- `execution_boundary_and_isolation`

`ACCEPT` requires all findings true, exact reviewed-file ordering and hashes,
UTC reviewer identity distinct from the operator, `effects_run: false`, and a
valid canonical self-digest. Any false finding is `REJECT` and authorizes no
execution. The reviewer may not infer a provider, node, cost ceiling, model,
dataset, or receipt that is absent from the packet.

Every mutation in this phase names state slice
`oaklab-experience-learning-h100-replication-v2`.

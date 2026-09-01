# Oak Lab H100 replication V3 independent-review packet

State slice: `oaklab-experience-learning-h100-replication-v3`.

This is a static review request. It is not implementation, custody, provider,
spend, H100, or effects authorization.

Read exactly these files and no others:

1. `docs/research/experience-learning/48-oaklab-h100-replication-v3-protocol.md`
2. `docs/research/experience-learning/49-oaklab-h100-replication-v3-review-packet.md`
3. `experiments/experience_learning/oaklab_h100_v3_protocol.json`
4. `experiments/experience_learning/compile_oaklab_h100_v3_protocol.py`
5. `experiments/experience_learning/validate_oaklab_h100_v3_protocol.py`
6. `experiments/experience_learning/tests/test_oaklab_h100_v3_protocol.py`
7. `experiments/experience_learning/oaklab_h100_v3_compiled_protocol.json`
8. `AGENTS.md`

The receipt must contain exactly these top-level keys:
`schema`, `state_slice`, `review_decision`, `reviewer`, `reviewed_at_utc`,
`reviewed_files`, `reviewed_file_sha256`, `protocol_sha256`,
`review_packet_sha256`, `compiled_sha256`, `findings`, `effects_run`, and
`receipt_sha256`.

The findings set is exactly:

- `paired_estimand_and_carryover_controls`
- `canonical_campaign_manifest`
- `signed_provider_cost_stop_receipts`
- `closed_world_digest_content_result_root`
- `fit_tune_prediction_lock_receipts`
- `resource_energy_formulas_and_margins`
- `execution_boundary_and_lane_isolation`

`ACCEPT` requires all findings true, exact ordered file hashes, independent
reviewer identity, UTC timestamp, `effects_run: false`, and a valid canonical
self-digest. Any false finding is `REJECT`; it authorizes no execution. The
reviewer must not invent a provider, node, spend ceiling, model, dataset,
signature, or receipt.

Every mutation in this phase names state slice
`oaklab-experience-learning-h100-replication-v3`.

# Oak Lab H100 replication V2 independent review

State slice: `oaklab-experience-learning-h100-replication-v2`.

Decision: `REJECT`.

The exact eight-file packet was read from stable bytes. Hermetic validation
passed (`4 passed`), but the packet is not executable enough for acceptance.

Findings:

- `fresh_estimand_and_carryover_controls`: `false` — one arm is assigned per
  episode, but the claimed paired regret has no executable cross-arm pairing
  unit or pairing rule.
- `canonical_manifest_hashing`: `false` — campaign-manifest schema,
  canonical serialization, self-digest, and manifest-to-result binding are
  absent; `manifest_sha256` remains a placeholder.
- `provider_cost_stop_receipts`: `false` — fields are listed, but exact
  serialization, UTC grammar, signatures, allocation binding, stop semantics,
  and hard-ceiling binding are unspecified.
- `closed_world_result_root`: `false` — the validator checks paths and
  symlinks but not file digests, contents, finite values, or manifest binding.
- `fit_tune_assessment_locking`: `false` — no executable fit/tune lock,
  prediction lock, independent lock receipt, or lock path is defined.
- `resource_and_energy_gate`: `false` — no non-inferiority margins/test rules,
  operation formulas, energy trace schema, joule integration, or denominator
  is defined.
- `execution_boundary_and_isolation`: `true` — pre-review prohibition and
  lane isolation are explicit.

No model, data, provider, H100, energy, or effects execution occurred. This
review does not authorize patching or retuning V2. A continuation requires a
new protocol identity with a fully executable estimand, manifest, receipt,
locking, resource, and result-root contract.

Receipt: `45-oaklab-h100-replication-v2-independent-review.json`.

Every mutation in this phase names state slice
`oaklab-experience-learning-h100-replication-v2`.

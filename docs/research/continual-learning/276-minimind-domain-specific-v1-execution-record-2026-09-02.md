# MiniMind domain-specific continual-learning V1 execution record

State slice: `continual-learning-minimind-domain-specific-v1`.

## Disposition

The canonical exact-synthetic fixture completed as `SyntheticCandidate` and
was independently validated. This is a bounded contract qualification, not a
MiniMind model result.

The tune lock selected `domain_adapters`. On the independent assessment split,
its mean primary improvement was `0.06493918724968535`, with maximum forgetting
`0.0` and maximum forward/reverse order delta `0.0`. The other assessment arms
were retained as controls. The result contains 108 trials across three splits,
three replicate seeds, three order seeds, six arms, and both order directions.

## Custody and identity

- MiniMind source commit: `7a6fddd63a30c06b2fdd5fac4089922b29bc841b`
- Source manifest digest: `0289a66fa4076c917aa9cf76a0df64a0900d5c805f76ee395d95e75ec5139e21`
- Canonical artifact root: `/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v1-synthetic-20260902-r2`
- Result digest: `0aeaa0339f8364d92da805380cb9d808f7e5829c7b77d61b9c1f8856300b41ee`
- Independent validator: `valid`

The earlier provisional synthetic output ending in `20260902` was generated
before the split-correlation correction and is stale. It is excluded from this
record; only the `20260902-r2` artifact is canonical.

## Execution boundary

Training, model loading, inference, network access, provider calls, and
assessment on real MiniMind data were all `false`. The real MiniMind runner is
implemented for the same 108-trial factorial but refuses to proceed without
the fresh independent signed Ed25519 `ACCEPT` required by review packet 274.
No acceptance receipt exists. It retains only aggregate model metrics and
verifies in-memory checkpoint snapshots; no raw model weights or real-model
output were created.

The claim ceiling is
`LocalDevelopmentMiniMindDomainSequenceSyntheticOnly`. No model-bearing,
general continual-learning, benchmark, production, or provider claim follows
from this record.

Every mutation in this phase names state slice
`continual-learning-minimind-domain-specific-v1`.

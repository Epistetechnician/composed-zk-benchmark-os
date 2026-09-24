# Causal-intervention record V1

State slice: `proof-carrying-nano-causal-intervention-record-v1`.

This package defines a closed, record-only schema for a future activation
replacement observation. It binds a parent activation action digest, donor and
target checkpoint/layer/site/token coordinates, before/after activation
digests, the exact replacement operator, measured effect and controls, host
parameter digests, proof status, and replay metadata.

The exact operator in V1 is `replace_token_vector` with coefficient `1`, no
interpolation, and digest-bound donor and target activations. Records are
immutable in the SQLite WAL store and export as `CausalInterventionRecordOnly`
bundles. Host parameters must have equal before/after digests.

The Lean theorem and independent validator establish only record identity,
operator syntax, digest binding, replay metadata consistency, unchanged host
parameters, and checked-proof artifact binding. They do not prove that the
measured effect is causal, that the donor is semantically matched, or that the
host implementation is faithfully modeled.

Run the hermetic contract gate:

```text
pnpm --ignore-workspace run verify:proof-carrying-nano-causal-intervention-record-v1
```

No host intervention is executed by this package. Causal assessment remains
sealed until an independent reviewer accepts the exact review packet at
`docs/research/proof-carrying-nano-causal-intervention-record-v1-review-packet.md`.

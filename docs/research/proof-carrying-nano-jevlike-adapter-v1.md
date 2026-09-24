# Proof-carrying nano Jevlike adapter V1

State slice: `proof-carrying-nano-interp-jevlike-adapter-v1`.

Status: implemented contract boundary; external model execution not run.

## Scope

This slice connects the stable hypothesis option/action shape to a pinned
external Jevlike scorer. It does not vendor Jevlike, download a checkpoint,
attach to a frontier host, mutate host activations, promote a hypothesis to a
causal claim, or build the dashboard or swarm controller.

The adapter accepts the ordered candidate IDs already represented by the V1
option schema. It passes those IDs to Jevlike as text options, records the
returned values as canonical decimal strings, and quantizes them to exact
non-negative integer weights. The action records the option-set digest,
context digest, host checkpoint/layer/site, scorer identity, checkpoint
digest, encoder/runtime identities, device, seed, quantization configuration,
and pinned upstream revision.

The only supported upstream revision is:

`vinnylarouge/jevlike@94f5fd1b0b11d52bbdfdf4e0ee6aa96b568f8452`

`PinnedJevlikeRunner` checks the checkout revision and scorer checkpoint file
digest before delayed imports of Jevlike's public `ChoiceExample`,
`load_checkpoint`, and `move` APIs. Tests inject a fake runner, so the
repository verification lane does not require PyTorch, Jevlike, a checkpoint,
or external network access.

## Proof boundary

Every emitted action has status `HypothesisOnly`. `JevlikeLeanProofEngine`
rechecks the action and generates a Lean theorem over the recorded fixed-point
weights. The theorem proves:

- the exact integer weight sum and rational normalization entries;
- the selected index is a maximum, with first-index tie behavior;
- the selected index, candidate ID, and candidate kind agree with the ordered
  option set.

The theorem does not prove that Jevlike scored the host correctly, that its
checkpoint is useful, that the host computation has the claimed mechanism, or
that an intervention has a causal effect. Those require a later separately
authorized evidence slice.

## Store and replay

`JevlikeHypothesisStore` uses the append-only SQLite/WAL action and proof
tables, rejects stale or forged digests, rechecks checked proofs before commit,
and exports bundles with status `HypothesisOnly`. Contradictory checked
selections sharing the same claim key are returned as conflicts rather than
silently resolved.

Replay consumes only the recorded decimal scores and option-set payload. It
does not invoke Jevlike again. Reordering the option payload, changing a
quantized weight, changing a raw score to `NaN`, or rebinding the selected
index fails closed.

## Verification

Run:

```text
pnpm --ignore-workspace run verify:proof-carrying-nano-jevlike-adapter-v1
```

The claim ceiling is
`LocalExternalJevlikeQuantizedHypothesisRankingOnly`. Passing this local
contract check is not independent review, scientific validation, host-model
evidence, or production authorization.

Every mutation governed by this record touches state slice
`proof-carrying-nano-interp-jevlike-adapter-v1`.

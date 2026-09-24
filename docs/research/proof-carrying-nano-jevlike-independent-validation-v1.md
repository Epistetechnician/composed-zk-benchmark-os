# Independent Jevlike adapter validation V1

State slice: `proof-carrying-nano-jevlike-independent-validation-v1`.

This slice independently validates the existing Jevlike hypothesis bundle
boundary. It does not raise the claim ceiling, attach to a real host model,
perform causal interventions, mutate host weights, or authorize production or
scientific use.

## Validator boundary

`tools/proof_carrying_nano_jevlike_independent_validation_v1/validator.py`
has no dependency on the adapter store or proof generator. It independently
checks the closed bundle schema, canonical bundle/action/option/proof digests,
ordered option and context bindings, pinned scorer configuration, exact decimal
score capture, fixed-point probability normalization, first-max selected-index
consistency, `HypothesisOnly`, and proof-to-action binding. For checked proofs it
reconstructs the expected arithmetic Lean source and invokes Lean directly.
Failed proof attempts remain valid records only when they carry diagnostics.

## CPU qualification

The bounded qualification used the external Jevlike checkout at
`94f5fd1b0b11d52bbdfdf4e0ee6aa96b568f8452` and a copied checkpoint in an
owner-only external custody root. The checkpoint and qualification output
remain outside this repository.

Qualification result:

- Status: `QualifiedAdapterBoundary`.
- Checkpoint digest:
  `sha256:d73f6f48d82b7b40807903131b50e672bb76db0528264f2f86009a36c5a5ee39`.
- Custody manifest digest:
  `sha256:5a2ca799d101311148fd76a6ac7c396008f0d925e18a2e8b47474d880f448dcd`.
- Bundle digest:
  `sha256:94672e2c147a1034630b152067c73b8252460fcc4643d7028c378daad24bc1b3`.
- Runtime: CPU, Python 3.14.5, PyTorch 2.13.0.
- Exact checks: permutation sensitivity, repeatability, exact probability
  capture, unchanged toy-host snapshot, and independent Lean bundle validation.
- Independent checked proofs: `1`.

The report is at the external custody output path
`/Users/shaanp/.codex/runs/jevlike-adapter-independent-validation-v1-qualification/qualification-report.json`.
It contains exact captured probabilities and is not a repository artifact.

## Reproduction

Prepare a new external custody root from an already available checkpoint:

```text
./scripts/python -B -m tools.proof_carrying_nano_jevlike_independent_validation_v1.qualification \
  --repo-root /absolute/path/to/composed-zk-benchmark-os \
  --prepare-source-checkpoint /absolute/path/to/checkpoint.pt \
  --custody-root /absolute/path/outside/the/repository/custody
```

Run one pinned CPU qualification with the resulting custody manifest:

```text
./scripts/python -B -m tools.proof_carrying_nano_jevlike_independent_validation_v1.qualification \
  --repo-root /absolute/path/to/composed-zk-benchmark-os \
  --custody-manifest /absolute/path/outside/the/repository/custody/checkpoint-custody.json \
  --upstream-root /absolute/path/to/jevlike-at-94f5fd1b0b11d52bbdfdf4e0ee6aa96b568f8452 \
  --output-root /absolute/path/outside/the/repository/qualification-output
```

Run the hermetic contract gate with:

```text
pnpm --ignore-workspace run verify:proof-carrying-nano-jevlike-independent-validation-v1
```

Every mutation governed by this record touches state slice
`proof-carrying-nano-jevlike-independent-validation-v1`.

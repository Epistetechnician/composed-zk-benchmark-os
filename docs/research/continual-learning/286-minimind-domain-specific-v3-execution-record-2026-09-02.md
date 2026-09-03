# MiniMind domain-specific continual-learning V3 execution record

State slice: `continual-learning-minimind-domain-specific-v3`.

## Current disposition

`ModelContractValid`; one bounded offline MiniMind campaign completed under
the fresh V3 independent signed receipt. The result remains capped at
`LocalDevelopmentMiniMindDomainSequenceQualificationV3`.

No provider call or network model/data acquisition ran. The model output is
aggregate-only; no raw prompts, tokens, activations, weights, gradients, or
per-trial stage payloads were retained.

## Synthetic execution

The fresh external source checkout is pinned to commit
`7a6fddd63a30c06b2fdd5fac4089922b29bc841b`. The fresh synthetic root is:

`/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v3-synthetic-20260902`

The independent validator returned `valid=true`, disposition
`SyntheticCandidate`, and `trial_count=108`. The tune lock selected
`domain_adapters`. The published result is aggregate-only; stage payloads,
records, tokens, weights, gradients, and model outputs were not written.

External artifact file SHA-256 values:

- `contract.json`: `87c3a560009efdc02aa5f3435a85a641d927ea48a8feb3007820d49db4495f72`
- `result.json`: `856037b04076d60040ae47fa166853d1858817746f35282968e11191699b5bfd`
- `source-manifest.json`: `c0f9a16c209373e242e127651dddf142a6884d6c978b2eb1a35ccb3b5c436e46`

## Independent authorization

The fresh packet received a certificate-backed independent signed `ACCEPT`.
The packet-bound execution receipt is:

`/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v3-execution-receipt-20260902.json`

Receipt SHA-256:

`77fc2e151fbb9c906766e103fb3f597ebcf412bdaee821983cd872c5d6fac968`

The receipt and frozen packet were revalidated by both the runner and the
independent validator before model execution.

## Model execution

The bounded model root is:

`/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v3-model-20260902`

The independent validator returned `valid=true`, disposition
`ModelContractValid`, and `trial_count=78`. The campaign used the pinned
MiniMind source checkout, the fresh V3 corpus, CPU execution, and one step per
domain stage. Fit and tune covered all fixed arms; after the predeclared tune
lock, assessment covered only the locked `sequential_full` arm.

Model `contract.json` SHA-256:

`7e2652f6f7d9b4c06c5bacc8472e5f1e2ed051495814b34a4fa51482058e2818`

## Local verification

- V3 focused tests: `11 passed`.
- V3 runner and independent validator compile successfully.
- V3 independent synthetic validator: `valid=true`, `108` aggregate trials.
- Root mode and exact-file-set checks passed on the canonical synthetic root.
- Root mode and exact-file-set checks passed on the canonical synthetic and
  model roots.
- The fresh packet-bound independent `ACCEPT` was valid before model execution;
  no V2 bytes were patched or rerun.

The V2 rejection remains terminal and is not repaired or rerun under V3.
Every mutation in this phase names state slice
`continual-learning-minimind-domain-specific-v3`.

# Proof-carrying symbolic transfer concrete refinement V2

State slice: `proof-carrying-symbolic-transfer-refinement-v2`.

Protocol identity: `weco-symbolic-discovery-transfer-refinement-v2`.

Status: `MACHINE_CHECKED_SCOPED / LOCAL_SYNTHETIC_ONLY`.

Claim ceiling: `LocalMachineCheckedFormalContractOnly`.

## Scope

This slice refines the abstract V1 Lean contract with a closed-world synthetic
evaluator. The candidate receives only canonical `PublicTask` values. Hidden
programs and assessment outputs remain evaluator-owned and are used only for
scoring and truth-mutation testing. No model, provider, external corpus,
network, spend, or accepted Evidence Ledger mutation is permitted.

The fixture contains fit, tune, and held-out episodes for seeds 101 and 202.
The reference public-only synthesizer enumerates the fixed primitive vocabulary
under each task's depth bound. The evaluator computes task and family metrics;
candidate-reported metrics are forbidden.

## Fail-closed checks

- Canonical JSON and exact schemas reject unknown fields and malformed rows.
- Candidate output requires one bounded discovery per task and unique IDs.
- Candidate output is repeated after hidden truth replacement; any change is
  rejected as leakage or nondeterminism.
- Family metrics sort by canonical family ID and are checked under reversal.
- Metrics are recomputed from assessment outputs and cannot be supplied by the
  candidate.
- Receipt fields, protocol identity, claim ceiling, and every digest are
  validated; receipt tampering or unknown fields fail closed.
- A generated witness is compiled by the pinned Lean `v4.30.0` kernel against
  `MathDiscovery.RefinementWitness`.

## Verification

From the repository root, with the pinned Lean toolchain available:

```text
bash scripts/verify_math_discovery_refinement_v2.sh
PYTHONPATH=. python3 -m unittest discover -s tools/proof_carrying_symbolic_transfer_refinement_v2/tests -v
```

The protocol emits a temporary deterministic receipt and Lean witness, then
removes them. The receipt binds evaluator, V1 formal contract, canonical
fixture, configuration, trace, and witness digests. The witness proves only
that this bounded receipt schema and its declared checks have the exact V2
identity; it is not a proof that arbitrary Python execution refines Lean.

## Authority boundary

The V1 local-continuation exception permits this synthetic refinement without
an independent reviewer. It does not authorize scientific or model-bearing
execution, external custody, provider calls, spend, benchmark/SOTA/breakthrough
claims, production use, or any claim above the stated ceiling. A verified ZK
execution relation requires a fresh protocol identity and separate authority
record.

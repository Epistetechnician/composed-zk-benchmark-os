# Proof-carrying nano interpretability V1

State slice: `proof-carrying-nano-interp-v1`.

Status: `LOCAL_SYNTHETIC_MACHINE_CHECKED / INDEPENDENT_REVIEW_REQUIRED`.

This slice implements the Phase 0 to Phase 1 tracer bullet for the proof-
carrying nano-model design: a deterministic toy host slice, one read-only
feature-detection nano, a hypothesis-ranking nano, a concurrent append-only
store, a deterministic toy causal-intervention nano, and Lean 4 proof
attempts for exact feature lookup, finite ranking invariants, and intervention
effects.

## Implemented contract

- `ToyHostSlice` exposes immutable checkpoint, layer, site, seed, and integer
  activation capture.
- `FeatureDetectorNano.attach` binds a nano identity to one host layer/site;
  `NanoAttachment.run` cannot mutate the host and emits a digest-bound
  `MiniAction`; `run_and_record` persists the action and its proof attempt.
- `HypothesisOptionSet` is a closed, versioned, digest-bound schema for an
  ordered list of `feature`, `circuit`, or `intervention` candidates. Its
  context digest, scorer identity, option order, and option identities all
  participate in the option-set digest.
- `HypothesisRankingNano` attaches read-only to the toy host and emits a
  `HypothesisOnly` action. `DeterministicOptionScorer` can derive stable
  integer weights locally or accept caller-supplied non-negative integer
  weights; no Jevlike or model import is used.
- Ranking outputs use exact numerator/denominator records. The Lean artifact
  proves denominator normalization and that the selected index is the first
  maximum and resolves to the logged candidate and kind.
- `InterventionSpec` is a digest-bound replacement operation tied to the
  captured host-context hash. `CausalInterventionNano` is read-only: it
  computes a pure toy pre/post activation, exact vector/scalar deltas, and an
  explicit no-op control. It may reference a ranking action by digest, but it
  never promotes that ranking beyond `HypothesisOnly`.
- The intervention Lean artifact proves replacement semantics, vector delta,
  scalar effect, and no-op identity. `ConcurrentStore` indexes checked
  intervention observations separately and rejects unknown ranking references.
- `ConcurrentStore` uses SQLite WAL mode and short `BEGIN IMMEDIATE`
  transactions. Exact duplicate action/proof submissions are idempotent;
  altered payloads are rejected.
- Each action stores prompt, activation, output, timestamp, action version,
  host context hash, nano identity, layer/site, and a feature claim.
- `LeanProofEngine` generates a closed-world Lean theorem and records
  `checked` or `failed` status plus source and diagnostics. The store
  re-checks every submitted `checked` artifact against the pinned Lean
  project, so a status-only forged proof is rejected.
- Proven claims can be queried by layer and feature. Checked rankings are also
  available through `query_hypotheses`, and checked interventions through
  `query_interventions`; contradictory checked feature claims, rankings, and
  interventions have separate conflict queries.
- `NanoAttachment.replay` reconstructs an action from persisted inputs and
  requires the same action digest. `validate_integrity` detects tampered
  action/proof payloads and can re-run checked proofs.
- `export_bundle` and `write_bundle` produce a deterministic, digest-bound
  bundle containing the action, every proof attempt, and a human-readable
  summary. Ranking bundles carry `status: HypothesisOnly`; `validate_bundle`
  verifies the digest, bindings, status, and checked proofs.
- `HypothesisRankingNano` is a deterministic synthetic ranking contract. It
  can derive stable local weights or consume caller-supplied non-negative
  integer scores, records an ordered option-set digest and exact rational
  probabilities, marks the result `HypothesisOnly`, and carries a Lean proof
  of normalization and selected-index consistency. It is not an executable
  Jevlike model adapter.

## Verification

```text
pnpm --ignore-workspace run verify:proof-carrying-nano-interp-v1
```

The formal checker is also directly runnable:

```text
bash scripts/verify_proof_carrying_nano_interp_v1.sh
```

## Claim ceiling

The Lean kernel proves only exact lookup semantics, finite integer ranking
invariants, and the pure replacement semantics of a captured toy record. This
does not prove that a real neural host, activation hook, feature label, causal
intervention, circuit, scorer, or nano-model refines the toy semantics. A
`HypothesisOnly` result and an `InterventionObserved` toy result are not a
feature, circuit, intervention, alignment, benchmark, or production claim.
The slice creates no frontier-model evidence, scientific claim, production
authority, accepted Evidence Ledger mutation, or independent review. The
current ceiling is
`LocalSyntheticToyHostFeatureLookupHypothesisRankingAndToyInterventionOnly`;
independent review remains required.

## Next refinement boundary

The separately reviewed Jevlike adapter refinement is now implemented under
the [pinned Jevlike adapter slice](proof-carrying-nano-jevlike-adapter-v1.md):
it uses a new protocol identity, pins the external revision, remains a
`HypothesisOnly` scorer, and quantizes floating-point output before any proof
attempt. Swarm scheduling and dashboard work remain later phases.

The external `jevlike` repository remains a reference-only integration target
under the [Jevlike integration boundary](jevlike-integration-boundary-v1.md).
Its weights, datasets, traces, and generated outputs are not inputs to this
slice.

Every mutation governed by this record touches state slice
`proof-carrying-nano-interp-v1`.

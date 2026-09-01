# Plasticity guard with reversible adapters V1 execution record

Date: 2026-08-28.

State slice: `continual-learning-plasticity-guard-reversible-adapter-v1`.

Status: `COMPLETED / DEVELOPMENT_CANDIDATE`.

The protocol and explicit user authorization are recorded in:

- `89-plasticity-guard-reversible-adapter-v1-protocol.md`
- `90-plasticity-guard-reversible-adapter-v1-execution-authorization-2026-08-28.md`

The implementation is additive and uses the already-cached Gemma3 1B PT MLX
checkpoint offline. It will publish only to new external PrimaryED and DAed
roots. No result, assessment metric, or scientific classification exists in
this record until the runner completes qualification, prediction locking,
assessment, independent validation, and mirror equality checks.

The final record must report the primary paired assessment endpoint, every
hard guard, base-model manifest equality, prediction-lock digest, independent
validator receipt, and the exact bounded classification. Astral integration
and ZK/PQC backends remain `not_run`.

## Execution receipt

PrimaryED active root:

`/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/continual-learning-plasticity-guard-reversible-adapter-v1-20260828-r1`

DAed mirror root:

`/Volumes/DAed/Archives/composed-zk-benchmark-os/continual-learning-plasticity-guard-reversible-adapter-v1-20260828-r1`

Qualification passed. Native reload maximum logit delta was `0.0`, zero-adapter
maximum logit delta was `0.0`, the trained adapter produced a nonzero probe
delta of `4.59375`, and copied adapter save/restore maximum logit delta was
`0.0`.

The fixed factorial completed eight cases: two seeds (`1739`, `1741`), two
orders, and two arms. Fixed cadence committed all six candidate updates in
every case. `plasticity_guard` committed one and rolled back five in every
case. All update attempts used the same four rows, three iterations, batch
size, four trainable layers, optimizer, learning rate, and seed-plus-step
contract in both arms.

The primary paired held-out assessment endpoint passed:

- mean guarded-minus-fixed adaptation improvement: `0.064052287` NLL/token;
- deterministic 10,000-resample 95% interval: `[0.031372549, 0.087581699]`;
- positive paired cases: `4/4`;
- preregistered threshold: `0.010` NLL/token;
- classification: `DevelopmentCandidate`.

All hard guards passed. Assessment repeat mean-NLL deltas were `0.0`; fit
forgetting fractions ranged from `-0.270142180` to `-0.037237644`; tune ECE
changes ranged from `-0.016345933` to `0.017068781`; the cached model
manifest was unchanged; and PrimaryED and DAed were byte-identical at
validation. Prediction locking was confirmed before assessment, and the
independent aggregate-only validator returned `valid: true` for both roots.

Receipt linkage:

```text
config_sha256: 2bb0c2dce8b88aa30551bd56229925875b2e81750a7099cf60daed706ad931ed
qualification_sha256: 7360d8a2e0b76f95cd351bfce0ad73fb7ef92fd1adf31cb37bce284d1d471fe5
prediction_lock_sha256: 26d569d52b122ceff911995afeb1a0b4f797604809b1a7c9e209eefbe45f5c19
results_sha256: 46d0654b199205b2957e5a1fb758c1989c377db7d6ab86eaa0f6440de3bd8316
model_manifest_sha256: 69f078b42d4521d3e53f0c388a20fa6cf32b4df7ea6535b0eb9da6ccef75c256
corpus_manifest_sha256: c7b3763dc040a283aea105a6c1df843776b29f33e4fab77f319d81a79502e1d0
```

The prediction-lock value above is copied from the published receipt; no
assessment data is added to the lock. Astral integration and ZK/PQC backends
were not run.

This result is bounded local feasibility evidence for the declared Gemma3,
NEWSROOM cohort, adapter budget, and guard. It does not establish a general
continual-learning improvement, a neuroscience-of-AI result, an Astral
breakthrough, introspection, causal self-modeling, benchmark superiority, or
production readiness. The two earlier validator-linkage failures are preserved
as recoverable forensic artifacts under DAed and are not valid result roots.

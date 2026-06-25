# Benchmark Taxonomy

Benchmark Families are generated from Semantic IR and expected verdicts. Each family should include positive and negative cases when the target backend supports them.

| Family | Purpose | Tunables | Expected Metrics | Mutation Opportunities | Evidence Expectation | Adapter Suitability |
|---|---|---|---|---|---|---|
| Baseline FSMs | Establish correctness and overhead floor. | state count, transition count | verifier latency, constraint count | corrupted guards, semantic no-op drift | Level 1+ after local replay | Mock JSON, zk-Harness, formal lanes |
| Branching FSMs | Stress guarded transition selection. | branching factor, guard complexity | constraint count, negative-test result | corrupted guards, trace ordering corruption | Level 1+ | zk-Harness, formal lanes |
| Bounded loops | Test loop bounds and counters. | loop depth, bound policy | prover time, constraint count | bad counters, invalid unroll bounds | Level 1+ | zk-Harness, clean, zkLean |
| Nested loops | Stress trace length and dependency ordering. | nesting depth, stride | prover time, memory use | stale reads, ordering corruption | Level 1+ | zk-Harness |
| Recursive envelopes | Stress recursion-depth binding. | recursion depth, digest shape | proof size, recursion tolerance | recursion-envelope mismatch | Level 1+ before gnark; higher later | gnark later, zk-Harness |
| Memory-heavy state machines | Stress RAM-like state. | memory footprint, read/write ratio | memory use, trace export | stale state reads, witness aliasing | Level 1+ | zkLean, Garden, zk-Harness |
| Guard-heavy machines | Stress constraints around predicates. | guard count, expression size | constraint count, failure coverage | corrupted guards, invariant weakening | Level 1+ | formal lanes, zk-Harness |
| Nondeterministic machines | Expose backend assumptions about choice. | nondeterminism policy | inconclusive/capability gaps | nondeterministic transition injection | Capability-aware evidence | Formal lanes first |
| Public/private boundary stress | Test witness/input separation. | boundary complexity | boundary-check result | witness aliasing, boundary mismatch | Level 1+ | zkML, formal lanes |
| Stale-read stress | Detect old state reuse. | read/write delay | unsound-acceptance detection | stale state reads | Level 1+ | zk-Harness, formal lanes |
| Counter consistency cases | Test monotonicity and exact bounds. | counter size, overflow policy | negative-test result | bad counters | Level 1+ | zk-Harness |
| zkML/control-flow mixed workloads | Bind model-like outputs to decisions. | model size, threshold policy | zkML metrics, proof time | boundary mismatch, observation omission | Narrow benchmark evidence later | zkonduit adapter |
| Recursion aggregation cases | Aggregate evidence envelopes. | depth, aggregation width | recursion tolerance, proof size | envelope mismatch | Recursion evidence only | gnark later |
| Formal-only semantic cases | Prove tiny scoped properties. | property scope | proof status | invariant strengthening/weakening | Level 4/5 when proved | clean, zkLean, Garden |
| Negative-test-only cases | Focus on rejected traces. | mutation class | failure coverage | all malicious classes | Backend capability evidence | Mock, formal, selected benchmark lanes |

## Evidence Rule

Benchmark family definitions are Level 0 until replay artifacts, formal artifacts, or independently reproduced evidence exist. A successful proof is not automatically evidence that the source spec was meaningful.

## Local v0 Implementation Status

Implemented locally in Phase D/E:

- Baseline FSMs: deterministic generator, concrete instance metadata, accepted/rejected traces, local oracle evaluation.
- Branching FSMs: deterministic generator with guarded branch selection, accepted/rejected traces, local oracle evaluation.
- Bounded loops / bounded counter loops: deterministic generator with counter, bound, invariant, accepted/rejected traces, local oracle evaluation.

Implemented locally in Phase 154:

- Nested loops: deterministic generator with two stacked bounded loops, inner/outer counters, inner/outer `LoopSpec` entries, an inner-bounded invariant, accepted/rejected traces, local oracle evaluation.
- Guard-heavy machines: deterministic generator with acquire/release/advance/finish transitions exercising `GuardExpr::And`/`GuardExpr::Or`, an `advance_until_bound` `LoopSpec`, a `locked_implies_value_at_or_below_bound` invariant, accepted/rejected traces, local oracle evaluation.

Implemented locally in Phase 164:

- Recursive envelopes: bounded unfold/seal machine with `envelope_digest` loop metadata, accepted/rejected traces, local oracle evaluation.
- Memory-heavy state machines: multi-slot write/read ordering machine, accepted/rejected traces, local oracle evaluation.
- Public/private boundary stress: nonce binding with witness-policy metadata, accepted/rejected traces, local oracle evaluation.
- zkML/control-flow mixed workloads: confidence/threshold guarded control-flow machine with observations, accepted/rejected traces, local oracle evaluation (metadata only; no zkML execution).

Future families:

- Nondeterministic machines.
- Recursion aggregation cases.
- Formal-only semantic cases.

Generated families are local semantic fixtures. They are not official benchmark evidence and do not carry performance metrics.

## Phase K Local Soak Profiles

Phase K local soak profiles exercise the existing local families only:

- BaselineFsm
- BranchingFsm
- BoundedCounterLoop

Local soak profiles do not add new Benchmark Families. They are operational stress tests of the benchmark OS pipeline: deterministic generation, Mutation Variant production, Oracle replay, local pack read/write paths, internal benchmark OS telemetry, local health report creation, and failure corpus extraction.

Soak profiles are not ZK backend benchmark suites. Local soak telemetry is not official benchmark evidence. Internal timing telemetry is not ZK backend performance. Failure corpus entries are reproduction aids, not accepted evidence.

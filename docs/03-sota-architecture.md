# SOTA Architecture

## SOTA Wedge

The SOTA wedge is control-flow semantic benchmark generation with formal hooks and adversarial mutation scoring. This project does not claim SOTA measured results. It defines a system shape for producing stronger benchmark evidence later.

## Five Layers

1. Specification DSL: declares machines, states, fields, transitions, guards, loops, invariants, observations, targets, mutations, evidence, traces, expected results, oracle, witness policy, public inputs, private witnesses, and semantic equivalence classes.
2. State/Loop Generator: expands seeds into Benchmark Families with tunable state count, branching factor, loop depth, recursion depth, guard complexity, memory footprint, nondeterminism, public/private boundary complexity, trace length, witness shape, and equivalence class.
3. Mutation Engine: emits valid, near-valid, malicious, and invalid Mutation Variants with Expected Verdicts.
4. Multi-Backend Adapter Layer: wraps benchmark, formal, proof, zkML, and local evidence lanes.
5. Scoring And Evidence Ledger: creates Evidence Records and Score Reports with performance and soundness separated.

## Canonical Pipeline

```text
Surface DSL
  -> parsed AST
  -> canonical semantic IR
  -> generated benchmark family
  -> concrete benchmark instance
  -> mutation variant
  -> backend artifact
  -> replay result
  -> evidence record
  -> scored report
```

## Semantic IR At The Center

Semantic IR is the shared truth boundary. It carries:

- machine and state definitions,
- transition relation,
- trace validity policy,
- oracle definitions,
- witness and public/private boundaries,
- expected verdicts,
- mutation provenance,
- evidence requirements.

Adapters consume Semantic IR-derived benchmark instances. They do not define semantics.

## Architecture Diagram

```text
                                 +----------------------+
                                 | Source Inventories   |
                                 | zk/formal/local refs |
                                 +----------+-----------+
                                            |
                                            v
+-------------+    +-------------+    +-------------+    +-------------------+
| Surface DSL | -> | Parsed AST  | -> | Semantic IR | -> | Benchmark Family  |
+-------------+    +-------------+    +------+------+    +---------+---------+
                                           |                         |
                                           v                         v
                                  +----------------+       +-------------------+
                                  | Oracle Model   |       | Benchmark Instance|
                                  +-------+--------+       +---------+---------+
                                          |                          |
                                          v                          v
                                  +----------------+       +-------------------+
                                  | Expected Verdict|<-----| Mutation Variant  |
                                  +----------------+       +---------+---------+
                                                                    |
                                                                    v
            +-------------+  +-------------+  +-------------+  +-------------+
            | zk-Harness  |  | formal lanes|  | gnark recur |  | zkML lanes  |
            +------+------+  +------+------+  +------+------+  +------+------+
                   |                |                |                |
                   +----------------+----------------+----------------+
                                    |
                                    v
                          +-------------------+
                          | Evidence Record   |
                          +---------+---------+
                                    |
                                    v
                          +-------------------+
                          | Score Report      |
                          +-------------------+
```

## Why Existing Benchmark Repos Become Adapters

Existing benchmark repos already know how to execute, prove, verify, or report metrics in their domain. This project owns semantic generation and expected verdicts. Wrapping avoids copying feature sets and keeps maintenance risk bounded.

## Why Formal Systems Become Evidence Lanes

clean, zkLean, and Garden can produce scoped formal evidence in future phases. They should not be treated as global truth. A machine-checked proof for one transition property does not prove the full benchmark OS.

## Why zkML Benchmarks Are Narrow Workload Adapters

zkML workloads add mixed-domain stress, but the project center is control-flow semantics. zkML adapters should test stateful workflows that combine inference-like workloads with guards, witnesses, and trace policies.

## How Mutations Create Soundness Stress

Mutations generate expected-reject or expected-unsound-if-accepted cases. The benchmark becomes useful when a backend accepts a variant the oracle says should be rejected, or when a backend cannot express the required negative test capability.

## Separate Performance And Soundness Scoring

Performance score covers prover time, verifier latency, proof size, memory, constraint count, and recursion tolerance. Soundness-related scores cover negative-test handling, unsound-acceptance detection, trace export, formal evidence, and oracle alignment.

## Claim Boundaries Prevent Hype

The evidence ledger must cap claims:

- Level 0: design note only.
- Level 1: local replay evidence.
- Level 2: reproducible benchmark artifact.
- Level 3: cross-backend replay evidence.
- Level 4: formal property statement.
- Level 5: machine-checked proof for a scoped property.
- Level 6: independently reproduced evidence.

## Risks And Mitigations

| Risk | Mitigation |
|---|---|
| Adapter work swallows core semantics. | Implement DSL/core schema first. |
| Formal evidence is overclaimed. | Bind every proof to scope and claim boundary. |
| Negative tests are too backend-specific. | Use capability flags and expected verdicts. |
| One aggregate score hides failures. | Keep score axes visible. |
| zkML broadens scope too early. | Keep zkML to narrow workload manifests. |


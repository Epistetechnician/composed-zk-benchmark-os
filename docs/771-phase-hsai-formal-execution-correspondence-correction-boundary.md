# Phase 771 HSAI Formal Execution Correspondence Correction Boundary

## Status

Complete as a documentation-first executor-correspondence audit and correction
boundary.

State slice:
`phase-771-hsai-formal-execution-correspondence-correction-boundary`.

Classification: `ExecutableCorrespondenceMismatchRecorded`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Audit Verdict

The Phase 770 plan is a deterministic conceptual inventory, not an executable
operation plan. Its 65-operation digest remains the immutable identity of that
inventory:

```text
1644a895733d769fbe89795cc3fc7d4886d71b03c8c28b9f1866f5a075a1db14
```

It must not be used as the executor-binding digest. Preserving it while adding
executors would encode inherited command aggregation, network-capability
overreach, incomplete filesystem contracts, and incomplete cleanup results.
A versioned plan is required before operation-to-executor materialization.

No Phase 770 bounded operation currently has a complete inherited
`CommandSpec`. Every one lacks exact absolute status/stdout/stderr paths; most
also lack one or more exact argv, cwd, replacement environment, timeout, cap,
or expected-outcome fields. The timeout fixture references `$RUN`, which the
current command environment allowlist cannot carry. The Phase 720 direct Lean
checks require explicit `-o` destinations that are absent from the older Phase
678 argv. These are specification conflicts, not implementation defaults.

## Controlling Source Order

Phase 772 must normalize inherited contracts in this precedence order:

1. Phase 744 controls the complete stage order.
2. Phase 753 controls dirty-primary preservation and detached execution.
3. Phase 757 controls independent Charon source-identity producers and
   immediate assertions.
4. Phase 761 controls the bounded raw-parser self-test and standalone
   acceptance.
5. Phase 763 controls Rust identity and marked-component acceptance.
6. Phase 749 controls committed helper identities and helper CLIs.
7. Phase 742 controls archive profiles; Phase 732 controls exact fixtures and
   the dedicated loopback lifecycle.
8. Phase 724 controls the fourteen-`rfl` witness; Phase 720 controls direct
   `.olean` order; Phase 702 controls exact client metadata.
9. Phase 678 controls remaining command, environment, cache, sandbox,
   extraction, checking, retention, cleanup, and claim details.

Later corrections control only their named conflict. Missing fields are
missing specifications; they may not be guessed from shell history, host
state, imports, executable discovery, or convenience.

## Required Cardinality Corrections

| Phase 770 operation | Problem | Phase 772 requirement |
|---|---|---|
| `capture-rust-identities` | Aggregates six exact commands and twelve transcript files. | Split into one bounded operation per child invocation, each followed by its typed acceptance. |
| `hash-charon-paths` | Aggregates five independently bounded `shasum` producers. | Split into five producers with one immediate comparison each. |
| `assert-charon-paths` | Compresses five regular/non-symlink facts. | Bind five typed path assertions to the corresponding source identities. |
| `assert-charon-stability` | Requires fresh commit, status, and five hash producers after prior assertions. | Represent every fresh child command explicitly; do not run subprocesses inside an assertion executor. |
| `run-sandbox-controls` | Aggregates process-positive, DNS-negative, and direct-IP-negative commands. | Split all child invocations and add the inherited pre-closure hostname-positive control. |
| `verify-charon-binaries` | Includes fresh version and native-binary inspection commands under an internal assertion label. | Split every child invocation from pure acceptance predicates. |
| `accept-lean-identities` | Depends on fresh Lean and Lake identity commands not represented as producers. | Add exact bounded identity producers before acceptance. |
| `verify-frozen-repository` | Compresses Git, scanner, disk, tool, and root probes. | Split child invocations from pure checks and type every resulting artifact. |
| `snapshot-primary` | Calls Git and produces durable state while labeled as an assertion. | Model bounded snapshot producers and a typed primary-snapshot artifact before root creation. |

The dedicated loopback operation is the sole permitted multi-process lifecycle
operation. It remains one closed typed controller because listener readiness,
positive probe, byte-identical sandboxed-negative probe, termination, and reap
must be evaluated as one lifetime. It is not a generic background-process
escape hatch.

## Phase 772 Plan V2 Contract

Phase 772 may extend only
`tools/hsai-formal-preflight/execution_state_machine.py`, its focused tests, one
implementation note, the Phase 770 next-gate note, and standard mirrors. It
must introduce `hsai-formal-complete-operation-plan-v2` without mutating the
meaning or published digest of v1.

### Bounded child rule

Every actual child invocation has exactly one bounded operation and exactly
one future `CommandSpec`. A bounded operation must bind an absolute argv
template, exact cwd template, complete replacement environment, timeout,
stdout/stderr caps, expected reason/return/signal, and three unique transcript
artifacts. Generic shells remain prohibited except the two byte-exact Phase
732 fixtures already admitted by Phase 768.

The v2 tests must prove set equality among bounded operation ids, future command
binding ids, and declared transcript producer ids. Group labels and assertions
may not hide a child process.

### Capability rule

Stage network policy becomes a ceiling, not an inherited command capability.
Every executable operation must declare exactly one capability:

```text
host-offline
external-acquisition
controlled-loopback
sandbox-closed
```

Only an explicit closed set of acquisition ids may declare
`external-acquisition`. The plan must include an irreversible
`external-network-closed` barrier. No later operation may declare acquisition.
The loopback controller alone may declare `controlled-loopback`; every formal
backend, build, extraction, and kernel-check command must declare
`sandbox-closed`.

### Typed template and artifact rule

The plan must define one placeholder registry. Each placeholder has a type,
producer, allowed consumers, and canonical resolved-root class. Resolution is
single-pass. Unknown, unresolved, recursive, repeated-brace, NUL, non-UTF-8,
relative, noncanonical, traversal, owner-escaping, or symlink-ancestor paths
fail before any mutation.

Every artifact declaration must bind:

```text
artifact_id, producer_operation_id, path_template, artifact_kind,
mode, size_or_bound, schema_or_digest_policy, consumer_operation_ids
```

The immutable path-normalized plan digest, executor-binding digest, and
machine-specific resolved-attempt digest are separate identities. A resolved
machine path may never enter the immutable plan digest or retained proof slice.

### Closed non-producer rule

Internal assertions become a closed tagged union of pure acceptance predicates
over prior artifacts or immutable constants. Filesystem operations become a
closed union of:

```text
owned-root-setup
exact-file-set-materialization
exact-tree-removal
retention-transaction
```

No generic callback, arbitrary path list, recursive delete primitive, shell
text, or subprocess call is permitted inside these executors. Each mutation
must name its state slice, ownership receipt, preconditions, postconditions,
mode, replacement policy, and rollback or terminal-failure behavior.

### Cleanup rule

Cleanup is an ordered aggregate, not one Boolean result. It must preserve the
first operational failure, collect every cleanup failure separately, attempt
all independently safe cleanup steps, and always perform primary verification
last. It may remove only roots carrying both absence and successful-creation
ownership receipts. It must never mutate the primary checkout, `$HOME/.cargo`,
repository targets, unrelated caches, or unowned worktrees.

The result schema must distinguish:

```text
complete
failed-cleaned
cleanup-failed
```

and retain the original failure plus ordered cleanup-step results and failure
codes.

## Required Hermetic Tests

Phase 772 must prove:

- exact child-command cardinality and one-to-one binding coverage;
- no missing, duplicate, extra, or hidden producer;
- deterministic v2 serialization and a published v2 plan SHA-256;
- exact capability membership and irreversible network closure;
- rejection of every placeholder, path-escape, and symlink-ancestor class;
- artifact producer/consumer closure and identity drift rejection;
- closed non-producer variant coverage with no subprocess escape;
- first failure at every v2 operation blocks every normal successor;
- cleanup remains reachable from every failure;
- partial cleanup failure preserves the original failure and all cleanup
  results; and
- exact `/usr/bin/python3` binding for committed Python helper execution.

Phase 772 uses fake executors, hermetic temporary trees, and local process
fixtures only. It must not perform network acquisition, create persistent tool
roots, run Rustup, Charon, Aeneas, Lean, Cargo, Lake, SMT, Z3, COBALT, or a
formal backend, or generate a proof artifact.

## Exit Gate

Executor materialization remains prohibited until the versioned plan v2 is
committed, its cardinality and capability tests pass, every missing field is
represented as an explicit unresolved contract rather than guessed, and an
independent audit finds no hidden child process or owner-escaping mutation.

Phase 771 creates no executable executor coverage, backend result, proof
artifact, checker transcript, accepted evidence, Level2+, score axis, semantic
correctness, production readiness, SOTA, breakthrough, full-security claim,
external audit, or action authority.

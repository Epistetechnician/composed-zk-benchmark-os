# Phase 772 HSAI Formal Execution Command-Spec Completeness Stop

## Status

Stopped before implementation because inherited executor specifications are
incomplete.

State slice: `phase-772-hsai-formal-execution-command-spec-completeness-stop`.

Classification: `ExecutorSpecificationIncomplete`.

Execution status: `StoppedPreImplementation`. Evidence ceiling:
`Level1LocalReplayOrLower`.

## Stop Point

Phase 772 audited every Phase 770 bounded operation against the Phase 768
`CommandSpec` contract before changing Python source. None of the 35 entries
has a complete exact specification for all required fields:

```text
absolute argv
absolute canonical cwd
complete replacement environment
network capability
timeout
stdout cap
stderr cap
absolute status path
absolute stdout path
absolute stderr path
expected reason
expected return code
expected signal
```

Every entry lacks exact status/stdout/stderr path templates. Several entries
also aggregate multiple child commands or lack exact argv, cwd, environment,
timeout, or outcome fields. Therefore Phase 772 stopped before modifying
`execution_state_machine.py`, constructing plan v2, creating attempt roots, or
running any producer.

## Cardinality Conflicts

| Existing operation | Inherited requirement | Conflict |
|---|---|---|
| `capture-rust-identities` | Rustup version, three installed-component captures, rustc identity, and Cargo identity require separate bounded transcripts. | One operation cannot represent six independently accepted child commands. |
| `hash-charon-paths` | Five separate `shasum -a 256` producers with immediate per-path assertions. | One operation hides five statuses and ten streams. |
| `assert-charon-stability` | Fresh commit, status, and five hash producers after initial assertions. | Internal assertion would have to hide child processes. |
| `run-sandbox-controls` | Hostname-positive acquisition control, then separate sandboxed process-positive, hostname-negative, and direct-IP-negative commands. | One operation cannot encode four argv and mixed outcomes. |
| `verify-charon-binaries` | Fresh version, architecture, signature, dependency, adjacency, and driver-binding commands. | Internal assertion payload does not identify bounded producers. |
| `accept-lean-identities` | Separate Lean and Lake identity child commands precede acceptance. | Required producers are absent. |
| `verify-frozen-repository` | Git, scanner, disk, executable, and root probes. | Required child cardinality and transcript identities are not frozen. |
| `snapshot-primary` | Git `HEAD` and porcelain producers feed the snapshot. | The current internal helper invokes unbounded subprocesses. |

The Phase 732 loopback lifecycle remains the only authorized multi-process
typed operation because its listener and two probes must share one controlled
lifetime. It is not evidence that other producer aggregation is acceptable.

## Field Gaps By Producer Group

| Group | Known exact fields | Missing or conflicting fields |
|---|---|---|
| committed helper compile/tests | Interpreter and broad CLI intent. | Exact file order/discovery argv, cwd, environment, bounds, transcripts. |
| raw-parser self-test | Exact argv, `120s`, `1MiB/256KiB`, exit zero, canonical 31/0 result. | Cwd, replacement environment, transcripts. |
| four process fixtures | Exact argv, bounds, and outcomes. | Cwd and transcripts; timeout fixture needs `RUN`, which is absent from the current environment allowlist. |
| Rust acquisition | Asset identities, toolchain token, component set, stream caps. | Exact downloader/installer argv, cwd, full environment, timeouts, transcripts. |
| six Rust identities | Child argv, run cwd, core Rustup environment, caps, expected identities. | Six distinct operation bindings, timeouts, transcripts; Phase 763 marked output must supersede older unmarked parsing. |
| Charon source | Commit and five path/hash identities. | Exact init/fetch/checkout argv and bounds; decomposed identity and stability producers. |
| Aeneas/Lean assets | URLs, sizes, hashes, archive profiles, extraction intent. | Exact absolute downloader/extractor argv, cwd, environment, timeouts, transcripts; Lean extraction argv is not frozen. |
| dependency acquisition | Core Cargo/Lake argv, cwd, environments, caps, exit zero. | Timeouts and transcripts; direct `rustc_private` probe source/flags remain incomplete. |
| sandbox controls | Positive `/usr/bin/true` and direct-IP argv; paired hostname semantics. | Exact hostname argv, per-command bounds/transcripts, exact negative outcomes. |
| Charon build | Complete child Cargo argv, cwd/environment, cap, exit zero. | Timeout, transcript paths, resolved sandbox wrapper binding. |
| Charon/Aeneas backend | Core child argv, bounds, generated-output expectations. | Complete wrapper argv, some cwd/environment fields, transcripts. |
| direct Lean checks | Order, cwd/environment, bounds, output artifacts, exit zero. | Complete argv with Phase 720 `-o` destinations and transcripts; older Phase 678 argv is superseded. |
| final Lake build | Core argv, cwd/environment, bounds, exit zero. | Transcript paths and exact mutable artifact inventory. |

## Preserved Identities

The Phase 770 v1 digest remains unchanged and historical:

```text
1644a895733d769fbe89795cc3fc7d4886d71b03c8c28b9f1866f5a075a1db14
```

No plan-v2 digest exists. No executor-binding digest exists. No
machine-resolved attempt digest exists. The primary checkout's pre-existing
`crates/hsai-agent-admission/src/lib.rs` mutation remains outside this state
slice and was not staged or modified.

## Phase 773 Source-Normalization Gate

Phase 773 must be documentation-first. It may add one exact executor-source
normalization document and standard mirrors. It must not modify Python or Rust
source or run a producer.

For every actual child command, Phase 773 must publish one row containing:

```text
operation_id
controlling_phase_and_anchor
absolute argv template
canonical cwd template
complete replacement environment
capability
timeout and stream caps
three unique transcript artifact templates
expected reason, return code, and signal
typed input artifacts
typed output artifacts
acceptance operation id
resolution status
```

Rows with an unresolved field remain explicitly `blocked`; they do not receive
a guessed default. The document must also publish:

- the exact decomposed producer count;
- the closed external-acquisition id set;
- the irreversible network-closure position;
- the exact placeholder registry and path-containment classes;
- the closed non-producer variant inventory;
- aggregate cleanup step order and result schema; and
- a deterministic path-normalized source-ledger SHA-256.

Only after every required row is resolved and the source ledger is committed
may a later phase implement plan v2. That implementation remains hermetic and
cannot itself authorize live execution.

Phase 772 creates no executable plan, backend result, proof artifact, checker
transcript, accepted evidence, Level2+, score axis, semantic correctness,
production readiness, SOTA, breakthrough, full-security claim, external audit,
or action authority.

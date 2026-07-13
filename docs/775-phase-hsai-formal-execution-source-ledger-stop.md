# Phase 775 HSAI Formal Execution Source Ledger Stop

## Status

Stopped before expanding or hashing the command source ledger.

State slice: `phase-775-hsai-formal-execution-source-ledger-stop`.

Classification: `ExecutableIdentityAndAuditContractIncomplete`.

Execution status: `StoppedDocumentationOnly`. Evidence ceiling:
`Level1LocalReplayOrLower`.

## Stop Verdict

Phase 775 audited the committed Phase 774 resolution against the controlling
Phase 771 exact-command, typed-placeholder, sandbox-capability, artifact, and
retention rules. The literal Phase 774 arithmetic and its resolution-contract
SHA-256 are mechanically correct, but the underlying producer set and several
required fields are not complete enough to expand a truthful 84-row ledger.

No `hsai-formal-source-ledger-v1` digest exists. No plan v2, executor binding,
machine-resolved attempt digest, or live attempt is authorized.

## Blocking Contradictions

### Executable identity is not canonical

Phase 774 names `/opt/homebrew/bin/zstd` and requires that path to be regular
and non-symlink. A read-only host-path audit found:

```text
/opt/homebrew/bin/git  -> ../Cellar/git/2.47.1/bin/git
/opt/homebrew/bin/zstd -> ../Cellar/zstd/1.5.7_1/bin/zstd
/usr/bin/tar           -> bsdtar
```

The `zstd` rule is therefore false on the current host. The Git path is called
identity-pinned without freezing a canonical realpath, link text, or digest,
and the tar row similarly lacks a resolved executable identity. A future
ledger must bind executable placeholders to canonical regular-file targets,
link facts, and digests without putting a machine-specific resolved path into
the immutable path-normalized ledger.

The Phase 774 `zstd --force` argv also conflicts with exclusive absent-output
creation. The correction must remove replacement authority and bind creation
mode and ownership before decompression.

### The placeholder registry is not typed

Phase 771 requires every placeholder to declare its type, producer, allowed
consumers, and canonical resolved-root class. Phase 774 lists placeholder
names only. It also omits executable-identity placeholders and
`SANDBOX_PROFILE`.

The Phase 774 transcript digest binds one brace-expanded pseudo-template even
though the contract declares three distinct paths. The corrected contract must
bind explicit status, stdout, and stderr template fields.

### Sandbox capability is not bound to argv

Phase 774 labels native audits `sandbox-closed`, but the displayed argv arrays
start directly with `lipo`, `codesign`, `spctl`, or `otool`. The committed
bounded adapter executes the supplied argv directly; it does not add a sandbox
wrapper. A later contract must choose and freeze one mechanism:

1. `/usr/bin/sandbox-exec -f ${SANDBOX_PROFILE}` is part of every exact
   sandbox-closed argv; or
2. a separately typed executor transformation owns the wrapper and is covered
   by one-to-one correspondence tests.

No ledger row may claim `sandbox-closed` until that choice is explicit.

### Native-audit cardinality and target identity remain incomplete

The Phase 774 row `otool-load-commands-charon` targets `${CHARON_BIN}` even
though the inherited driver-binding requirement concerns
`${CHARON_DRIVER}` and its `librustc_driver` load path.

The 74-row Phase 773 base also did not decompose the inherited packaged-Aeneas
architecture, adjacency, `libgmp`, `codesign`, Gatekeeper, and dynamic-link
audits. Phase 774 mixes the historical ad-hoc-signed asset observation into
post-build Charon rows and leaves `spctl-charon`'s exact expected return code
blocked. The claimed exact total of 84 ordinary commands is therefore not a
canonical producer count, even though `74 + 4 + 1 + 5 = 84` is arithmetically
correct.

### Replacement environment and retained kernel evidence are incomplete

Phase 774 introduces environment keys that the current `CommandSpec`
allowlist rejects. That is an explicit future plan-v2 source change, not an
implicit ledger capability.

The current retention operation is only the label
`retain-path-free-proof-slice`. It does not type the generated `Types.lean`,
`Funs.lean`, witness, client metadata, provenance, direct Lean status records,
final Lake status, source/tool/plan digests, `.olean` digests, or a bounded
green-kernel result. Retention inputs and consumers must be frozen before a
live path can claim that generated Lean and kernel evidence will survive
cleanup.

## Preserved Results

The Phase 774 canonical JSON remains valid for its limited resolution
contract, and its SHA-256 recomputes as:

```text
d6117ddd618fde5369f109bc73487c5aa210d6b4c6adcc9039fc70f998dee3ae
```

That digest does not establish command completeness. The Phase 770 conceptual
plan digest also remains historical and non-executable:

```text
1644a895733d769fbe89795cc3fc7d4886d71b03c8c28b9f1866f5a075a1db14
```

The formal-preflight suite remains green at 83 tests. No Charon, Aeneas, Lean,
Lake, Rustup, Cargo, network, sandbox backend, or kernel command ran in this
phase. The pre-existing `crates/hsai-agent-admission/src/lib.rs` mutation
remains outside this state slice and was not modified or staged.

## Validation

Observed locally:

```text
repository hygiene: 1 passed
documentation claim-boundary coverage: 1 passed
Phase H source claim boundaries: 4 passed
Phase 765 escalation guards: 5 passed
formal-preflight suite: 83 passed
Phase 775 added-link integrity: passed
Phase 775 diff hygiene: passed
```

Root `pnpm run lint` is inapplicable because the repository has no root
`package.json`. No pull request is opened by this phase.

## Phase 776 Correction Boundary

Phase 776 must remain documentation-first. It may add one executable-identity,
sandbox-binding, producer-cardinality, and retention-schema correction
document plus standard mirrors. It must:

1. separate packaged-Aeneas asset audits from source-built Charon audits and
   publish the corrected exact producer count;
2. replace hard-coded symlink executables with typed identity placeholders and
   canonical realpath/link/digest acceptance rules;
3. remove overwrite authority from Lean decompression;
4. bind explicit status, stdout, and stderr transcript templates;
5. bind the sandbox wrapper or typed wrapper transformation;
6. correct the Charon-driver loader target and resolve every native-audit
   expected outcome;
7. define the complete replacement-environment vocabulary for a later source
   phase; and
8. define a path-free retained-kernel-evidence schema and exact retained
   artifact consumers.

Phase 776 may not modify Python or Rust source, create attempt roots, run a
producer, acquire assets, or execute Charon, Aeneas, Lean, Lake, Rustup, Cargo,
SMT, Z3, COBALT, a sandbox backend, or a kernel check. A fully expanded source
ledger remains a later phase after these corrections are complete.

Phase 775 creates no executable plan, source-ledger digest, backend result,
generated Lean source, retained kernel result, proof artifact, accepted
evidence, Level2+, score axis, semantic correctness, production readiness,
SOTA, breakthrough, full-security claim, external audit, or action authority.

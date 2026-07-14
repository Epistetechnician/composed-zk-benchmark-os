# Phase 786 HSAI Formal Native Transcript Dependency Route Correction

## Status

Complete as a documentation-first dependency and closure-route correction.

State slice:
`phase-786-hsai-formal-native-transcript-dependency-route-correction`.

Classification: `NativeTranscriptDependencyRouteCorrected`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Resolution Verdict

Phase 786 corrects the ordering defect recorded by Phase 785. It resolves no
Phase 780 closure lane and authorizes no fixture capture.

Phase 780 lane `L05` requires native transcript grammars selected by accepted
`codesign`, `spctl`, and `otool` identities. Lane `L09` defines the immutable
executable-role registry and machine-policy schema that gives those identities
meaning. The prior schedule placed `L05` before `L09`; Phase 785 proved that
the required raw positive and negative fixture corpus also does not exist.

The corrected dependency chain is:

```text
L09 immutable executable-role registry and machine-policy schema
  -> P01 native transcript fixture-acquisition protocol and readiness audit
  -> P02 conditional identity-bound local fixture corpus capture
  -> L05 native transcript grammars, typed outputs, and acceptance IDs
  -> L06, L07, L08, and L10 specialized closure
  -> L11 complete row expansion
  -> independent whole-ledger audit and conditional source-ledger digest
  -> earliest possible plan-v2 boundary
```

`P01` and `P02` are provenance prerequisites, not new Phase 780 blocker lanes.
The Phase 780 lane count remains eleven. They do not add command rows to the
Phase 778 operation order. They exist only to prevent unbound transcript bytes
or invented parser fixtures from becoming immutable ledger inputs.

## Authority Separation

The route separates four distinct authorities.

### Source authority

The immutable source ledger may name executable roles, requested-path
templates, identity classes, resolvers, consumers, machine-policy references,
and grammar-profile selectors. It may not contain an attempt's canonical path,
device, inode, observed executable digest, host identifier, or captured stream
digest as though those values were universal.

### Machine authority

A machine-resolved identity observation must bind the accepted role to the
requested path, ordered symlink hops, canonical regular file, device and inode,
SHA-256, mode, owner, applicable platform/build identity, and the exact policy
decision. These values are attempt- or capture-specific observations. They do
not become source-ledger defaults.

### Fixture authority

An observed positive fixture must bind raw stdout and stderr bytes to:

```text
fixture schema and fixture id
capture-protocol identity and digest
executable role and machine identity observation
exact ordered argv
cwd and replacement environment
target role and target identity observation
timeout and stream caps
reason, return code, and signal
stdout byte length and SHA-256
stderr byte length and SHA-256
platform/build disclosure
capture timestamp and nonsecret provenance
```

Every raw byte file must be declared, bounded, non-secret, regular,
non-symlink, digest-addressed, and read back before publication. Missing,
extra, duplicate, absolute, parent-traversing, replaced, or digest-mismatched
files fail the corpus.

### Grammar authority

A grammar profile may consume only fixture records whose executable identity
selector exactly matches that profile. Typed parser outputs and acceptance
operation IDs are `L05` outputs. A capture phase may not infer, publish, or
accept them.

## Positive And Negative Corpus Rules

`P01` must distinguish observed positive bytes from derived negative fixtures.

Observed fixtures are byte-exact outputs from one authorized capture. They may
not be reconstructed from Phase 667-669 summaries, terminal history,
screenshots, remembered output, documentation examples, or manually typed
records.

Derived negative fixtures may be created only from an admitted observed
fixture under a declared deterministic mutation record. The closed mutation
classes required by Phase 785 are:

```text
missing semantic record
duplicate semantic record
reordered semantic record
ambiguous semantic record
malformed semantic record
truncated semantic record
extra semantic record
```

Each derived fixture must identify its positive parent digest, mutation class,
exact byte transformation, expected parser rejection code, and resulting byte
digest. It must be labeled `synthetic-negative`; it may never be represented as
observed native-tool output.

Return-code-only, substring-only, unordered-record, best-effort, warning-only,
and unknown-version fallback profiles remain prohibited.

## Capture Readiness Gate

Phase 788 must complete a documentation-first readiness audit before Phase 789
can be authorized. For every distinct semantic shape needed by `N21`, it must
name:

1. the exact accepted executable role and identity selector;
2. the exact non-secret capture target source and target-identity rule;
3. the exact argv, cwd, replacement environment, timeout, and stream caps;
4. the required expected process outcome;
5. the raw-byte ownership, retention, redaction, and publication policy;
6. the corpus manifest and fixture path schema;
7. deterministic negative-fixture derivation rules;
8. independent reviewer inputs and failure conditions; and
9. an explicit statement that the capture is local regression material, not
   execution evidence for the 102-row formal campaign.

Unavailable packaged or source-built targets, unavailable policy-admitted
native-tool identities, unresolved stream ownership, missing redaction rules,
or incomplete semantic-shape coverage must stop before Phase 789. Phase 788
may authorize only a bounded local fixture-capture state slice after all
readiness inputs are exact.

## Conditional Capture Gate

Phase 789 is conditional on successful Phase 787 and Phase 788 closure. Its
future authorization must name every file and command it may create or run.
It may capture only the native transcript corpus defined by Phase 788.

Phase 789 may not run Rustup, Cargo, Charon extraction, Aeneas extraction,
Lean, Lake, SMT, Z3, COBALT, a proof backend, a kernel checker, or the 102-row
formal campaign. It may not publish parser grammars, mutate the accepted
Evidence Ledger, create Level2+ evidence, or populate score axes.

If any identity, target, argv, environment, process outcome, byte digest,
redaction result, mutation derivation, or corpus path differs from the
Phase 788 readiness contract, capture stops and `L05` remains open.

## Corrected Closure Schedule

This schedule supersedes Phase 784's Phase 785-795 schedule and every later
forward reference derived from it. Phase 780 lane definitions and exit criteria
remain authoritative.

```text
786 dependency route correction; no lane closure
787 L09 immutable executable-role registry and machine-policy schema
788 P01 native transcript fixture-acquisition protocol and readiness audit
789 P02 conditional identity-bound local fixture corpus capture
790 L05 native transcript grammars, typed outputs, acceptance IDs, and fixtures
791 L06 Charon driver preflight argv contract
792 L07 archive inventory contracts
793 L08 mutable output inventory contracts
794 L10 canonical JSONL serialization profile and conformance vectors
795 L11 row expansion tranche 001-038
796 L11 row expansion tranche 039-064
797 L11 row expansion tranche 065-102
798 independent whole-ledger audit and conditional digest publication
799 earliest possible plan-v2 boundary, only after Phase 798 success
```

The schedule does not assume that Phase 789 will run. A failed identity,
readiness, availability, provenance, or redaction gate produces another stop.
No later phase may skip `P01` or `P02` by embedding example text in a grammar
document.

`L06`, `L07`, and `L08` remain after `L05` to preserve one reviewed closure
output at a time. `L10` remains immediately before `L11` because canonical
serialization applies to the fully corrected successor-ledger inputs. All
`L01` through `L10` outputs remain prerequisites for `L11`.

## Phase 787 Gate

Phase 787 remains documentation-first. It may resolve only Phase 780 lane
`L09` by publishing the complete immutable executable-role registry and
machine-policy schema for exactly `E83`.

The registry must include exact role IDs, requested-path templates, identity
classes, safe resolvers, consumer operation IDs, acceptance-policy references,
and grammar-selector inputs for `/usr/bin/codesign`, `/usr/sbin/spctl`, and
`/usr/bin/otool`. It must prove exact role-to-row coverage and preserve machine
observations outside the immutable source ledger.

Phase 787 may not resolve an executable on the current host, publish an
observed executable digest, capture a transcript, create a fixture, define a
native transcript grammar, close `L05`, modify Python or Rust source, create an
attempt root, publish a source-ledger digest, or run any helper, test, producer,
network, Rustup, Cargo, Charon, Aeneas, Lean, Lake, native audit, sandbox, SMT,
Z3, COBALT, or kernel command.

## State Preserved

```text
Phase 778 ordinary operation count     102
Phase 778 operation-order digest       490c30a8098214754d20e4025696e2e3c702df8d4f7114a611157653ea7a4464
historical Phase 779 blocker count     1469
historical Phase 779 blocked rows      102
historical Phase 779 source digest     absent
resolved Phase 780 lanes               L01-L04
open Phase 780 lanes                   L05-L11
```

Historical Phase 779 JSONL is unchanged. Phase 786 creates no executable role
registry, machine policy, machine observation, fixture, grammar, parser output,
acceptance operation ID, source-ledger digest, plan-v2 object, or executor
binding.

## Source Correspondence

| Route fact | Controlling source |
|---|---|
| `L05` identity-bound grammar requirement | Phase 780 `Resolution Matrix` |
| `L09` role registry and external machine observations | Phases 776 and 780 |
| Exact `N21`, `E83`, and `R102` sets | Phase 780 `Exact Operation Sets` |
| Missing raw fixture corpus and required provenance | Phase 785 stop verdict |
| Separate bounded streams and no reconstruction | Phase 728 identity transcript closure |
| Exact fixture argv, bounds, outcomes, and hashes | Phase 732 fixture closure |
| Machine identity and output paths before launch | Phases 771 and 777 |
| Immutable 102-row order and digest | Phase 778 order correction |

## Claim Boundary

Phase 786 is routing metadata. It is not an executable registry, machine
policy, machine observation, fixture-acquisition authorization, fixture corpus,
native transcript grammar, parser, transcript, executable plan, executor
binding, backend result, generated Lean, retained kernel result, proof artifact,
checker transcript, accepted evidence, Level2+, score axis, semantic
correctness, production readiness, SOTA, breakthrough, full security, external
audit, or action authority.

## Phase 787 Forward Result

Phase 787 subsequently resolves `L09` at the immutable contract-input level in
`docs/787-phase-hsai-formal-executable-role-registry-machine-policy.md`.
It publishes 26 role definitions, four acceptance-policy classes, exact role
bindings for all 83 `E83` rows, an external machine-policy schema, an
attempt-specific observation schema, and exact `darwin-native-v1` selector
inputs. It records no machine observation or executable digest. `L05` through
`L08`, `L10`, and `L11` remain open. Phase 788 is authorized
documentation-first only for the `P01` fixture-acquisition protocol and
readiness audit.

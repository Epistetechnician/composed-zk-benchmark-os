# Phase 789 HSAI Formal Native Transcript Capture Prerequisite Route Correction

## Status

Complete as a documentation-first prerequisite and schedule correction.

State slice:
`phase-789-hsai-formal-native-transcript-capture-prerequisite-route-correction`.

Classification: `NativeTranscriptCapturePrerequisiteRouteCorrected`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Verdict

Phase 789 does not perform the previously scheduled `P02` capture. Phase 788
records `not-ready`, so capture has no authorization.

This phase replaces that invalid next step with a complete ordering contract
for the missing machine and target inputs. It also corrects two Phase 788
omissions:

1. built-row capture requires an accepted `SANDBOX_EXEC_EXE` observation in
   addition to the wrapped native-tool observation; and
2. input preparation cannot prepopulate `${CAPTURE_ROOT}` because Phase 788
   requires that root to be absent before capture.

No Phase 780 lane closes. Resolved lanes remain `L01-L04,L09`; open lanes
remain `L05-L08,L10-L11`. Historical Phase 779 JSONL remains unchanged with
1,469 blockers, 102 blocked rows, and no source-ledger digest.

## Corrected Authority Chain

```text
L09 executable-role and policy schemas
  -> P01A capture-input preparation contract (this phase)
  -> P01B conditional machine/target input materialization
  -> P02 conditional identity-bound corpus capture
  -> L05 identity-bound grammar closure
```

`P01A`, `P01B`, and `P02` are provenance prerequisites, not new Phase 780
lanes and not new rows in the immutable 102-operation order.

## Capture Executable Identity Set

The exact capture executable set is:

```text
SANDBOX_EXEC_EXE
CODESIGN_EXE
SPCTL_EXE
OTOOL_EXE
```

Packaged rows bind only their direct native role. Built rows 076-082 bind two
observations in argv order: `SANDBOX_EXEC_EXE` first and `CODESIGN_EXE` or
`OTOOL_EXE` second.

Future built-row positive provenance must add these fields to the Phase 788
shape:

```text
wrapper_role_id=SANDBOX_EXEC_EXE
wrapper_identity_observation_sha256
sandbox_profile_sha256=5c358b8d847211333e7ba22df82d84f796b5f30a41a2682209a949d783adbd08
wrapped_role_id
wrapped_identity_observation_sha256
```

`darwin-native-v1` continues to select the wrapped native grammar. The wrapper
has its own accepted Phase 787 observation and exact profile binding. Missing,
reordered, rejected, stale, or drifted wrapper identity fails before launch.

## Preparation And Capture Roots

Input preparation and capture use separate roots:

```text
PREPARATION_ROOT=/private/tmp/hsai-native-transcript-input-preparation-v1
CAPTURE_ROOT=/private/tmp/hsai-native-transcript-capture-v1
```

Phase 790 may create only `PREPARATION_ROOT`. It stages validated target bytes,
receipts, identity observations, policy input, profile source bytes, reviewer
assignments, and one handoff manifest there.

Phase 791 must begin with absent `CAPTURE_ROOT`. Its first bounded preamble
creates that root exclusively, copies the six accepted target bytes from the
handoff without mutation, materializes the byte-exact sandbox profile, and
read-back checks every digest. This slot-filling preamble is not target
production. Network access, extraction, compilation, target substitution, and
receipt repair are forbidden in Phase 791.

## P01B Preparation Role Closure

The future preparation operation set may consume only these executable
identity roles, whether as a direct argv executable or an explicitly pinned
compiler identity:

```text
CURL_EXE
GIT_EXE
TAR_EXE
RUSTUP_EXE
RUSTC_EXE
CARGO_EXE
SANDBOX_EXEC_EXE
```

The operator-reviewed machine policy must contain exact accepted host entries
for `CURL_EXE`, `GIT_EXE`, `TAR_EXE`, `RUSTUP_EXE`,
`SANDBOX_EXEC_EXE`, `CODESIGN_EXE`, `SPCTL_EXE`, and `OTOOL_EXE`.
`RUSTC_EXE` and `CARGO_EXE` use accepted owned-toolchain receipts under Phase
787 rather than host-policy entries.

No executable may be inferred from `PATH`, a shell, an unbound child process,
or a capability label. Preparation must stop if its final exact argv and
pinned-child identity set introduces another role.

## Conditional Preparation Order

Phase 790 may proceed only under a separately acknowledged implementation
slice and must checkpoint these stages in order:

1. accept one canonical operator-reviewed machine-policy object;
2. resolve and accept read-only identity observations for every host role in
   the preparation and capture sets without launching those executables;
3. acquire and accept the pinned Rust manifest and toolchain inputs;
4. acquire and accept exact Charon source commit
   `909ff09ad0f144f83d354f2c3d26f631fb9f8e9a` and its frozen source hashes;
5. acquire Aeneas archive
   `aeneas-macos-aarch64.tar.gz`, byte length `123234656`, SHA-256
   `fe706e847b01d83178e703898006bf372c5fcac007942b280efce776f5c35d45`;
6. validate archive safety before exact extraction into an absent staging root;
7. receipt-check the four packaged targets against the Phase 788 digests;
8. perform the exact deny-network sandboxed ordinal-073 Charon build;
9. receipt-check the two built targets through in-process Mach-O,
   architecture, signature, owner, mode, path, and SHA-256 acceptance;
10. copy all six accepted targets into the preparation handoff tree and
    read-back verify them;
11. materialize and verify the byte-exact sandbox profile source;
12. bind distinct machine-policy reviewer, capture operator, fixture reviewer,
    and grammar reviewer principals; and
13. publish one canonical handoff manifest and validation decision.

The machine-policy reviewer must be distinct from the capture operator. The
capture operator, fixture reviewer, and grammar reviewer must remain pairwise
distinct. The machine-policy reviewer may equal a later reviewer only when the
Phase 790 contract states that relationship explicitly and the reviewer did
not produce the reviewed object.

## Preparation Handoff Shape

Phase 790 may materialize only this logical tree outside git:

```text
machine-policy.json
identity-observations/CURL_EXE.json
identity-observations/GIT_EXE.json
identity-observations/TAR_EXE.json
identity-observations/RUSTUP_EXE.json
identity-observations/SANDBOX_EXEC_EXE.json
identity-observations/CODESIGN_EXE.json
identity-observations/SPCTL_EXE.json
identity-observations/OTOOL_EXE.json
owned-toolchain/RUSTC_EXE.json
owned-toolchain/CARGO_EXE.json
targets/packaged/aeneas
targets/packaged/charon
targets/packaged/charon-driver
targets/packaged/libgmp.10.dylib
targets/built/charon
targets/built/charon-driver
target-receipts/packaged-aeneas.json
target-receipts/packaged-charon.json
target-receipts/packaged-charon-driver.json
target-receipts/packaged-libgmp.json
target-receipts/built-charon.json
target-receipts/built-charon-driver.json
sandbox.sb
reviewer-assignments.json
handoff-manifest.json
validation.json
NONCLAIMS.md
```

The canonical handoff manifest binds every relative path, byte length,
SHA-256, source authority, producer checkpoint, policy/observation digest,
target receipt, reviewer assignment, and the Phase 788 protocol identity. It
also records `capture_authorized=false`. Phase 790 cannot authorize itself or
run the 21 capture commands.

Missing, extra, duplicate, absolute, traversing, symlinked, non-regular,
wrong-owner, wrong-mode, unlisted, stale, or digest-drifted content rejects the
whole handoff. Partial preparation output is deleted on failure.

## Phase 790 Boundary

Phase 790 is the only future phase permitted to attempt `P01B` materialization.
It may use network, Rustup, Cargo, Git, curl, tar, and the deny-network sandbox
only where the exact ordered preparation contract and accepted executable
identities permit them.

It may not run `codesign`, `spctl`, or `otool`; capture stdout or stderr for
grammar authority; derive fixtures; author a grammar; run Aeneas extraction,
Lean, Lake, SMT, Z3, COBALT, a proof backend, or a kernel checker; mutate an
accepted Evidence Ledger; create Level2+ evidence; or populate score axes.

If any producer argv, source authority, receipt schema, platform acceptance,
review assignment, cleanup rule, or handoff field remains unresolved, Phase
790 must stop before mutation rather than guess.

## Phase 791 Capture Boundary

Phase 791 is conditional on one accepted Phase 790 handoff digest and a fresh
read-back validation. It may run only the exact 21 Phase 788 capture argv
arrays plus the wrapper-identity correction in this phase.

It may create byte-exact observed positives, the seven deterministic synthetic
negative classes, the corpus manifest, deterministic forbidden-value scan, and
fixture/grammar-input review. It may not acquire, extract, compile, repair,
substitute, recapture under fallback identities, define parser semantics, or
close `L05`.

## Phase 792 Grammar Boundary

Phase 792 may attempt `L05` only after Phase 791 produces a complete accepted
corpus. It must publish selector-bound total grammars, typed outputs, exact
acceptance operation IDs, immutable fixture bindings, negative rejection, and
independent grammar review for all 21 rows.

Return-code-only, substring-only, unordered-record, warning-only, default,
nearest-version, and unknown-version fallback remain forbidden.

## Corrected Closure Schedule

This schedule supersedes Phase 786 from Phase 789 onward without rewriting
historical text:

```text
789 P01A capture-prerequisite route and preparation contract; no execution
790 P01B conditional machine-policy, identity, and six-target materialization
791 P02 conditional identity-bound native transcript corpus capture
792 L05 native transcript grammars, typed outputs, acceptance IDs, fixtures
793 L06 Charon driver preflight argv contract
794 L07 archive inventory contracts
795 L08 mutable output inventory contracts
796 L10 canonical JSONL serialization profile and conformance vectors
797 L11 row expansion tranche 001-038
798 L11 row expansion tranche 039-064
799 L11 row expansion tranche 065-102
800 independent whole-ledger audit and conditional digest publication
801 earliest possible plan-v2 boundary, only after Phase 800 success
```

The phase number is not evidence. Any failed preparation, capture, grammar,
inventory, row-expansion, canonicalization, or independent-audit gate produces
another stop.

## Post-Plan Boundary

Capture-only identity observations do not resolve the 102-row campaign
machine. After plan-v2, later explicit phases must still implement the
executor, resolve fresh complete-plan machine identities, implement retention,
run a dry preflight, and obtain live-attempt authorization. Only then may
bounded backend execution be considered.

## State Preserved

```text
Phase 778 ordinary operation count     102
Phase 778 operation-order digest       490c30a8098214754d20e4025696e2e3c702df8d4f7114a611157653ea7a4464
historical Phase 779 blocker count     1469
historical Phase 779 blocked rows      102
historical Phase 779 source digest     absent
resolved Phase 780 lanes               L01-L04,L09
open Phase 780 lanes                   L05-L08,L10-L11
P01 readiness decision                 not-ready
P01B preparation handoff               absent
P02 capture authorization              absent
```

Phase 789 creates no machine policy, identity observation, target, build
receipt, reviewer assignment, sandbox profile, handoff, transcript, fixture,
grammar, parser output, acceptance operation ID, executable plan, executor
binding, source-ledger digest, or evidence record.

## Source Correspondence

| Route fact | Controlling source |
|---|---|
| Not-ready result, target slots, capture protocol | Phase 788 readiness audit |
| Wrapper-first built-row role bindings | Phase 787 executable registry |
| Sandbox prefix and profile digest | Phase 776 execution contract correction |
| Identity-before-fixture authority | Phase 786 dependency route correction |
| N21, lane order, and exit gates | Phase 780 resolution matrix |
| Exact operation order | Phase 778 order correction |
| Source-build ordering | Phases 777 and 778 |
| Packaged/source-built authorities | Phases 667, 670, 678, 782, and 788 |
| Plan-v2 dependency on audited ledger digest | Phases 769, 780, and 786 |

## Claim Boundary

Phase 789 is prerequisite routing and preparation metadata. It is not a
machine-policy instance, machine observation, target materialization, build
receipt, reviewer assignment, native-tool run, transcript, fixture corpus,
grammar, parser, acceptance operation ID, executable plan, executor binding,
backend result, generated Lean, retained kernel result, proof artifact, checker
transcript, accepted evidence, Level2+, score axis, semantic correctness,
production readiness, SOTA, breakthrough, full security, external audit, or
action authority.

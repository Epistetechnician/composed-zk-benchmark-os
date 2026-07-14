# Phase 780 HSAI Formal Blocker Resolution Matrix

## Status

Complete as a documentation-first blocker-routing and source-correspondence
stop.

State slice: `phase-780-hsai-formal-blocker-resolution-matrix`.

Classification: `BlockerResolutionRoutedCapabilityCorrespondenceStopped`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Verdict

Phase 779 contains 102 blocked rows and 1,469 unique blocker objects across
nine closed blocker causes. Canonical JSONL serialization is a tenth,
document-level blocker.

This audit found an eleventh closure lane. Phase 779 marks ordinals 036, 037,
059, and 060 `sandbox-closed`, while Phases 773 and 774 classify those
pre-closure materialization commands `host-offline`. Neither Phase 776 nor
Phase 778 explicitly supersedes those four classifications. Therefore the
Phase 779 capability split is declared but not source-correspondence accepted.

Phase 780 routes all eleven lanes. It resolves none of them. All 102 ledger
rows remain blocked, canonical serialization remains unfrozen, and no
source-ledger digest exists.

## Census Authority

The row authority is the JSONL block in Phase 779. The operation-name authority
is the exact ordered list in Phase 778 with order digest:

```text
490c30a8098214754d20e4025696e2e3c702df8d4f7114a611157653ea7a4464
```

An ordinal in this document means exactly the Phase 778 operation ID at that
ordinal. Reassignment, insertion, deletion, or reordering is a validation
failure.

```text
row_count=102
blocked_row_count=102
jsonl_blocker_count=1469
jsonl_blocker_cause_count=9
document_level_blocker_count=1
source_correspondence_discrepancy_count=1
closure_lane_count=11
```

Forty-two row/field pairs carry both the general
`fully-expanded-row-field-unresolved` blocker and one specialized blocker.
Both must be discharged. Resolving only the specialized blocker does not make
the field or row resolved.

## Exact Operation Sets

The following names are exact and closed:

```text
D4 = download-rust-manifest, download-aeneas-main, download-aeneas-lean,
     download-lean
I1 = install-rust-toolchain
H2 = compile-helper-sources, run-helper-tests
N21 = codesign-verify-packaged-aeneas, codesign-verify-packaged-charon,
      codesign-verify-packaged-charon-driver,
      codesign-display-packaged-aeneas, codesign-display-packaged-charon,
      codesign-display-packaged-charon-driver, spctl-packaged-aeneas,
      spctl-packaged-charon, spctl-packaged-charon-driver,
      otool-libraries-packaged-aeneas, otool-libraries-packaged-charon,
      otool-libraries-packaged-charon-driver,
      otool-libraries-packaged-libgmp,
      otool-load-commands-packaged-charon-driver,
      codesign-verify-built-charon, codesign-verify-built-charon-driver,
      codesign-display-built-charon, codesign-display-built-charon-driver,
      otool-libraries-built-charon, otool-libraries-built-charon-driver,
      otool-load-commands-built-charon-driver
P1 = preflight-built-charon-driver-load
A5 = validate-aeneas-archives, extract-aeneas-main,
     extract-aeneas-lean-staging, decompress-lean-archive, extract-lean-tar
M8 = build-charon, extract-checker-llbc, pretty-print-checker-llbc,
     generate-aeneas-lean, check-types-olean, check-funs-olean,
     check-witness-olean, lake-build
C4 = extract-aeneas-main, extract-aeneas-lean-staging,
     decompress-lean-archive, extract-lean-tar
```

`E83` is exactly the Phase 778 operation IDs at these ordinals:

```text
007-022 028-058 061-082 085-098
```

`R102` is every Phase 778 operation ID at ordinals 001 through 102.
`S102` is the document-level serialization dependency over the same ordered
row set; it is not a command operation.

## Source Path Index

Every phase citation in the matrix resolves to exactly one path:

```text
678 docs/678-phase-hsai-gateway-threat-ordinal-authoritative-execution-protocol.md
716 docs/716-phase-hsai-gateway-threat-ordinal-charon-version-subcommand-closure.md
720 docs/720-phase-hsai-gateway-threat-ordinal-direct-olean-closure.md
742 docs/742-phase-hsai-gateway-threat-ordinal-exact-archive-profile-closure.md
744 docs/744-phase-hsai-gateway-threat-ordinal-authoritative-order-closure.md
748 docs/748-phase-hsai-gateway-threat-ordinal-canonical-helper-boundary.md
749 docs/749-phase-hsai-gateway-threat-ordinal-canonical-helper-implementation.md
759 docs/759-phase-hsai-gateway-threat-ordinal-helper-hash-command-closure.md
761 docs/761-phase-hsai-gateway-threat-ordinal-bounded-self-test-closure.md
763 docs/763-phase-hsai-gateway-threat-ordinal-rustup-inventory-closure.md
771 docs/771-phase-hsai-formal-execution-correspondence-correction-boundary.md
772 docs/772-phase-hsai-formal-execution-command-spec-completeness-stop.md
773 docs/773-phase-hsai-formal-execution-source-normalization-stop.md
774 docs/774-phase-hsai-formal-execution-command-family-resolution.md
776 docs/776-phase-hsai-formal-execution-contract-correction.md
777 docs/777-phase-hsai-formal-execution-pre-use-ordering-stop.md
778 docs/778-phase-hsai-formal-execution-operation-order-correction.md
779 docs/779-phase-hsai-formal-source-ledger-expansion.md
```

## Resolution Matrix

| Lane | Cause or discrepancy | Blockers / rows | Affected operations and fields | Controlling inputs to reconcile | Required immutable output | Review and exit gate | Assigned phase |
|---|---|---:|---|---|---|---|---:|
| `L01` | `capability-source-correspondence-discrepancy` | 0 / 4 | `C4`; `capability` | Phase 773 `Aeneas and Lean materialization/identity`; Phase 774 `Lean Extraction Resolution`; Phase 776 `Lean Extraction Correction` and `Sandbox Binding`; Phase 778 `Network And Loopback Order` | One explicit supersession or restoration decision for each row, with exact wrapper consequences and recomputed capability counts | No inference from executable roles; all four rows have controlling anchors; every sandbox row has exact wrapper obligations; network order remains closed | 781 |
| `L02` | `exact-downloader-argv-unresolved` | 4 / 4 | `D4`; `argv_template` | Phases 678, 742, 744, 772, 773, 774, and 776 | Four complete ordered argv arrays with absolute executable roles, pinned inputs, absent-output behavior, and no shell or inherited credentials | URLs and digests remain pinned; no `PATH` lookup, pipeline, implicit retry, overwrite, or post-069 acquisition | 782 |
| `L03` | `exact-installer-argv-unresolved` | 1 / 1 | `I1`; `argv_template` | Phases 744, 763, 772, 773, 774, and 776 | Exact noninteractive installer argv, manifest input, toolchain token, component request, isolated roots, and output contract | Exactly the marked component set; no parent profile, global Rust mutation, implicit prompt, or inherited environment | 782 |
| `L04` | `helper-file-order-unresolved` | 2 / 2 | `H2`; `argv_template` | Phases 749, 759, 761, 772, and 773 | Exact `/usr/bin/python3` compile and test argv arrays with ordered committed file/module sets | Set equality with committed helpers/tests; hashes accepted before use; no import or filesystem discovery | 783 |
| `L05` | `native-transcript-grammar-unresolved` | 21 / 21 | `N21`; `acceptance_operation_id` | Phase 776 `Corrected Native-Audit Cardinality` | Executable-version-bound `codesign`, `spctl`, and `otool` grammars, typed parser outputs, acceptance IDs, and immutable positive/negative fixtures | Missing, duplicate, reordered, ambiguous, and extra semantic records fail; substring-only and return-code-only acceptance are prohibited | 784 |
| `L06` | `driver-preflight-argv-unresolved` | 1 / 1 | `P1`; `argv_template` | Phases 776, 777, and 778 pre-use contracts | Exact sandbox-prefixed non-mutating driver-load argv plus typed toolchain-library inputs and outputs | Uses accepted Charon driver and exact `librustc_driver` identity; no extraction or durable mutation; finishes before ordinal 092 | 785 |
| `L07` | `archive-inventory-unresolved` | 5 / 5 | `A5`; `typed_output_artifacts` | Phases 742, 744, 748, 749, and 776 | Typed validation summary, Aeneas extraction trees, staged-duplicate policy, `lean.tar`, Lean tree, and exact digest/inventory consumers | Structural safety precedes profile equality; absent exclusive creation; extra, missing, linked, escaped, or replaced entries fail | 786 |
| `L08` | `mutable-output-inventory-unresolved` | 8 / 8 | `M8`; `typed_output_artifacts` | Phases 678, 716, 720, and 776 retained-evidence contract | Exact before/after mutable-root manifests, allowed additions/changes, forbidden drift, output digests, and consumers | Only named roots may change; immutable-cache drift and extra/missing outputs fail; retained projections recompute | 787 |
| `L09` | `machine-executable-identity-acceptance-unresolved` | 83 / 83 | `E83`; `executable_roles` | Phase 776 `Executable Identity Contract` | Complete immutable role registry: role ID, requested-path template, identity class, resolver, consumers, and acceptance policy per row | Exact role-to-row coverage; finite safe symlink resolution and policy-admitted digest; machine observations stay external | 788 |
| `L10` | `canonical-jsonl-serialization-unresolved` | 0 / 102 | `S102`; digest preimage | Phase 779 declaration; Phase 774 and 778 single-object precedents | JSONL encoding, recursive key order, escaping, numeric rules, duplicate-key rejection, row order, LF and final-newline policy, and digest preimage | Two independent serializers match conformance vectors; parse/re-serialize is idempotent; no row digest is published | 789 |
| `L11` | `fully-expanded-row-field-unresolved` | 1,344 / 102 | `R102`; fourteen fields listed below | Phase 771 `Controlling Source Order` and typed artifacts; Phase 772 required fields; Phase 773 command families; Phase 774 authoring profiles; Phase 776 corrected contracts; Phase 778 order; Phase 779 rows; accepted outputs from `L01`-`L10` | Every row-specific value and exact controlling anchor, with no profiles, grouped defaults, or inferred values | Exact order, one child per row, complete environment, placeholders, artifacts, acceptances, bounds, outcomes, and blocker removal | 790-792 |

The fourteen `L11` fields are exactly:

```text
controlling_phase_and_anchor argv_template cwd_template
replacement_environment timeout_seconds stdout_cap_bytes stderr_cap_bytes
expected_reason expected_return_code expected_signal typed_input_artifacts
typed_output_artifacts acceptance_operation_id allowed_placeholders
```

Expected reason, return code, and signal remain generally blocked on 74 rows;
the other eleven `L11` field families remain blocked on all 102 rows.

## Ordered Closure Program

```text
781 capability-source correspondence for C4
782 acquisition and installer argv contracts
783 helper compile/test order contract
784 native transcript grammar contract and fixtures
785 Charon driver preflight argv contract
786 archive inventory contracts
787 mutable output inventory contracts
788 immutable executable-role registry and machine-policy schema
789 canonical JSONL serialization profile and conformance vectors
790 row expansion tranche 001-038
791 row expansion tranche 039-064
792 row expansion tranche 065-102
793 independent whole-ledger audit and conditional digest publication
794 earliest possible plan-v2 boundary, only after Phase 793 success
```

Each phase is documentation-first unless a later explicit authorization says
otherwise. A phase resolves only its named lane. Historical Phase 779 rows are
not edited in place; accepted closure outputs are integrated into a successor
ledger artifact during Phases 790-792.

Phase 793 must fail closed unless the successor ledger has exactly 102 rows,
the Phase 778 order digest, zero blockers, no capability-source discrepancy,
complete role coverage, and byte-identical canonicalization under two
independent implementations. Only then may it publish a source-ledger digest.

## Claim Boundary

This matrix is routing metadata. It is not a source-ledger correction,
canonicalization profile, executable plan, executor binding, machine policy,
machine observation, transcript, backend result, or evidence record.

Phase 780 creates no generated Lean, retained kernel result, proof artifact,
checker transcript, accepted evidence, Level2+, score axis, semantic
correctness, production readiness, SOTA, breakthrough, full security,
external audit, or action authority.

Phase 781 subsequently resolves `L01` in
`docs/781-phase-hsai-formal-capability-source-correspondence-correction.md`.
The successor ledger must restore rows 036, 037, 059, and 060 to
`host-offline`, producing the corrected partition 10 external-acquisition, 63
host-offline, and 29 sandbox-closed rows. `L02` through `L11` remain open, all
102 rows remain blocked, and Phase 782 is the next authorized docs-first lane.

Phase 782 subsequently resolves `L02` and `L03` in
`docs/782-phase-hsai-formal-acquisition-and-installer-argv-contracts.md`.
The four downloader and one isolated Rust installer argv contracts are exact
inputs to successor-ledger expansion. `L04` through `L11` remain open,
historical Phase 779 JSONL and its 1,469 blockers remain unchanged, all 102
rows remain blocked, no source-ledger digest exists, and Phase 783 is the next
authorized docs-first lane.

Phase 783 subsequently stops before resolving `L04` in
`docs/783-phase-hsai-formal-helper-pre-use-ordering-stop.md`. Phase 759 requires
three separate helper-hash child producers before ordinal 007, while Phase 771
requires one operation per child and the Phase 778 102-operation order contains
no such rows. The inherited `py_compile` shape also writes bytecode with no
typed output or cleanup contract. `L04` through `L11` remain open, historical
Phase 779 JSONL and its 1,469 blockers remain unchanged, all 102 rows remain
blocked, and no source-ledger digest exists. The ordered closure program is
stopped pending an explicit route and operation-order correction; Phase 784's
previously assigned `L05` work is not authorized.

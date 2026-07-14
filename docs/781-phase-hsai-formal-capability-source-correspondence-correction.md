# Phase 781 HSAI Formal Capability Source Correspondence Correction

## Status

Complete as a documentation-first four-row capability correction.

State slice:
`phase-781-hsai-formal-capability-source-correspondence-correction`.

Classification: `CapabilitySourceCorrespondenceResolvedHostOffline`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Verdict

The successor source ledger must classify ordinals 036, 037, 059, and 060 as
`host-offline`.

Phase 771 states a broad sandbox rule for extraction. The later Phase 773
normalization explicitly classifies these named non-download Aeneas and Lean
materialization rows as `host-offline`, and Phase 774 specifically retains
`host-offline` for the two Lean extraction commands. Those operation-specific
later contracts control these rows. Phase 776 corrects their direct argv and
defines the wrapper for commands already classified `sandbox-closed`; it does
not reclassify these four rows. Phase 778 explicitly requires
`sandbox-closed` for ordinals 070 through 098 and does not reclassify earlier
rows.

A new early `sandbox-closed` supersession would place materialization before
the irreversible network closure, controlled-loopback lifecycle, and sandbox
controls. That requires a separate operation-order correction and is not
authorized by Phase 781. Source correspondence therefore restores the later,
operation-specific `host-offline` contracts.

Historical Phase 779 JSONL remains unchanged. This correction is an immutable
input to the successor ledger assembled in Phases 790-792.

## Corrected Rows

| Ordinal | Operation ID | Phase 779 value | Successor value | Sandbox wrapper | Executable-role effect |
|---:|---|---|---|---|---|
| 036 | `extract-aeneas-main` | `sandbox-closed` | `host-offline` | forbidden | remains blocked; no extractor role is inferred |
| 037 | `extract-aeneas-lean-staging` | `sandbox-closed` | `host-offline` | forbidden | remains blocked; no extractor role is inferred |
| 059 | `decompress-lean-archive` | `sandbox-closed` | `host-offline` | forbidden | exactly `ZSTD_EXE` |
| 060 | `extract-lean-tar` | `sandbox-closed` | `host-offline` | forbidden | exactly `TAR_EXE` |

`SANDBOX_EXEC_EXE` and `SANDBOX_PROFILE` are forbidden row obligations for all
four corrected rows. Rows 059 and 060 retain the direct Phase 776 zstd and tar
argv. Their exact remaining argv fields stay blocked until the Phase 791
row-expansion tranche integrates every required field.

## Corrected Capability Partition

```text
external-acquisition  10 = 015,016,024,033,034,058,066-069
host-offline          63 = 001-014,017-023,025-032,035-057,059-065,099-102
sandbox-closed        29 = 070-098
ordinary rows        102
controlled-loopback    1 = separate lifecycle, no ordinary ordinal
```

The irreversible external-network closure remains after ordinal 069. The
controlled-loopback lifecycle remains after closure and before ordinal 070.
No external-acquisition row moves, and no command after ordinal 069 may reopen
external networking.

## Blocker And Role Consequences

```text
Phase 779 blocker objects remain                 1469
blocked rows remain                               102
machine-executable role blockers remain            83
E83 ordinal set remains       007-022,028-058,061-082,085-098
resolved executable-role references become          21
resolved SANDBOX_EXEC_EXE references become           2
remaining closure lanes                              10
source-ledger digest                             absent
```

Rows 036 and 037 remain in `E83`. Rows 059 and 060 remain outside `E83`
because their underlying zstd and tar roles stay exact. The only surviving
resolved `SANDBOX_EXEC_EXE` references are rows 083 and 084. Phase 788's
83-row executable-role workload is unchanged.

Resolving capability correspondence does not discharge any Phase 779 blocker
object. `L01` is resolved; Phase 780 lanes `L02` through `L11` remain open.

## Correction Identity

The following single JSON object uses recursively sorted keys, compact
separators, UTF-8, and no trailing newline. This local single-object rule does
not resolve the separate Phase 789 JSONL serialization profile.

```json
{"authorities":[{"anchor":"Aeneas and Lean materialization/identity: 13","document_path":"docs/773-phase-hsai-formal-execution-source-normalization-stop.md","ordinals":["036","037"],"phase_id":"phase-773"},{"anchor":"Lean Extraction Resolution","document_path":"docs/774-phase-hsai-formal-execution-command-family-resolution.md","ordinals":["059","060"],"phase_id":"phase-774"},{"anchor":"Lean Extraction Correction","document_path":"docs/776-phase-hsai-formal-execution-contract-correction.md","ordinals":["059","060"],"phase_id":"phase-776"},{"anchor":"Sandbox Binding","document_path":"docs/776-phase-hsai-formal-execution-contract-correction.md","ordinals":["036","037","059","060"],"phase_id":"phase-776"},{"anchor":"Network And Loopback Order","document_path":"docs/778-phase-hsai-formal-execution-operation-order-correction.md","ordinals":["036","037","059","060"],"phase_id":"phase-778"}],"base_blocker_count":1469,"base_operation_order_sha256":"490c30a8098214754d20e4025696e2e3c702df8d4f7114a611157653ea7a4464","base_row_count":102,"base_source_ledger_path":"docs/779-phase-hsai-formal-source-ledger-expansion.md","base_source_ledger_schema":"hsai-formal-source-ledger-v1","capability_counts_after":{"external-acquisition":10,"host-offline":63,"sandbox-closed":29},"capability_ordinals_after":{"external-acquisition":["015","016","024","033","034","058","066","067","068","069"],"host-offline":["001","002","003","004","005","006","007","008","009","010","011","012","013","014","017","018","019","020","021","022","023","025","026","027","028","029","030","031","032","035","036","037","038","039","040","041","042","043","044","045","046","047","048","049","050","051","052","053","054","055","056","057","059","060","061","062","063","064","065","099","100","101","102"],"sandbox-closed":["070","071","072","073","074","075","076","077","078","079","080","081","082","083","084","085","086","087","088","089","090","091","092","093","094","095","096","097","098"]},"corrections":[{"capability_after":"host-offline","capability_before":"sandbox-closed","executable_role_effect":{"kind":"blocked-unchanged"},"operation_id":"extract-aeneas-main","ordinal":"036","sandbox_wrapper_after":"forbidden"},{"capability_after":"host-offline","capability_before":"sandbox-closed","executable_role_effect":{"kind":"blocked-unchanged"},"operation_id":"extract-aeneas-lean-staging","ordinal":"037","sandbox_wrapper_after":"forbidden"},{"capability_after":"host-offline","capability_before":"sandbox-closed","executable_role_effect":{"kind":"resolved-exact","role_ids":["ZSTD_EXE"]},"operation_id":"decompress-lean-archive","ordinal":"059","sandbox_wrapper_after":"forbidden"},{"capability_after":"host-offline","capability_before":"sandbox-closed","executable_role_effect":{"kind":"resolved-exact","role_ids":["TAR_EXE"]},"operation_id":"extract-lean-tar","ordinal":"060","sandbox_wrapper_after":"forbidden"}],"historical_phase779_rows_unchanged":true,"remaining_blocked_row_count":102,"remaining_closure_lane_count":10,"schema":"hsai-formal-capability-source-correspondence-correction-v1"}
```

SHA-256 of those exact bytes:

```text
cadc5bfa05e900dfa466713bb44109e192f7bf8d37aae045776b430bbc07e77c
```

This digest identifies only the capability correction. It is not the missing
source-ledger, plan-v2, executor-binding, or machine-resolved-attempt digest.

## Phase 782 Gate

Phase 782 remains documentation-first. It may resolve only Phase 780 lanes
`L02` and `L03`: the four downloader argv contracts and one Rust installer
argv contract, with exact executable-role placeholders, ordered argv, pinned
inputs, absent-output behavior, isolated roots, and noninteractive semantics.
Executable-role identity acceptance remains reserved for Phase 788.

Phase 782 may not modify Python or Rust source, rewrite historical Phase 779
rows, resolve machine observations, create attempt roots, publish a
source-ledger digest, or run any producer. Phase 783 and later lanes remain
blocked behind the Phase 780 order.

## Claim Boundary

Phase 781 is source-correspondence metadata. It is not an executable ledger,
plan-v2 object, executor binding, machine identity, transcript, backend result,
or evidence record.

Phase 781 creates no generated Lean, retained kernel result, proof artifact,
checker transcript, accepted evidence, Level2+, score axis, semantic
correctness, production readiness, SOTA, breakthrough, full security,
external audit, or action authority.

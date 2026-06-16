# Code Review — zkbench-core

Scope: full static review of `crates/zkbench-core` (~21k LOC src, 163 integration tests). Toolchain unavailable in the review sandbox, so `cargo clippy`/`cargo test` were not run — run them locally to confirm.

**Status update:** H1, M2, M3, and M4 have been fixed in-place (`dsl/oracle.rs`, `soak/runner.rs`, `pack/reader.rs`). M1 is resolved by policy: digests are version-locked, documented in `evidence/digest.rs` — any serialized-shape change to a digested type must bump the ledger schema version, and old-version ledgers are read-only. Fixes are unverified by cargo (no toolchain in review sandbox); run the commands in "Suggested next steps" before committing.

Overall: strong codebase. `#![forbid(unsafe_code)]`, zero `unwrap`/`expect`/`panic!` in src, no TODOs, deterministic ordering throughout (BTreeMap, sorted vecs), claim-boundary discipline enforced in code (not just docs), and consistent validation layering. The findings below are ordered by severity.

## High

### H1. Unchecked i64 arithmetic in the oracle — `dsl/oracle.rs:275-304`
`apply_int_update` uses raw `+` / `-` (`left + right`). In debug builds an adversarial or generated trace that overflows i64 panics the oracle; in release builds it **wraps silently**, which can flip a verdict (e.g. a counter wrapping past `i64::MAX` re-satisfying a `lt` guard → wrong `Accepted`). For a soundness-failure-detection oracle this is the one real correctness hole.

Fix: `checked_add`/`checked_sub`, returning `Rejected` (or `CapabilityGap`) on overflow:

```rust
let Some(result) = update(current, operand) else {
    return Ok(Some(OracleOutcome::Rejected { reason: "integer overflow in arithmetic update".into() }));
};
```
with `update: impl FnOnce(i64, i64) -> Option<i64>` and call sites passing `i64::checked_add`/`i64::checked_sub`.

## Medium

### M1. "Canonical" JSON digests are not canonical — `evidence/digest.rs:11-14`
`canonical_json_bytes` is plain `serde_json::to_vec`. Byte output depends on struct **field declaration order**, so any field rename/reorder/addition silently invalidates every existing ledger digest chain (`evidence/ledger.rs`, `review_ledger.rs`, `proposal_ledger.rs`) — `validate()` will report tamper-style mismatches for untouched data. Either implement real canonicalization (sorted keys, e.g. via `serde_json::Value` round-trip), or document that digests are version-locked and bump `EvidenceLedgerVersion` on any schema change with a migration story.

Related fragility: persisted summaries embed `format!("{:?}", …)` Debug strings (`evidence/ledger.rs:243`, `review_ledger.rs:116-127`, `append_preview.rs:321`, `proposal_ledger.rs:87-90`, `failure_corpus.rs:325`, `zk_harness/dry_run.rs:408`). Debug output is not a stable contract; derive `Display`/`serde` names instead.

### M2. Failure corpus refs duplicated/wrong in checkpoint — `soak/runner.rs:309-318`
```rust
for failure in &case_result.failures {
    if let Some(entry_id) = corpus.index.entries.last()...
```
`entries.last()` is loop-invariant: a case with N failures pushes the **last** corpus entry id N times into `checkpoint.failure_corpus_refs`; the first N−1 entries are never referenced. Map each failure to its own entry id (e.g. capture ids when pushing in `run_case`, or take the last N entries).

### M3. `load_evidence_ledger` skips path validation — `pack/reader.rs:54`
`self.root.join(&file.relative_path)` uses a manifest-supplied path without `validate_relative_path`, so a crafted `pack.json` with an absolute or `../` path reads files outside the pack root. `validate()` checks paths for the digest loop but calls `load_evidence_ledger()` independently, and it's also a public method. One-line fix: validate before joining. Inconsistent with the strict path rejection used everywhere else (`external_runner/validation.rs:48`).

### M4. `StopOnFirstFailure` loses the final checkpoint — `soak/runner.rs:320-327`
The `break` happens before `write_checkpoint`, so the failing case is marked failed in the in-memory checkpoint (returned in `SoakRunResult`) but never persisted. A subsequent resume re-runs the failed case even under `SkipFailedOnResume`. Write the checkpoint before breaking. Also, the shard status after an early break is still `Completed`/`CompletedWithFailures` even though remaining cases were never attempted — consider an `Aborted` status.

### M5. Trace initial fields not type-checked — `dsl/validation.rs:215-222`, `dsl/oracle.rs:39-41`
`validate_trace` confirms `initial_fields` keys are declared but not that values match the declared `field_type`. A trace can overwrite an int field with text; the mismatch then surfaces at runtime as `CapabilityGap` (in `compare_ints`) instead of a validation error, miscategorizing a malformed input as an oracle limitation. Check `value.matches_type(&field.field_type)` during validation (the machinery already exists — it's used for `field.initial` at validation.rs:47-56).

## Low

- **L1. Untagged serde enums** (`Value`, `OperandSpec`, `GuardSpec`, `GuardExpr`, `ActionSpec`): deserialization failures produce "data did not match any variant of untagged enum" with no location info — painful for YAML benchmark authors. Also `Noop { noop: false }` is still a noop. Consider internally-tagged representations or custom errors at the parse boundary.
- **L2. Duplicate/over-broad digest-algorithm check** — `external_runner/importer.rs:602-613`: the candidate-wide "unsupported algorithm" scan sits inside the per-ref loop, emitting one duplicate issue per ref and failing every ref if any single digest is non-SHA256, even refs with valid SHA-256 matches. Hoist it out of the loop if per-candidate, or scope it per-ref.
- **L3. `SampledPacks` ≡ `AllPacksWithinLimit`** — `soak/runner.rs:679-690`: both arms are identical (`pack_write_count < max_packs`); no sampling logic exists. Either implement sampling or collapse the variants until it does.
- **L4. Error enum boilerplate** — `error.rs`: 25 structurally identical `{path, message}` variants plus 25 hand-written constructors (~300 lines). A single struct with an `ErrorKind` enum (or a macro) removes ~250 lines with no API loss. Also `From<serde_json::Error>` maps to `Parse`, while most call sites wrap JSON errors as `Serialization`/`Deserialization` manually — pick one.
- **L5. Public API surface** — `lib.rs` re-exports ~400 names at crate root *and* duplicates a large subset in `prelude`. Consider exporting modules at root and keeping the curated list only in `prelude`; the current setup makes every type name a semver commitment twice.
- **L6. Unused feature flag** — `Cargo.toml` declares `external-runner = []`, but `lib.rs` compiles `pub mod external_runner;` unconditionally. Either gate the module (`#[cfg(feature = "external-runner")]`) or drop the feature.
- **L7. Silent shard misattribution** — `soak/runner.rs:915-926`: `corpus_entry` falls back to `SoakShardId::from_index(0)` when the case isn't found in any manifest, silently mislabeling the failure. Prefer an error or an explicit "unknown" marker. Similarly `extract_failure_corpus` (runner.rs:756-771) silently skips results whose case id isn't in the plan.
- **L8. Brittle issue-kind inference** — `external_runner/importer.rs:905-923`: `base_issue_kind` classifies by substring-matching paths/messages ("provenance", "absolute"); a reworded message changes the issue kind. Have the base validator emit kinds directly.
- **L9. Linear lookups** — `SemanticIr::transition/state/field` (`dsl/ir.rs:136-151`), `resolver.lookup`, `plan.case_plans.find` are O(n) per call (O(n·m) per trace evaluation). Fine at current scale; switch to `BTreeMap` indexes if machines/plans grow.
- **L10. 32-bit casts** — `soak/config.rs:68` (`(end - start) as usize`) and `generator/deterministic.rs:244` (`seed.value as usize`) truncate on 32-bit targets. `SoakSeedRange::values()` also materializes the full range as a `Vec` — capped by `max_seeds` validation, but `values()` is callable pre-validation.

## Suggested next steps

1. Fix H1 (checked arithmetic) and M2–M4 — all are small, localized patches.
2. Decide the digest-stability story (M1) before any ledger leaves a single-version environment.
3. Run `cargo clippy --all-targets -- -D warnings` and `cargo test` locally; this review was static-only.

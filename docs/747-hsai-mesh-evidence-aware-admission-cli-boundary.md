# Phase 747 HSAI Mesh Evidence-Aware Admission CLI Boundary

Date: 2026-07-12

State slice: `phase-747-hsai-mesh-evidence-aware-admission-cli`.

Status: complete for the frozen v1 Rust parity CLI and additive evidence-aware
v2 wire contract.

## Purpose

Phase 747 implements one hermetic Rust command boundary that executes the
existing HSAI Mesh repo-patch admission evaluator over a strict wire contract.
It provides the bounded replacement command for the Mesh Python metadata-allow
adapter; Mesh runtime wiring remains a separate state slice. It does not
transfer action authority to HSAI.

The implementation supports the frozen `mesh.hsai_admission_request.v1`
compatibility contract and the additive
`mesh.hsai_admission_request.v2` contract. Version 2 carries the canonical
candidate payload, pre-execution evidence, Mesh evaluation status, final
recommendation, blocking reasons, canonical stage results, and a structural
disposable-worktree preflight receipt. Rust recomputes the candidate, evidence,
stage-results, and action-proposal digests before evaluating a gate.
Caller-supplied `passed` booleans are not sufficient evidence.

## Implemented surface

- `crates/hsai-agent-admission/src/bin/hsai-mesh-admission/main.rs` owns the
  bounded stdin/stdout command and explicit `--current-policy-id` input;
- `crates/hsai-agent-admission/src/bin/hsai-mesh-admission/runtime.rs` owns the
  duplicate-rejecting parser, strict wire DTOs, Mesh canonical JSON digest,
  digest parsing, v1/v2 wire-to-domain conversion, existing evaluator
  invocation, and decision mapping;
- `crates/hsai-agent-admission/tests/mesh_repo_patch_admission_cli_contract.rs`
  covers allow, deny, stale policy, evidence-binding drift, duplicate keys,
  unknown fields, trailing data, duplicate set entries, malformed digests,
  wrong action kinds, size/depth bounds, missing policy input, digest
  recomputation, stdout/stderr behavior, forbidden runtime surfaces, v2
  structural allow, candidate/evidence/stage/action digest tampering, failed and
  empty tests, path and policy drift, protected-path rejection, missing receipt
  fields, and duplicate changed paths.

The v1 adapter derives both local evidence gates only from the declared evidence
digest and its matching attestation reference. It does not embed or inspect the
pre-execution evidence packet. That limitation is explicit in every emitted
decision's formal-evidence nonclaim.

The v2 adapter accepts structurally verified local preflight declarations only
when all of the following hold:

- canonical recomputation matches `candidate_payload_digest`,
  `evidence_packet_digest`, `stage_results_digest`, and
  `action_proposal_digest`;
- decision, run, action, actor, and current-policy bindings agree;
- Mesh evaluation passed, recommends `execute`, and has no blocking reasons;
- the preflight receipt has the exact
  `mesh.repo_patch_disposable_worktree.v1` state slice;
- target and changed paths are portable, inside `allowed_paths`, and outside
  `protected_paths`;
- the receipt binds exactly one changed target path;
- declared test commands and receipt `argv` values match, test results are
  nonempty, and every return code is zero;
- all declared SHA-256 and Git object identifiers have canonical shapes; and
- the evidence digest is bound by an attestation reference.

V2 validation is structural local preflight validation. Its exact nonclaim is:

> Structural local preflight validation only; validates embedded bytes and
> declarations but is not proof that the declared commands ran, not formal
> proof, accepted evidence, production certification, or authority to execute a
> patch.

## Authorized mutation surface

- additive Rust source under `crates/hsai-agent-admission/src/` for strict wire
  parsing, bounded-input validation, canonical Mesh JSON hashing, wire-to-domain
  conversion, and decision mapping;
- one binary under `crates/hsai-agent-admission/src/bin/` that reads one request
  from stdin and emits one decision on stdout;
- focused integration tests and non-secret fixtures under
  `crates/hsai-agent-admission/tests/`;
- backward-compatible `crates/hsai-agent-admission/Cargo.toml` metadata only if
  required without adding a dependency;
- this phase note and standard `README.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`, and `AGENTS.md` mirrors.

## Runtime contract

- Input is bounded to 1 MiB and one JSON object.
- Duplicate keys, Unicode-equivalent duplicate keys, unknown fields, trailing
  data, duplicate set entries, malformed digests, and excessive nesting fail
  closed.
- The current Mesh policy id is explicit operator input.
- Allow and deny decisions exit zero. Malformed input and internal failures exit
  nonzero and emit no decision object.
- Stdout contains only the decision JSON. Diagnostics use stderr.
- No network, listener, credential access, filesystem write, Mesh runtime call,
  external process spawn, or fallback allow path is permitted.
- V2 digest or wire-shape tampering fails without a decision object. Structurally
  valid but non-admissible evaluation, path, policy, or test evidence becomes a
  deterministic deny through the existing HSAI evaluator.

## Claim boundary

HSAI remains an evidence and admission engine. Every emitted decision preserves
`grants_authority=false` and `production_readiness_claimed=false`. Mesh alone
may issue and consume a separately authenticated, expiring, single-use local
execution capability after both HSAI admission and Mesh policy approval.

Phase 747 creates local contract and regression evidence only. It creates no
accepted Evidence Ledger record, Level2+ evidence, benchmark evidence, formal
proof, semantic-correctness result, production-readiness result, SOTA result,
breakthrough result, full-security result, global uniqueness result, or
authority to execute a patch.

## Focused validation

- targeted `rustfmt --check` over the two binary files and focused test;
- targeted Clippy over the binary and focused test with `-D warnings`;
- 12/12 focused CLI contracts passed;
- 17/17 existing Mesh admission contracts passed.
- 6/6 HSAI claim-boundary source-scan contracts passed;
- repository hygiene and documentation-boundary tests passed;
- `git diff --check` passed;
- `crates/hsai-agent-admission/src/lib.rs`, crate metadata, and `Cargo.lock`
  remained unchanged.

Workspace-wide and cross-repository Mesh runtime gates remain outside this
focused implementation handoff.

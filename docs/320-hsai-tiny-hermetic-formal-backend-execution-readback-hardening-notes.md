# Phase 320 HSAI Tiny Hermetic Formal-Backend Execution Readback Hardening Notes

State slice: `Phase 320 HSAI tiny hermetic formal-backend execution readback hardening`.

## Scope

Phase 320 hardens the Phase 319 local fixture execution readback lane. It adds
focused negative coverage around the declared-file output bundle without adding
new process APIs, new runners, real solver scripts, proof artifacts, checker
transcripts, accepted evidence, Level2+ evidence, score axes, or proof-authority
claims.

The only execution path remains the fixed local fixture process introduced in
Phase 319.

## Implemented Coverage

Phase 320 adds focused tests for:

- Malformed declared JSON rejection.
- Existing output-root rejection when overwrite is not explicitly allowed.
- Output-root symlink rejection.
- Bundle-directory symlink rejection.
- Declared-file symlink rejection.
- Declared-sidecar symlink rejection.
- Digest-preserving stdout summary semantic drift rejection.
- Digest-preserving redaction-report semantic drift rejection.
- Digest-preserving nonpromotion-report semantic drift rejection.

The digest-preserving drift tests intentionally update the surrounding manifest
and transcript digests where needed so readback reaches the intended semantic
validator instead of stopping at an earlier stale-sidecar or digest mismatch.

## Evidence Meaning

This phase can support only this claim:

```text
HSAI has hardened local regression coverage for the tiny hermetic formal-backend fixture execution readback lane.
```

It strengthens local readback confidence. It does not convert the Phase 319
fixture run into proof authority.

## Nonclaims

Phase 320 does not support:

- `HSAI is SOTA.`
- `HSAI is fully secure.`
- `HSAI proves semantic correctness.`
- `HSAI is production ready.`
- `HSAI has accepted formal evidence.`
- `HSAI has Level2+ formal evidence.`
- `HSAI has backend score axes.`
- `HSAI has Lean proof artifacts.`
- `HSAI has SMT/Z3 proof artifacts.`
- `HSAI has COBALT proof artifacts.`
- `HSAI has checker transcripts.`
- `HSAI has solver certificates.`
- `HSAI has authority to execute downstream actions.`

## Anti-Goals

This phase does not permit:

- Generic backend runners.
- Caller-supplied executable paths.
- Caller-supplied argv.
- Shell execution.
- Inherited environment.
- Stdin.
- Network access.
- Package runtime files.
- External repo clones.
- Vendored source.
- Lean execution.
- SMT/Z3 execution.
- COBALT execution.
- Aeneas/Hax/rust-lean execution.
- Coq/TLA+/CBMC/model-checker execution.
- Solver scripts.
- Checker scripts.
- Proof artifact creation.
- Checker transcript creation.
- Solver-certificate creation.
- Accepted Evidence Ledger mutation.
- Level2+ evidence.
- Score-axis population.
- Benchmark evidence.
- Official benchmark submission.
- Live provider calls.
- Credential handling.
- Semantic-correctness claims.
- Production-readiness claims.
- SOTA claims.
- Breakthrough claims.
- Full-security claims.
- Authority to execute an action.

## Validation

Targeted validation:

```text
cargo test -p hsai-agent-admission gateway_formal_backend_tiny_hermetic_execution -- --nocapture
```

Full validation remains:

```text
cargo fmt --all -- --check
cargo test -p hsai-e2e-harness --test claim_boundary_source_scan
cargo test -p zkbench-core --test repo_claim_boundary_docs --test repo_hygiene
git diff --check
find README.md AGENTS.md docs crates -type f -empty
pnpm run lint, if package.json exists
cargo test --workspace
```

## Next Slice

The next responsible slice is Phase 321: a docs-first boundary for a real
Lean/SMT/COBALT command lane. It must decide one tiny property, one backend
mode, one artifact grammar, one checker transcript grammar, and one quarantine
readback contract before any real proof assistant, solver, or COBALT command is
allowed to run.

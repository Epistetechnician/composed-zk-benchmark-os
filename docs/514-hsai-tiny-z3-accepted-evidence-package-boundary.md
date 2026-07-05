# Phase 514 HSAI Tiny Z3 Accepted Evidence Package Boundary

State slice: `Phase 514 HSAI tiny Z3 accepted evidence package boundary`.

Phase 514 defines the docs-first boundary for a future local accepted-evidence
package over the Phase 513 materialized accepted ledger artifact:

```text
Phase 513 materialized accepted append metadata
  + explicit local evidence package policy
  -> local accepted-evidence package metadata
```

This phase does not implement Rust code, change Cargo metadata, write files,
read accepted Evidence Ledger files, write accepted Evidence Ledger files,
create accepted-evidence package metadata, create accepted formal evidence,
create Level2+ evidence, populate score axes, generate proof artifacts,
generate checker transcripts, generate solver certificates, run Lean, run new
SMT, run COBALT, run Rust-to-Lean extraction, create benchmark evidence, claim
semantic correctness, claim production readiness, claim SOTA, claim
breakthrough status, claim full security, claim external audit status, or grant
authority to execute an action.

## Future Allowed Touch Surface

A future implementation phase may only touch these files unless a later
boundary explicitly broadens scope:

- `crates/hsai-agent-admission/src/lib.rs`;
- focused tests in `crates/hsai-agent-admission/src/lib.rs`;
- future phase notes under `docs/`;
- navigation/status updates under `README.md`, `docs/12-task-list.md`,
  `docs/90-whole-codebase-validation-report.md`, this boundary, and
  `AGENTS.md`.

No Cargo metadata change, external dependency, feature flag, binary, script,
runner, process-spawn API, network API, official submission API, solver API,
proof-assistant API, benchmark runner, score-axis output, or backend execution
output is authorized by this boundary.

## Future Package Meaning

A future accepted-evidence package may be local metadata only. It may bind:

- one exact Phase 513 materialized accepted append metadata record;
- one Phase 513 materialized ledger artifact digest;
- one Phase 513 materialized append report digest;
- one Phase 513 ledger path identity digest;
- one Phase 513 ledger path policy digest;
- package policy id;
- package decision id;
- package timestamp;
- evidence class `LocalReplay`;
- claim boundary `Level1LocalReplay`;
- explicit local-only nonclaims;
- explicit evidence caps.

The package must not contain or imply:

- formal proof authority;
- checker transcript authority;
- solver certificate authority;
- Lean proof;
- SMT proof authority;
- COBALT containment evidence;
- Rust-to-Lean proof;
- Level2+ evidence;
- score-axis evidence;
- benchmark evidence;
- external audit evidence;
- semantic correctness;
- production readiness;
- SOTA;
- full security;
- action authority.

## Required Future Bindings

A future implementation that tries to satisfy this boundary must bind:

- one Phase 513 materialized accepted append metadata digest;
- one Phase 513 materialization input digest;
- the Phase 513 digest-binding map digest;
- the Phase 513 id-binding map digest;
- the Phase 513 label-binding map digest;
- the Phase 513 explicit nonclaim digest;
- the Phase 513 materialization-rule digest;
- the Phase 513 forbidden-API set digest;
- the Phase 513 inherited-digest requirement digest;
- the Phase 513 Phase 511 mutation digest;
- the Phase 513 ledger path identity digest;
- the Phase 513 ledger path policy digest;
- the Phase 513 materialized append report digest;
- the Phase 513 materialized ledger artifact digest;
- the Phase 513 materialized ledger artifact byte length;
- the Phase 511 appended evidence class;
- the Phase 511 appended claim boundary;
- package policy digest;
- package nonclaim digest;
- package cap digest.

## Required Future Validation Rules

A future implementation must fail closed if:

- the Phase 513 materialized append metadata record is not exact;
- Phase 513 did not route through the `zkbench-core` materialized owner;
- Phase 513 did not create materialized accepted ledger output;
- the Phase 513 materialized ledger artifact digest is missing or zero;
- the Phase 513 materialized ledger artifact byte length is zero;
- the Phase 511 appended evidence class is not `LocalReplay`;
- the Phase 511 appended claim boundary is not `Level1LocalReplay`;
- package policy, nonclaim, or cap digests are missing or drift;
- the package attempts to create formal evidence;
- the package attempts to create Level2+ evidence;
- the package attempts to populate score axes;
- the package attempts to cite proof/checker/solver authority;
- the package attempts to cite Lean/new-SMT/COBALT/Rust-to-Lean evidence;
- the package attempts to cite benchmark evidence or external audit evidence;
- the package claims semantic correctness, production readiness, SOTA,
  breakthrough status, full security, or action authority.

## Backend Relationship

This boundary is not backend execution. It is not Lean, SMT, COBALT, or
Rust-to-Lean evidence. It is not proof authority. It is not benchmark evidence.
It is not score-axis evidence. It is not external audit evidence.

If a future package succeeds, it may support this claim only:

```text
HSAI packages one local Level1LocalReplay accepted-ledger artifact as scoped
local accepted evidence for a reviewed tiny-Z3 gateway path.
```

That still would not be accepted formal evidence, Level2+ evidence, score-axis
evidence, Lean proof, SMT proof authority, COBALT containment evidence,
Rust-to-Lean proof, checker transcript authority, solver certificate authority,
benchmark evidence, external audit, SOTA, semantic correctness, production
readiness, full security, or authority to execute an action.

## Phase 515 Implementation Exit Criteria

A future Phase 515 may implement local accepted-evidence package metadata only
if it:

- touches only the allowed files listed above;
- performs no process or network calls;
- writes no package artifact files;
- validates one exact Phase 513 materialized append metadata record;
- binds package policy, nonclaim, and cap digests;
- records evidence class `LocalReplay`;
- records claim boundary `Level1LocalReplay`;
- rejects formal evidence, Level2+, score axes, proof/checker/solver
  authority, backend execution evidence, benchmark evidence, external audit,
  strong claims, and action authority in the metadata itself.

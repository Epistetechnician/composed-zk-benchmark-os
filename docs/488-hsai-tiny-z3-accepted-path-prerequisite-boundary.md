# Phase 488 HSAI Tiny Z3 Accepted-Path Prerequisite Boundary

State slice: `Phase 488 HSAI tiny Z3 accepted-path prerequisite boundary`.

Phase 488 defines the docs-first prerequisite boundary for moving beyond the
Phase 487 local terminal metadata chain. The purpose is to state what must be
true before HSAI can responsibly pursue any accepted append decision, accepted
formal evidence, score-axis population, Level2+ evidence, or public claim of
SOTA, full security, semantic correctness, or production readiness.

This phase does not implement Rust code, change Cargo metadata, write
filesystem artifacts, mutate the accepted Evidence Ledger, change accepted
append policy, create accepted formal evidence, create Level2+ evidence,
populate score axes, generate proof artifacts, generate checker transcripts,
generate solver certificates, run Lean, run new SMT, run COBALT, run
Rust-to-Lean extraction, submit benchmarks, claim semantic correctness, claim
production readiness, claim SOTA, claim breakthrough status, claim full
security, or grant authority to execute an action.

## Current Terminal State

The Phase 487 terminal metadata supports only this claim:

```text
HSAI can locally record that one tiny-Z3 settlement-blocker review terminal
review closure review is terminal for the current local chain while settlement
into accepted append or accepted formal evidence remains blocked.
```

That terminal record is not accepted evidence. It is not a proof artifact. It
is not a checker transcript. It is not a solver certificate. It is not Level2+
evidence. It does not populate score axes. It does not prove semantic
correctness, production readiness, SOTA, full security, or action authority.

## Required Future Acceptance Gates

Before any accepted append decision can be considered, a future phase must
define and implement all of these gates:

- accepted append owner and mutation route;
- accepted append policy version;
- exact accepted evidence class;
- exact claim boundary for that evidence class;
- replayable input bundle identity;
- source correspondence statement and digest;
- reviewer policy and reviewer decision requirements;
- rejection behavior for policy drift;
- rejection behavior for stale current accepted append blockers;
- explicit nonclaim set and nonclaim digest;
- accepted Evidence Ledger append preview and append transaction rules;
- rollback or quarantine behavior for invalid append attempts.

The accepted append route must remain owned by the existing accepted append
policy surface. `hsai-agent-admission` metadata cannot directly mutate the
accepted Evidence Ledger unless a separate explicit phase opens and tests that
route.

## Required Future Formal-Evidence Gates

Before accepted formal evidence can be considered, a future phase must define
and implement all of these gates:

- proof-source authority policy;
- checker transcript authority policy;
- solver certificate authority policy;
- source-to-obligation correspondence policy;
- replay policy for the exact backend run;
- evidence class mapping for solver-only, checker-backed, certificate-backed,
  Lean, SMT, COBALT, and Rust-to-Lean lanes;
- explicit rule for whether solver `unsat` without certificate can ever exceed
  local reviewed metadata;
- explicit rule for whether COBALT-style containment evidence is scoped to an
  arithmetic/action-boundary property only;
- explicit rule for whether Lean/Rust-to-Lean evidence covers only extracted
  pure-data functions;
- rejection behavior for any whole-system, production, or semantic-correctness
  claim not entailed by the proof scope.

No future formal-evidence record may treat solver output, certificate
explanation, reviewed metadata, or terminal metadata as proof authority without
a separately implemented authority policy and tests.

## Required Future Level2+ and Score-Axis Gates

Before Level2+ evidence or score-axis population can be considered, a future
phase must define and implement all of these gates:

- Level2+ evidence class taxonomy;
- score-axis names and scoring semantics;
- score-axis source evidence requirements;
- score-axis nonclaim requirements;
- score-axis reviewer policy;
- benchmark comparison corpus and version;
- benchmark run reproducibility requirements;
- benchmark result quarantine and acceptance rules;
- rejection behavior for benchmark/SOTA claims unsupported by accepted
  benchmark evidence;
- explicit rule that local metadata cannot populate score axes.

Level2+ and score axes remain forbidden until those gates exist in code and
tests.

## Required Future Public-Claim Gates

Before any public claim of SOTA, full security, semantic correctness, or
production readiness can be considered, a future phase must define separate
evidence for each claim:

- SOTA requires accepted benchmark evidence against a named comparison set,
  versioned metrics, replayable runs, and reviewer approval.
- Full security requires a scoped threat model, implemented mitigations,
  adversarial tests, residual-risk disclosure, and external assumptions.
- Semantic correctness requires formal source correspondence from the
  executable source to the proved obligation and a checker policy appropriate
  to the claim scope.
- Production readiness requires deployment, operations, incident, rollback,
  monitoring, secrets, dependency, and recovery evidence separate from local
  proof metadata.

No single local proof, solver result, terminal metadata record, benchmark run,
or attestation result can establish all four claims.

## Required Future Implementation Exit Criteria

A future implementation phase may create prerequisite metadata only if it:

- names the exact accepted-path prerequisite record state slice;
- remains local metadata unless separately authorized;
- binds the Phase 487 terminal digest and input digest;
- binds the Phase 487 digest, id, and label binding maps;
- records each required future gate as unresolved, satisfied-by-reference, or
  rejected;
- rejects accepted append decisions in the prerequisite metadata itself;
- rejects accepted Evidence Ledger mutation in the prerequisite metadata
  itself;
- rejects accepted formal evidence creation in the prerequisite metadata
  itself;
- rejects Level2+ evidence creation in the prerequisite metadata itself;
- rejects score-axis population in the prerequisite metadata itself;
- rejects proof/checker/solver authority creation in the prerequisite metadata
  itself;
- rejects Lean/new-SMT/COBALT/Rust-to-Lean execution evidence creation in the
  prerequisite metadata itself;
- rejects benchmark/SOTA claims in the prerequisite metadata itself;
- rejects semantic-correctness, production-readiness, full-security,
  breakthrough, and action-authority claims in the prerequisite metadata
  itself.

## Evidence Meaning

The maximum claim after Phase 488 is:

```text
HSAI has a documented prerequisite boundary for leaving the local tiny-Z3
terminal metadata chain and later pursuing accepted append, accepted formal
evidence, Level2+, score axes, and strong public claims without conflating
local metadata with accepted evidence or proof authority.
```

That still is not:

- accepted append;
- accepted formal evidence;
- accepted Evidence Ledger mutation;
- Level2+ evidence;
- score-axis evidence;
- Lean proof;
- SMT proof authority;
- COBALT containment evidence;
- Rust-to-Lean proof;
- benchmark evidence;
- SOTA;
- semantic correctness;
- production readiness;
- full security;
- authority to execute an action.

## Next Responsible Slice

Phase 489 may implement local accepted-path prerequisite metadata over one
Phase 487 terminal record. It must not make accepted append decisions, mutate
the accepted Evidence Ledger, create accepted formal evidence, create Level2+
evidence, populate score axes, run Lean/new-SMT/COBALT/Rust-to-Lean
extraction, claim semantic correctness, claim production readiness, claim SOTA,
claim breakthrough status, claim full security, or grant action authority.

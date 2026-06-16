# Agent Case And Evidence Lane — Implementation Spec

## Status And Claim Boundary

Level 1 design artifact for the next explicit phase. It specifies a new crate,
`hsai-agent-case`, that depends on the shipped `hsai-claim-envelope` crate. It is
not source code. This phase builds interfaces and honest reference lanes only: no
real ZK, no TEE, no network, no identity store, no economy. A reference lane that
emits a `Stub`/`Local` envelope is not cryptographic proof, and a lane accepting a
case is not the oracle's verdict.

## Purpose

Turn a live agent action into a semantic, checkable `AgentCase` with an oracle
contract (the live-agent analog of a Benchmark Instance), and define the
`EvidenceLane` interface that mints `ClaimEnvelope`s from a case. This is the layer
that sits between L0 (the action) and the keystone, and it is the prerequisite for
the distinct-agent lane and `IdentityProvider` that follow.

## Dependencies On The Shipped Keystone

Reuse, do not redefine, these `hsai-claim-envelope` items: `ClaimEnvelope`,
`ClaimEnvelope::new`, `conjoin`, `admits`, `AcceptancePolicy`, `Predicate`,
`PropertyKind` (`Distinctness`, `MemoryIntegrity`, `PolicyCompliance`, `IsModel`,
`SemanticCorrectness`, `Custom`), `SubjectId`, `Maturity`, `TrustRoot`, `LaneId`,
`TimeWindow`. The agent-case crate produces and consumes these exact types.

## Types

```text
struct ActionId(String);
struct ModelId(String);
struct MemoryRoot([u8; 32]);          // commitment to agent memory state

enum Verdict { Accept, Reject, Inconclusive }   // mirrors the L0 oracle model

struct OracleContract {
  expected:         Verdict,                 // declared BEFORE any lane runs
  target_guarantees: BTreeSet<Predicate>,    // what a fully-verified case would establish
  excluded:         BTreeSet<Predicate>,     // explicit non-claims (claim boundary)
}

struct AgentCase {
  action:        ActionId,
  subject:       SubjectId,        // the acting agent identity
  claimed_model: ModelId,          // model the action CLAIMS to come from
  memory_root:   MemoryRoot,       // committed memory state for this action
  observed_at:   u64,              // time the action was observed
  oracle:        OracleContract,
}

struct RawAction { /* same fields as AgentCase */ }   // pre-lowering input
```

`RawAction` is the pre-lowering input to `CaseSource::lower`. In this phase it
mirrors `AgentCase` and `lower` is a structural passthrough (`RawAction.into()`).
Real lowering — canonicalization, computing the `memory_root` commitment, and
deriving the `OracleContract` from semantics — is deferred to a later phase; the
`CaseSource` interface is in place so that work has somewhere to land.

`target_guarantees` are *targets*, not guarantees: they name what evidence lanes
would need to establish for the case to be fully verified. Until a lane proves
one, it remains something a consumer must treat as unproven.

## Traits

```text
trait CaseSource {
  // Deterministic lowering of a raw action into a case. Same input -> same case.
  fn lower(&self, action: RawAction) -> AgentCase;
}

trait EvidenceLane {
  fn id(&self) -> LaneId;                              // LaneId::Named(...)
  fn ceiling(&self) -> Maturity;                       // max maturity this lane may emit
  fn evaluate(&self, case: &AgentCase) -> ClaimEnvelope;
}
```

Lane discipline (enforced by tests, see Invariants): a lane's emitted envelope
must have `maturity <= self.ceiling()`, must carry `excludes ⊇ case.oracle.excluded`
(the case's claim boundary propagates into every envelope about it), and must set
`valid` honestly (stubs may use `TimeWindow::all()`; real lanes derive it from
attestation or stake freshness).

## Reference Lanes (honest, in-scope)

Two reference lanes that demonstrate the pattern without overclaiming:

`DeclaredLane` — the honest baseline. It establishes nothing. It mints an envelope
with empty `guarantees`, `assumptions = case.oracle.target_guarantees` (everything
still needs proving), `excludes = case.oracle.excluded`, `maturity = Stub`, empty
`trust_roots`, `valid = TimeWindow::all()`. Composing only `DeclaredLane` output is
inadmissible under `require_closed` whenever there are targets — correct, because a
declaration proves nothing.

`LocalMemoryLane` — a locally-checked memory commitment. It mints `guarantees =
{ MemoryIntegrity(case.subject) }`, empty `assumptions`, `excludes =
case.oracle.excluded`, `maturity = Local` (locally checked, not proven), empty
`trust_roots`, `valid = [case.observed_at, ..]`. It is the stub stand-in for the
future ZK memory lane; it must NOT emit `Proven` or claim a `VerifyingKey` root.

## Claim Boundaries (hard statements, AGENTS.md style)

- A declared predicate is not an established guarantee.
- A lane evaluation is not the oracle's verdict.
- A `Stub` or `Local` lane is not cryptographic proof.
- An `AgentCase` is a local lowering, not a Benchmark Instance from `zkbench-core`.
- A lane may never emit maturity above its declared ceiling.
- The case's `excluded` set propagates into every envelope minted about it.

## Invariants (property-test statements)

For any lane `L` and case `c`, let `e = L.evaluate(c)`:

```text
LANE-1  ceiling:   e.maturity <= L.ceiling()
LANE-2  boundary:  e.excludes ⊇ c.oracle.excluded
LANE-3  no-forge:  e.trust_roots only contains roots the lane is defined to add
                   (DeclaredLane and LocalMemoryLane add none)
LANE-4  determinism: L.evaluate(c) == L.evaluate(c)   (byte-identical envelope)
```

For `CaseSource` `S` and raw action `a`:

```text
CASE-1  determinism: S.lower(a) == S.lower(a)
```

## Test Vectors

Predicates abbreviated `property(subject)`.

### W1 — A declaration proves nothing

```text
case C: subject=agentA, target_guarantees={ Distinctness(agentA), MemoryIntegrity(agentA) },
        excluded={ SemanticCorrectness(action1) }, expected=Accept
DeclaredLane.evaluate(C) == {
  guarantees:  { },
  assumptions: { Distinctness(agentA), MemoryIntegrity(agentA) },
  excludes:    { SemanticCorrectness(action1) },
  maturity:    Stub,
  trust_roots: { },
  valid:       all,
}
admits( { require:{}, min_maturity:Stub, require_closed:true, forbid:{}, at:T }, above )
  == Err([ OpenAssumption(Distinctness(agentA)), OpenAssumption(MemoryIntegrity(agentA)) ])
```

### W2 — Composing a real lane discharges one assumption, not all

```text
LocalMemoryLane.evaluate(C) == {
  guarantees:  { MemoryIntegrity(agentA) }, assumptions:{}, excludes:{ SemanticCorrectness(action1) },
  maturity: Local, trust_roots:{}, valid:[observed_at, ..],
}
conjoin( DeclaredLane.evaluate(C), LocalMemoryLane.evaluate(C) ) == {
  guarantees:  { MemoryIntegrity(agentA) },
  assumptions: { Distinctness(agentA) },          // memory discharged; distinctness still open
  excludes:    { SemanticCorrectness(action1) },
  maturity:    Stub,                               // min(Stub, Local)
  trust_roots: { },
  valid:       [observed_at, ..],
}
```

This is the key demonstration: the case cannot be closed until a distinct-agent
lane (next phase) discharges `Distinctness(agentA)`. The interface is correct
precisely because it leaves that hole visible.

### W3 — Deterministic lowering

```text
S.lower(action1) == S.lower(action1)        // byte-identical AgentCase
```

## Out Of Scope (next phases, do not build now)

The real ZK memory lane, the TEE provenance lane, the distinct-agent lane, the
`IdentityProvider` (L2), the economy (L3), the harness (L4), and interop (L5).
This phase ships only `AgentCase`, the two traits, the two reference lanes, and
their tests.

## Implementation Phase Notes

- New crate `crates/hsai-agent-case`, added to workspace members, depending on
  `hsai-claim-envelope` (path dependency). Do not modify `zkbench-core` or
  `hsai-claim-envelope`.
- Dev-dependency `proptest` for LANE-1..4 and CASE-1; encode W1–W3 as unit tests.
- Deterministic everywhere: `BTreeSet`, canonical serialization, no `HashMap`.
- A Rust toolchain (pinned 1.74) is required to build and test.
- Definition of done: `cargo test -p hsai-agent-case` green, `cargo fmt --check`
  and `cargo clippy -- -D warnings` clean, W1–W3 reproduced exactly.

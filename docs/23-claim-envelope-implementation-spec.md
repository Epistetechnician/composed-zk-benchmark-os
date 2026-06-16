# Claim Envelope — Implementation Spec

## Status And Claim Boundary

This is a Level 1 design artifact: pseudo-types, pseudo-traits, an algebra, and
test vectors. It is not source code. Per AGENTS.md, the Hyper Sacred AI claim
envelope is a new system layered on the benchmark OS (doc 22, L0); turning this
spec into a compiling crate is an explicit new implementation phase, not part of
the current zkbench-core scope. A spec is not an implementation, and a passing
property test will verify the algebra's laws, not the truth of any claim an
envelope carries.

## Purpose

Pin down the keystone precisely enough that implementation is mechanical. Every
other module emits and consumes this type; the four invariants are the system's
guarantee that composition cannot manufacture trust.

## Types

```text
enum Maturity { Stub, Local, Attested, Proven }   // total order; meet = min
// Stub < Local < Attested < Proven

enum TrustRoot {                                   // compose by union
  HardwareVendor(VendorId),    // TEE: NVIDIA / AMD SEV-SNP / Intel TDX key
  VerifyingKey(VkId),          // ZK circuit verifying key
  EconomicStake(StakeRef),     // bonded, slashable
  SocialReputation(AgentId),   // vouching identity
}

struct Predicate {             // a named property about a subject
  subject:  SubjectId,         // agent id, memory root, action id
  property: PropertyKind,      // Distinctness | MemoryIntegrity | PolicyCompliance | IsModel | ...
}

struct TimeWindow { start: u64, end: u64 }         // inclusive; meet = intersection

struct ClaimEnvelope {
  guarantees:  BTreeSet<Predicate>,   // established IF assumptions hold; compose by union
  assumptions: BTreeSet<Predicate>,   // premises; union then discharge
  excludes:    BTreeSet<Predicate>,   // explicit non-claims (claim boundary); union
  maturity:    Maturity,              // meet (min)
  trust_roots: BTreeSet<TrustRoot>,   // union
  valid:       TimeWindow,            // meet (intersection)
  lane:        LaneId,                // origin lane; Composite after compose
  provenance:  Hash,                  // content-addressed identity of THIS envelope (see Provenance note)
}
```

Determinism: use ordered sets (`BTreeSet`) and a canonical serialization so
`provenance` is reproducible, matching the benchmark OS's deterministic-artifact
discipline. No external crypto dependency is required for the algebra itself;
hashing can reuse the existing `sha2` dependency.

## Operators

```text
fn top() -> ClaimEnvelope {
  // identity element for conjoin
  guarantees: {}, assumptions: {}, excludes: {},
  maturity: Proven, trust_roots: {}, valid: [0, u64::MAX],
  lane: Top, provenance: hash_top(),
}

fn conjoin(a: ClaimEnvelope, b: ClaimEnvelope) -> ClaimEnvelope {
  if a == top() { return b; }   // exact identity (LAW-3)
  if b == top() { return a; }
  let guarantees  = a.guarantees ∪ b.guarantees;
  let assumptions = (a.assumptions ∪ b.assumptions) \ guarantees;  // discharge
  let result = ClaimEnvelope {
    guarantees,
    assumptions,
    excludes:    a.excludes ∪ b.excludes,
    maturity:    min(a.maturity, b.maturity),
    trust_roots: a.trust_roots ∪ b.trust_roots,
    valid:       intersect(a.valid, b.valid),
    lane:        Composite,
    provenance:  Hash([0; 32]),     // placeholder
  };
  ClaimEnvelope { provenance: hash_content("conjoin", &result), ..result }
}
```

`conjoin` is a commutative, associative monoid with identity `top()`.
Associativity holds because guarantees accumulate by union and the final
assumption set equals all-assumptions minus all-guarantees regardless of grouping.

### Provenance note (resolved during implementation)

Provenance is the content-addressed hash of the resulting envelope's fields (not a
hash of the input provenance values), and `top()` short-circuits as an exact
identity. This is required for the laws: an input-hash provenance is order- and
grouping-sensitive and would break LAW-1 (commutativity) and LAW-3 (identity),
both of which require all fields — provenance included — to be equal. Consequence:
provenance identifies an envelope's *content*, not its *derivation*, so the
input-DAG audit trail is not recoverable from provenance alone. Before envelopes
are wired into an evidence ledger, split identity (content hash, law-bearing) from
derivation (a DAG of input hashes, treated as metadata and excluded from the
equality the laws use), so both the algebra and auditability hold.

## Acceptance

```text
struct AcceptancePolicy {
  require:        BTreeSet<Predicate>,        // guarantees that must be present
  min_maturity:   Maturity,
  forbid_roots:   BTreeSet<TrustRootClass>,   // e.g. economy flags HardwareVendor-only
  require_closed: bool,                       // no open assumptions allowed
  at:             u64,                        // must be valid at this time
}

fn admits(p: AcceptancePolicy, e: ClaimEnvelope) -> Result<(), Vec<Rejection>> {
  // fails if: any p.require missing from e.guarantees;
  //           e.maturity < p.min_maturity;
  //           require_closed && e.assumptions nonempty;
  //           any e.trust_root in p.forbid_roots;
  //           p.at outside e.valid.
}
```

`require_closed` is the linchpin: an envelope that guarantees `PolicyCompliance`
while still assuming `IsModel` is inadmissible until a provenance envelope
discharges the assumption.

## The Four Invariants (property-test statements)

For all envelopes `a`, `b` (generate with random predicate sets, maturities,
roots, and windows), let `c = conjoin(a, b)`:

```text
INV-1  maturity:    c.maturity   <= min(a.maturity, b.maturity)
INV-2  excludes:    c.excludes   ⊇ a.excludes ∪ b.excludes
INV-3  trust_roots: c.trust_roots ⊇ a.trust_roots ∪ b.trust_roots
INV-4  valid:       c.valid       ⊆ a.valid ∩ b.valid
```

Plus the structural laws that make `conjoin` well-formed:

```text
LAW-1  commutative:   conjoin(a, b) ≅ conjoin(b, a)        (all fields equal)
LAW-2  associative:   conjoin(conjoin(a,b),c) ≅ conjoin(a,conjoin(b,c))
LAW-3  identity:      conjoin(a, top()) ≅ a
LAW-4  no-forge:      c.guarantees \ open-assumptions(c) carries maturity
                      min over the chain that established each guarantee
```

INV-1..4 are the meet laws; together they encode "assurance only descends." No
function in the API may raise maturity, remove an exclude, or drop a trust root.
A test suite asserting INV-1..4 and LAW-1..3 over randomized inputs promotes
ledger assumption A7 from Pending to Level 1.

## Test Vectors

Concrete cases for the implementation to reproduce exactly. Predicates abbreviated
as `property(subject)`; roots abbreviated; windows as `[start,end]`.

### V1 — TEE caps ZK (the hybrid-trust case)

```text
E_policy = {
  guarantees:  { PolicyCompliance(action1) },
  assumptions: { IsModel(agentA) },
  excludes:    { SemanticCorrectness(action1) },
  maturity:    Proven,
  trust_roots: { VerifyingKey(policy_vk) },
  valid:       [100, 200],
}
E_prov = {
  guarantees:  { IsModel(agentA) },
  assumptions: { },
  excludes:    { },
  maturity:    Attested,
  trust_roots: { HardwareVendor(nvidia) },
  valid:       [150, 300],
}
conjoin(E_policy, E_prov) == {
  guarantees:  { PolicyCompliance(action1), IsModel(agentA) },
  assumptions: { },                                  // discharged -> closed
  excludes:    { SemanticCorrectness(action1) },
  maturity:    Attested,                             // min(Proven, Attested)
  trust_roots: { VerifyingKey(policy_vk), HardwareVendor(nvidia) },
  valid:       [150, 200],
}
```

Acceptance check: an economy policy with `require_closed = true`,
`min_maturity = Attested`, `require = { PolicyCompliance(action1) }` admits the
result, but flags it provisional because `trust_roots` contains a
`HardwareVendor` class.

### V2 — Open assumption is inadmissible

```text
admits(
  { require: { PolicyCompliance(action1) }, min_maturity: Local,
    require_closed: true, at: 120 },
  E_policy                                   // still assumes IsModel(agentA)
) == Err([ OpenAssumption(IsModel(agentA)) ])
```

### V3 — Identity law

```text
conjoin(E_prov, top()) == E_prov            // up to lane/provenance normalization
```

### V4 — Disjoint validity yields empty window

```text
conjoin(
  { ..., valid: [0, 50] },
  { ..., valid: [60, 100] }
).valid == empty            // represented as start > end; admits() always fails on time
```

## Implementation Phase Notes

When an explicit implementation phase opens:

- Target a new crate (e.g. `crates/hsai-claim-envelope`), added to the workspace
  members, separate from `zkbench-core` so the two systems do not conflate.
- Dependencies: `serde`, `serde_json`, `sha2` (already in the workspace);
  `proptest` as a dev-dependency for INV-1..4 and LAW-1..3.
- Encode V1..V4 as fixture-backed unit tests and the invariants as proptests.
- No external rails, no economy, no network: this crate is pure data and algebra.

A Rust toolchain is required to build and run these tests; this sandbox does not
currently have one, so verification of compilation is deferred to that phase.

# Attestation-Verification Lane — Implementation Spec

## Status And Claim Boundary

Level 1 design artifact for the next explicit phase: a new crate `hsai-attestation`
depending on the shipped `hsai-claim-envelope`, `hsai-agent-case`, and
`hsai-distinct-agent` crates. It is not source code. It is the capstone of the
trust stack: the lane that discharges the anchor-validity assumption every
distinctness envelope has carried open since L2.

Honesty boundary, stated plainly. This phase verifies attestation at the
*interface* level. The reference `ManagedTokenVerifier` checks a token's nonce,
provider custom-data/report-data binding, measurements, and freshness but does
NOT cryptographically verify the managed attestation service's signature over
that token. That signature check — validating
an Azure Attestation / Intel Trust Authority JWT against the service JWKS, or a
vendor quote against its root cert — is the single real integration step, and it is
the point at which the stack leaves the pure-data regime. It is deliberately out of
scope here. A verified attestation is therefore `Attested`, never `Proven`, and it
establishes hardware-bounded distinctness only (ledger A4b), not competence or
safety.

## Purpose

Turn a (managed) attestation token for an anchor into a `ClaimEnvelope` that
GUARANTEES that anchor's validity predicate — the exact predicate the
distinct-agent lane emits as an open assumption — so conjoining the two closes the
distinctness envelope and makes it admissible under `require_closed` for the first
time in the build.

## Dependencies

Reuse, do not redefine: from `hsai-claim-envelope` — `ClaimEnvelope`, `conjoin`,
`Maturity`, `SubjectId`, `TimeWindow`, `LaneId`, `TrustRoot`. From `hsai-agent-case`
— `AgentCase`, `EvidenceLane`. From `hsai-distinct-agent` — `Anchor` (and its
`validity_assumption(subject)` and `trust_root()` methods, reused verbatim so the
guarantee predicate and trust root match the distinct-agent lane exactly — no
format drift).

## Types

```text
struct Token {
  anchor_id:    String,      // which anchor this attests (must match the Anchor)
  nonce:        u64,         // anti-replay nonce
  report_data:  Vec<u8>,     // provider custom-data binding
  measurements: Vec<u8>,     // measured code/firmware digest
  not_before:   u64,
  not_after:    u64,
}

struct VerifiedAttestation { anchor_id: String, not_before: u64, not_after: u64 }

enum VerifyError {
  AnchorMismatch,        // token.anchor_id != the anchor being checked
  NonceMismatch,
  MeasurementMismatch,
  ReportDataMismatch,
  Expired,               // now outside [not_before, not_after]
  SignatureUnverified,   // reserved for real backends; the reference impl never returns it
}

trait AttestationVerifier {
  // A real backend FIRST verifies the managed service's signature over the token,
  // then the fields below. The reference impl verifies only the fields.
  fn verify(&self, token: &Token, expected_nonce: u64, expected_report_data: &[u8],
            expected_measurements: &[u8],
            anchor_id: &str, now: u64) -> Result<VerifiedAttestation, VerifyError>;
}

struct ManagedTokenVerifier;   // reference backend; NO signature verification
// Ok iff token.anchor_id == anchor_id, token.nonce == expected_nonce,
// token.report_data == expected_report_data,
// token.measurements == expected_measurements, not_before <= now <= not_after.
```

## The Lane

```text
struct AttestationInput {
  anchor:                Anchor,
  token:                 Token,
  expected_nonce:        u64,
  expected_report_data:  Vec<u8>,
  expected_measurements: Vec<u8>,
}

struct AttestationLane<V: AttestationVerifier> { verifier: V, inputs: Vec<AttestationInput> }

impl<V: AttestationVerifier> EvidenceLane for AttestationLane<V> {
  fn id(&self) -> LaneId { LaneId::Named("attestation") }
  fn ceiling(&self) -> Maturity { Maturity::Attested }
  fn evaluate(&self, case: &AgentCase) -> ClaimEnvelope {
    let now = case.observed_at;
    // verify each input; collect guarantees, trust roots, and the meet of windows
    let mut guarantees = {}; let mut roots = {}; let mut window = TimeWindow::all();
    for input in &self.inputs {
      if let Ok(va) = verifier.verify(&input.token, input.expected_nonce,
                                      &input.expected_report_data,
                                      &input.expected_measurements,
                                      &input.anchor.anchor_id(), now) {
        guarantees |= { input.anchor.validity_assumption(&case.subject) };
        roots      |= { input.anchor.trust_root() };
        window      = window.intersect(TimeWindow { start: va.not_before, end: va.not_after });
      }
    }
    if guarantees.is_empty() {
      // nothing verified -> claims nothing, honest Stub
      ClaimEnvelope::new({}, {}, case.oracle.excluded.clone(), Maturity::Stub, {}, all, id)
    } else {
      ClaimEnvelope::new(guarantees, {}, case.oracle.excluded.clone(),
                         Maturity::Attested, roots, window, id)
    }
  }
}
```

The emitted guarantee is exactly `Anchor::validity_assumption(subject)` — the open
assumption from the distinct-agent lane — so `conjoin` discharges it.

## Claim Boundaries (hard statements)

- The reference verifier transcribes token claims; it does NOT verify the managed
  service signature. Real verification is the deferred integration and the point of
  leaving pure-data.
- A verified attestation is `Attested`, never `Proven`.
- Discharging anchor-validity establishes hardware-bounded distinctness only, not
  competence or safety.
- Freshness is enforced from the token window; an expired token never verifies.
- A rejected input contributes no guarantee and no trust root.

## Invariants (property-test statements)

```text
ATI-1  ceiling:    evaluate(case).maturity <= Attested  (never Proven)
ATI-2  selective:  the guarantee set == { anchor.validity_assumption(subject) } for
                   exactly the inputs the verifier accepted; rejected inputs add
                   neither a guarantee nor a trust root
ATI-3  window:     the emitted valid window ⊆ each accepted attestation's window
ATI-4  discharge:  conjoin(distinct_agent_env, attestation_env) removes the matching
                   anchor-validity assumption from the result
ATI-5  determinism: evaluate is byte-deterministic
```

## Test Vectors

### AT-1 — A verified token guarantees anchor validity

```text
input: anchor=HardwareAttested{nvidia,devX}, token matches expected nonce+report_data+measurements,
       window [100,300]; case.subject=agentA, observed_at=150
AttestationLane.evaluate(case) == {
  guarantees:  { Custom("anchor-valid:hw:nvidia:devX")(agentA) },
  assumptions: { },
  excludes:    case.oracle.excluded,
  maturity:    Attested,
  trust_roots: { HardwareVendor("hw:nvidia:devX") },
  valid:       [100, 300],
}
```

### AT-2 — The capstone: distinctness finally closes

```text
d = DistinctAgentLane{devX}.evaluate(case)   // guarantees Distinctness, assumes anchor-valid:devX
a = AttestationLane{verified devX}.evaluate(case)
conjoin(d, a) == {
  guarantees:  { Distinctness(agentA), Custom("anchor-valid:hw:nvidia:devX")(agentA) },
  assumptions: { },                           // discharged — CLOSED
  maturity:    Attested,
  trust_roots: { HardwareVendor("hw:nvidia:devX") },
  ...
}
// admits( require_closed policy requiring Distinctness, min Attested ) == Ok
// This is the first admissible distinctness envelope in the build.
```

### AT-3..AT-5 — Honest failure

```text
AT-3  nonce mismatch       -> verify Err(NonceMismatch)       -> lane guarantees nothing (Stub)
AT-4  now > not_after      -> verify Err(Expired)             -> lane guarantees nothing (Stub)
AT-5  measurement mismatch -> verify Err(MeasurementMismatch) -> lane guarantees nothing (Stub)
```

## Out Of Scope (the deferred real step and beyond)

Real managed-service signature verification (Azure Attestation / Intel Trust
Authority JWT against JWKS, or a vendor quote against its root cert) — this is the
recommended first real backend and the point of leaving pure-data. Also out of
scope: NVIDIA GPU attestation format specifics, ZK-wrapped proving (the
`Attested -> Proven` sunset), onchain verification, and any change to existing
crates. Do not resolve doc 22 open decisions.

## Implementation Phase Notes

- New crate `crates/hsai-attestation`, workspace member, path-depending on
  `hsai-claim-envelope`, `hsai-agent-case`, `hsai-distinct-agent`. Modify no
  existing crate.
- Dev-dependency `proptest`. Encode AT-1..5 as unit tests and ATI-1..5 as proptests.
- Deterministic: `BTreeSet`, integer math, no `HashMap`, no floats.
- Definition of done: `cargo test -p hsai-attestation` green, `cargo fmt --check`
  and `cargo clippy -p hsai-attestation --all-targets -- -D warnings` clean.
- Leave a clearly-marked seam (the `AttestationVerifier` trait) where a real
  signature-verifying backend drops in later.

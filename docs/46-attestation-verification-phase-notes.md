# Phase: Attestation-Verification Lane — Implementation Notes

New explicit implementation phase. Ships `crates/hsai-attestation`, the capstone
lane that discharges the anchor-validity assumption every distinctness envelope
has carried open since L2. Built per `docs/44-attestation-verification-lane-spec.md`.

## What shipped

- `Token`, `VerifiedAttestation`, `VerifyError` (`AnchorMismatch`,
  `NonceMismatch`, `ReportDataMismatch`, `MeasurementMismatch`, `Expired`, and
  the reserved-but-never-returned `SignatureUnverified`).
- `AttestationVerifier` trait — the clean seam where a real signature-verifying
  backend (Azure Attestation / Intel Trust Authority JWT, or a vendor quote)
  drops in later.
- `ManagedTokenVerifier` reference backend — checks `anchor_id`, `nonce`,
  provider custom-data/report-data binding, `measurements`, and freshness
  (`not_before <= now <= not_after`). Does NOT verify the managed service
  signature.
- `AttestationInput` and `AttestationLane<V>` implementing `EvidenceLane`. Uses
  `case.observed_at` as the verification time and the meet (intersection) of the
  accepted tokens' windows. Each accepted input contributes its anchor's
  `validity_assumption(subject)` guarantee and its `trust_root()`; nothing
  verified yields an honest `Stub`.

## Reused verbatim (no drift)

`Anchor::validity_assumption(subject)` and `Anchor::trust_root()` from
`hsai-distinct-agent`, `EvidenceLane`/`AgentCase` from `hsai-agent-case`, and
`ClaimEnvelope`/`conjoin`/`Maturity`/`TimeWindow`/`admits`/`AcceptancePolicy`
from `hsai-claim-envelope`. The emitted guarantee predicate is exactly the
distinct-agent open assumption, so `conjoin` discharges it.

## Claim boundary (honesty)

- The reference verifier transcribes token claims; it does NOT verify the managed
  service signature. That is the deferred real integration and the point at which
  the stack leaves the pure-data regime.
- A verified attestation is `Attested`, never `Proven`.
- Discharging anchor-validity establishes hardware-bounded distinctness only
  (ledger A4b), not competence or safety.
- An expired token never verifies; a rejected input contributes no guarantee and
  no trust root.

## Tests

- AT-1..5 as unit tests, including the AT-2 capstone: `conjoin(distinct_agent,
  attestation)` is closed (no open assumptions) and admitted under a
  `require_closed`, `min Attested` policy requiring `Distinctness` — the first
  admissible distinctness envelope in the build.
- ATI-1..5 as proptests: ceiling never exceeds `Attested`; guarantees/trust roots
  come from exactly the accepted inputs; the valid window is a subset of each
  accepted window; conjoin discharges the matching anchor-validity assumption;
  `evaluate` is deterministic.

## Definition of done

`cargo test -p hsai-attestation` green; `cargo fmt --check` and
`cargo clippy -p hsai-attestation --all-targets -- -D warnings` clean.

## Out of scope (deferred real step and beyond)

Real managed-service signature verification (the recommended first real backend),
NVIDIA GPU attestation format specifics, ZK-wrapped proving (the `Attested ->
Proven` sunset), onchain verification, and any change to existing crates.

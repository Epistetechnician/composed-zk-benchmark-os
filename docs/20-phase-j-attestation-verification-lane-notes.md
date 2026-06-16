# Phase J — Attestation Verification Lane

New explicit implementation phase. This phase ships the HSAI attestation
verification lane and the minimal foundation it stands on.

This phase doc stands in for the referenced `docs/44-attestation-verification-lane-spec.md`
and `docs/45-attestation-verification-handoff.md`, which do not exist in this
repository. See **Deviations** below: the "seven shipped HSAI crates" the spec
assumes were not present in this workspace, so the dependencies the lane reuses
were created here rather than reused from prior crates.

## Crates added

- `crates/hsai-core` (L0) — the shared vocabulary:
  - `Anchor::validity_assumption()` and `Anchor::trust_root()` — fixed constants.
    Every lane reuses them verbatim so an assumption left open by one lane is
    discharged by a guarantee from another.
  - `Guarantee` / `GuaranteeLevel` (`Attested`, `Proven`). `Proven` is never
    produced from a data lane; `Guarantee::attested` is the only constructor.
  - `LaneOutcome` (`Granted` / `Withheld`) — a withheld outcome carries no
    guarantee and no trust root.
  - `EvidenceLane` — the lane contract.
- `crates/hsai-agent-case` — `Case` (carries `observed_at`, the verification
  time, and observer-accepted `TimeWindow`s) and the half-open `TimeWindow`
  with `intersect`.
- `crates/hsai-distinct-agent` — `DistinctnessEnvelope`: opens carrying
  `Anchor::validity_assumption()`, is discharged only by a `Guarantee` resting on
  that same assumption and `Anchor::trust_root()`, and `require_closed()` admits
  it once discharged.
- `crates/hsai-attestation` (this phase's deliverable) — `Token`,
  `VerifiedAttestation`, `VerifyError`, the `AttestationVerifier` trait, the
  `ManagedTokenVerifier` reference backend, and `AttestationLane<V>` implementing
  `EvidenceLane`.

## What the reference verifier checks

`ManagedTokenVerifier::verify` uses `case.observed_at()` as the verification time
and checks:

1. nonce equals the expected nonce;
2. measurements equal the expected measurements;
3. freshness — the token is not expired (`observed_at >= expires_at` is expired),
   and `observed_at` lies inside the intersection of the token validity window,
   the verifier's accepted windows, and the case's accepted windows.

On success it grants an `Attested` guarantee reusing `Anchor::validity_assumption()`
and `Anchor::trust_root()` verbatim, so the guarantee discharges the
distinct-agent open assumption exactly.

## Claim boundary (honesty)

- The reference verifier does **not** verify the managed service signature. That
  signature check is the deferred real step — the point where the stack would
  leave pure-data. `token.signature` is carried but never inspected.
- A verified attestation is `Attested`, never `Proven`.
  `VerifiedAttestation::signature_verified()` is always `false`.
- A rejected input adds no guarantee and no trust root (`LaneOutcome::Withheld`).
- Expired tokens never verify.
- An attestation pass is not a proof. The guarantee is only as strong as
  `Anchor::validity_assumption()`, which states in prose that the binding is
  assumed, not proven.

## Tests

- AT-1..5 as unit tests in `crates/hsai-attestation/src/lib.rs`:
  - AT-1 valid token verifies and reuses the anchor constants verbatim;
  - AT-2 a verified attestation discharges the distinctness envelope, admitted
    under `require_closed`;
  - AT-3 expired tokens never verify;
  - AT-4 a rejected input adds no guarantee and no trust root;
  - AT-5 verified is `Attested` never `Proven`, signature unverified.
- ATI-1..5 as proptests in `crates/hsai-attestation/tests/ati_proptests.rs`:
  expired never verifies; nonce mismatch always rejected; measurement mismatch
  always rejected; rejection grants nothing (verify-Err iff lane-Withheld);
  every verified attestation is `Attested`/honest with `verified_at ==
  observed_at` inside the accepted window.

## Definition of done

`cargo test -p hsai-attestation` is green (6 unit tests + 5 proptests).

## Deviations from the assumed spec

1. **Foundation absent.** The referenced HSAI foundation (seven shipped crates
   L0–L3, the L5 membrane, the economy sim) and `docs/44`/`docs/45` were not
   present in this workspace, on any branch, or in history. The spec's
   instructions to "reuse `Anchor::…` verbatim", "implement the shipped
   `EvidenceLane`", and "modify no existing crate" presuppose them. To deliver a
   compiling, testable lane, the minimal dependencies it names (`Anchor`,
   `EvidenceLane`, the distinctness envelope, the agent case) were created in
   this phase rather than reused. The lane itself (`hsai-attestation`) matches the
   named surface exactly.
2. **No existing crate modified.** Only the workspace `Cargo.toml` `members` list
   was extended. `crates/zkbench-core` was left untouched. Note: `zkbench-core`
   does not compile on the initial commit (`unresolved import
   crate::evidence::review`), so `cargo test --workspace` fails for that
   pre-existing reason; the scoped `cargo test -p hsai-attestation` is green.

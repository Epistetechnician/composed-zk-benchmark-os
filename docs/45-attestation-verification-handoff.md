# Attestation-Verification Lane — Implementation Handoff

## Who This Is For

The engineering agent continuing the Hyper Sacred AI build. Seven crates are
shipped and verified (L0–L3, the L5 membrane, the economy simulation). This is the
capstone phase: the lane that discharges the anchor-validity assumption every
distinctness envelope has carried open since L2. Build one crate: `hsai-attestation`.

## Context In 60 Seconds

Since L2, every distinctness envelope has guaranteed `Distinctness` only under an
open assumption that the anchor is valid — a hole nothing could close. This lane
closes it: it turns a (managed) attestation token into an envelope that GUARANTEES
the anchor-validity predicate, so conjoining it with the distinct-agent envelope
yields the first admissible, closed distinctness claim in the build. It is built
abstract over a swappable `AttestationVerifier` backend, with a managed-token
reference impl. The one real step — verifying the managed service's signed token —
is deliberately deferred; it is where the stack leaves the pure-data regime.

## Source Of Truth (read in this order)

- `docs/44-attestation-verification-lane-spec.md` — THE spec: types, the
  `AttestationVerifier` trait, `ManagedTokenVerifier`, the `AttestationLane`, claim
  boundaries, invariants ATI-1..5, vectors AT-1..5.
- `crates/hsai-distinct-agent/src/lib.rs` — `Anchor`, and its
  `validity_assumption` / `trust_root` you reuse verbatim so the guarantee matches
  the open assumption exactly.
- `crates/hsai-agent-case/src/lib.rs` — the `EvidenceLane` trait you implement.
- `crates/hsai-claim-envelope/src/lib.rs` — `conjoin`, `ClaimEnvelope`, `TimeWindow`.
- `AGENTS.md` — hard rules.

## The Task

Open a new explicit implementation phase and build `crates/hsai-attestation` per
`docs/44`. Deliverable: a compiling, tested crate with the verifier trait, the
managed-token reference verifier, the `AttestationLane`, and tests reproducing
AT-1..5 (including the AT-2 capstone discharge) plus invariants ATI-1..5.

## The Honesty Boundary (the whole point of this phase)

- The reference `ManagedTokenVerifier` checks nonce, measurements, and freshness
  but does NOT verify the managed service's signature over the token. Mark this
  loudly. Real signature verification is the deferred integration and the moment
  the stack stops being pure-data.
- A verified attestation is `Attested`, never `Proven`. Do not emit `Proven`.
- The lane only guarantees anchor-validity for inputs the verifier accepted; a
  rejected input adds no guarantee and no trust root.
- Reuse `Anchor::validity_assumption(subject)` and `Anchor::trust_root()` verbatim
  so the guarantee predicate and trust root match the distinct-agent lane exactly —
  if they drift, the assumption will not discharge and AT-2 fails.
- Freshness is real: an expired token (now outside the window) must not verify.

## Hard Constraints (from AGENTS.md)

- New explicit phase; record it in AGENTS.md.
- New separate crate `crates/hsai-attestation`, workspace member, path-depending on
  the three crates above. Modify no existing crate.
- Pure data and interface. No network, no real crypto signature verification, no
  JWKS fetch, no GPU/ZK/onchain. Deterministic; `BTreeSet`, integer math, no
  `HashMap`, no floats.

## Build Plan

1. Toolchain: Rust 1.74.
2. Scaffold `crates/hsai-attestation/`; add to workspace members; path-depend on the
   three crates; dev-dep `proptest`.
3. Types: `Token`, `VerifiedAttestation`, `VerifyError`, the `AttestationVerifier`
   trait, and `ManagedTokenVerifier` per `docs/44` §Types.
4. `AttestationInput` and `AttestationLane<V>` implementing `EvidenceLane`, per
   §The Lane. Use `case.observed_at` as the verification time and the meet
   (intersection) of accepted windows.
5. Tests: AT-1..5 as unit tests (AT-2 must show the distinct-agent assumption
   discharging and the result admitted under `require_closed`); ATI-1..5 as
   proptests.
6. Green: `cargo test -p hsai-attestation`, `cargo fmt --check`, `cargo clippy -p
   hsai-attestation --all-targets -- -D warnings`.

## Definition Of Done

- Crate compiles on Rust 1.74; depends only on the three HSAI crates (+ serde as
  needed, proptest dev-only).
- AT-1: a verified token yields an `Attested` envelope guaranteeing the
  anchor-validity predicate with the vendor trust root and the token window.
- AT-2: `conjoin(distinct_agent_env, attestation_env)` is CLOSED (no open
  assumptions) and admitted under a `require_closed`, `min Attested` policy — the
  first admissible distinctness envelope in the build.
- AT-3..5: nonce / expiry / measurement failures yield no guarantee (Stub).
- ATI-1..5 hold as proptests. Phase note added to AGENTS.md and `docs/`.

## Correctness Pitfalls

- Predicate match is everything: emit exactly `anchor.validity_assumption(subject)`.
  Reconstructing the `Custom("anchor-valid:...")` string by hand risks drift and
  breaks the discharge — call the distinct-agent method.
- The window is a meet: intersect accepted attestation windows; do not union.
- Never emit `Proven`; the ceiling is `Attested`.
- A rejected input must change nothing about the envelope (no partial trust root).
- Keep the `AttestationVerifier` trait as the clean seam where a real
  signature-verifying backend (Azure Attestation / Intel Trust Authority) drops in.

## Out Of Scope

Real managed-service signature verification (the recommended first real backend,
and the deferred leave-pure-data step), NVIDIA GPU attestation format, ZK proving,
onchain verification, and any change to existing crates. Do not resolve doc 22 open
decisions.

## After This Phase

This closes the last open assumption in the stub stack: L0–L3 + L5 + identity are
now end-to-end closeable in code. The remaining real-world steps are integrations,
not new primitives: the real attestation backend (verify the managed JWT), then —
as the ledger A1 sunset trigger fires — a ZK lane that raises distinctness toward
`Proven`.

## Paste-Ready Kickoff Prompt

> You are continuing the Hyper Sacred AI build in the `composed-zk-benchmark-os`
> repo. Seven crates are shipped (L0–L3, the L5 membrane, the economy sim). Read
> `docs/45-attestation-verification-handoff.md`, then
> `docs/44-attestation-verification-lane-spec.md`, then
> `crates/hsai-distinct-agent/src/lib.rs`, `crates/hsai-agent-case/src/lib.rs`, and
> `AGENTS.md`. Open a new explicit implementation phase and build
> `crates/hsai-attestation` exactly per doc 44: `Token`, `VerifiedAttestation`,
> `VerifyError`, the `AttestationVerifier` trait, the `ManagedTokenVerifier`
> reference backend, and `AttestationLane<V>` implementing the shipped
> `EvidenceLane`. Reuse `Anchor::validity_assumption` and `Anchor::trust_root`
> verbatim so the guarantee matches the distinct-agent open assumption and
> discharges it. Honesty: the reference verifier checks nonce/measurements/freshness
> but does NOT verify the managed service signature — that is the deferred real step
> where the stack leaves pure-data; a verified attestation is `Attested`, never
> `Proven`; a rejected input adds no guarantee or trust root; expired tokens never
> verify. Use `case.observed_at` as the verification time and intersect accepted
> windows. Encode AT-1..5 as unit tests (AT-2 must show the distinctness envelope
> closing and being admitted under require_closed) and ATI-1..5 as proptests. Modify
> no existing crate. Definition of done is in doc 45. Stop when `cargo test -p
> hsai-attestation` is green and report results and any deviations from doc 44.

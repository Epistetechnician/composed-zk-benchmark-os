# <Phase Name> — Implementation Handoff

> Standard handoff template. Copy this for every new phase handoff. Keep the
> section order; fill each section for the phase. The **Paste-Ready Kickoff
> Prompt** at the bottom is what the next agent receives verbatim — it MUST keep
> the Preflight line so every future phase starts on the right base.

## Preflight (do this first)

Confirm this worktree is branched from `master` (not the repo's initial commit) and that the prior-phase crates are present in `crates/` — if they're missing you're on a stale base: stop and rebase onto `master` before building.

## Who This Is For

The engineering agent continuing the Hyper Sacred AI build. State which crates
are already shipped and what this phase adds.

## Context In 60 Seconds

The minimal mental model: what gap exists, what this phase closes, and why.

## Source Of Truth (read in this order)

- `docs/NN-<phase>-spec.md` — THE spec.
- `crates/<prior-crate>/src/lib.rs` — the types/traits you reuse or implement.
- `AGENTS.md` — hard rules.

## The Task

Open a new explicit implementation phase and build `crates/<crate>` per the spec.
State the concrete deliverable.

## The Boundary (read carefully)

The honesty/claim boundary for this phase: what is and is not guaranteed, what is
deferred, and which levels (`Attested` vs `Proven`) may be emitted.

## Hard Constraints (from AGENTS.md)

- New explicit phase; record it in AGENTS.md.
- New separate crate; workspace member; path-depend only on the named crates.
  Modify no existing crate.
- Pure data and interface unless the spec says otherwise. Deterministic.

## Build Plan

1. Toolchain: Rust 1.74.
2. Scaffold the crate; add to workspace members; path-depend on prior crates;
   dev-dep `proptest`.
3. Types and trait per the spec.
4. The lane / entrypoint per the spec.
5. Tests: vectors as unit tests; invariants as proptests.
6. Green: `cargo test -p <crate>`, `cargo fmt --check`, `cargo clippy -p <crate>
   --all-targets -- -D warnings`.

## Definition Of Done

Crate compiles; named vectors pass as unit tests; named invariants hold as
proptests; phase note added to AGENTS.md and `docs/`.

## Correctness Pitfalls

The subtle parts specific to this phase.

## Out Of Scope

What not to build now.

## After This Phase

What the next phase is, for planning only.

## Paste-Ready Kickoff Prompt

> You are continuing the Hyper Sacred AI build in the `composed-zk-benchmark-os`
> repo. Preflight: confirm this worktree is branched from `master` (not the
> repo's initial commit) and that the prior-phase crates exist in `crates/` — if
> they're missing, stop and rebase onto `master` before building. Read
> `docs/NN-<phase>-handoff.md`, then `docs/NN-<phase>-spec.md`, then the prior
> crates it names, and `AGENTS.md`. Open a new explicit implementation phase and
> build `crates/<crate>` exactly per the spec. <phase-specific instructions and
> honesty boundary>. Definition of done is in the handoff. Stop when `cargo test
> -p <crate>` is green and report results and any deviations from the spec.

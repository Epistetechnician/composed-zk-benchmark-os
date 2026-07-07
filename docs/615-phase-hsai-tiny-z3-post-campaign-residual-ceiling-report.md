# Phase 615 HSAI Tiny Z3 Post-Campaign Residual Ceiling Report

State slice: `phase-615-hsai-tiny-z3-post-campaign-residual-ceiling-report`.

This report is the current single residual-ceiling record after Phases 603-614.
It states exactly what changed, exactly what remains blocked, and the current
decision on the local multi-obligation Z3 campaign.

This phase is documentation-only. It does not add Rust code, change Cargo
metadata, add dependencies, add command runners, write generated artifacts,
read raw transcripts, call network services, read credentials, import external
results, mutate the accepted Evidence Ledger, accept independent external
reproduction, create accepted formal evidence, create Level2+ evidence,
populate score axes, run Lean, run SMT/Z3, run COBALT, run Rust-to-Lean
extraction, create proof artifacts, create checker transcripts, create solver
certificates, create benchmark evidence, record human-review acceptance, claim
semantic correctness, claim production readiness, claim SOTA, claim
breakthrough status, claim full security, claim external audit status, or
grant authority to execute an action.

## What Changed

Phases 603-614 changed the local HSAI tiny-Z3 lane in these exact ways:

- Phase 603 fixed the Phase 531 exactness predicate so the canonical Phase 529
  real-Z3 `SolverUnsatWithoutCertificate` result for the gateway digest-binding
  obligation can propagate through the in-memory local accepted-append path.
- Phase 604 materialized that same local real-Z3 path through the existing
  local accepted-ledger JSON artifact machinery, still as `LocalReplay` /
  `Level1LocalReplay`.
- Phase 605 defined the external-review handoff packet for the Phase 604 local
  materialized path.
- Phase 606 defined the future returned operator-capture boundary.
- Phase 607 implemented quarantined local operator-capture packet
  materialization and readback over declared Phase 604 run telemetry.
- Phase 608 defined the exact-command local staging-runner boundary.
- Phase 609 added an operator-facing local example that executes the exact
  Phase 604 focused command and packages bounded transcript digests through the
  Phase 607 quarantined capture materializer.
- Phase 610 defined the in-memory staging-run audit boundary.
- Phase 611 implemented an in-memory audit summary over one readback-valid
  Phase 607/609 capture manifest.
- Phase 612 recorded the first residual-ceiling report after Phases 603-611.
- Phase 613 defined the local multi-obligation campaign boundary over existing
  Phase 529 hermetic local Z3 result objects.
- Phase 614 implemented the in-memory local campaign summary over multiple
  existing Phase 529 result objects, including unique-obligation checks,
  `unsat`/`sat` counts, optional mixed-verdict requirement, per-result digest
  visibility, and fail-closed nonpromotion validation.

The current supported statement is only:

```text
The repository can run local Phase 529 Z3 obligations, summarize one mixed
two-obligation local campaign in memory, and keep that campaign below accepted
evidence, Level2+, score-axis, proof, benchmark, semantic-correctness, and
production-readiness claims.
```

## Campaign Decision

Decision: run no broader campaign now.

The Phase 614 focused test already exercises the current useful local campaign:
one Phase 404 `unsat` obligation and one scoped `sat` obligation summarized
together through `GatewayFormalTinyZ3RealMultiObligationCampaignSummary`.
When a local `z3` executable is available, the test runs both obligations
through the Phase 529 hermetic local Z3 runner before summarizing them.

The campaign remains `Level1LocalReplay` only.

The next local campaign expansion should not happen until a future docs-first
boundary names:

- the exact obligation set;
- the stop rules;
- whether durable ignored output is allowed;
- the replay manifest shape;
- the nonpromotion checks;
- the reason a larger campaign would produce useful local data instead of
  repeated fixture noise.

Until that boundary exists, the correct campaign state is:

- keep the Phase 614 two-obligation mixed campaign as the current local
  campaign;
- rerun it only as a verification gate;
- do not create durable campaign artifacts;
- do not import campaign results into accepted evidence;
- do not populate score axes from campaign results;
- do not claim formal proof, semantic correctness, production readiness, SOTA,
  or full security from the campaign.

## What Remains Blocked

The repo remains a Level 1 local Rust foundation. It is not a deployable
system.

Backend execution remains blocked as a staged service:

- no server binary;
- no shipped REST/RPC API;
- no worker process;
- no production or staging traffic entrypoint.

Persistence remains blocked:

- no database;
- no object store;
- no queue;
- evidence ledgers remain local JSON artifacts only.

Deployment remains blocked:

- no Dockerfile;
- no Kubernetes manifest;
- no Terraform;
- no CI deployment step;
- no Makefile.

UI and operations remain blocked:

- no UI/dashboard;
- no normal-gate credential path;
- no live provider calls in normal gates;
- no operator-live lane promoted into ordinary verification.

Evidence promotion remains blocked:

- no accepted external evidence;
- no accepted formal evidence;
- no accepted independent external reproduction;
- no Level2+ evidence;
- no score-axis population;
- no benchmark evidence;
- no external audit evidence.

Proof authority remains blocked:

- no Lean proof authority;
- no COBALT execution evidence;
- no Rust-to-Lean proof authority;
- no checker transcript authority;
- no solver certificate authority.

Claim escalation remains blocked:

- no semantic-correctness claim;
- no production-readiness claim;
- no SOTA claim;
- no breakthrough claim;
- no full-security claim;
- no global uniqueness claim;
- no authority to execute an action.

## Current Stop Rule

Do not deploy.

Do not widen beyond the current Phase 614 two-obligation local campaign until a
new docs-first boundary justifies a larger local campaign and preserves the
`Level1LocalReplay` ceiling.

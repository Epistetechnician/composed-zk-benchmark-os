# V19 update-governance protocol

State slice: `continual-learning-update-governance-v1`.

Status: implemented as a local pure-data contract and hermetic tests.

Claim ceiling: `LocalDevelopmentUpdateGovernanceContract`.

## Purpose

V19 turns the deployment-governance gap into an executable boundary. It does
not train or serve a model. It validates whether a proposed model snapshot can
enter a tenant-scoped canary and promotion ledger after a fixed safety, utility,
consent, and provenance check.

The contract is intentionally digest-only. Model weights, transcripts, and raw
feedback remain repository-external artifacts referenced by digests.

## Candidate contract

Every `UpdateCandidate` binds:

- tenant identity;
- parent and candidate model identifiers plus artifact digests;
- update-data digest;
- unique source-event identifiers and their tenant bindings;
- the exact `tenant-training-opt-in-v1` consent scope;
- baseline/candidate jailbreak, backdoor, and persona-drift rates;
- baseline/candidate utility;
- canary sample, failure, and unknown counts.

The default policy is fail-closed:

- source events are required, unique, and same-tenant;
- consent must match the fixed opt-in scope;
- candidate safety metrics may not regress;
- safety unknowns are not accepted;
- candidate utility may not regress;
- canary samples are required, unknowns are forbidden, and failure rate must be
  zero.

Rejected candidates are quarantined with typed reason markers. They do not
become eligible for promotion.

## Lifecycle contract

```text
baseline
  -> canary_eligible | quarantined
canary_eligible
  -> promoted | quarantined (stale parent)
promoted
  -> promoted (next parent) | rollback
rollback
  -> promoted snapshot selected from prior history
```

The ledger is per tenant and append-only. Promotion requires the candidate's
parent digest to equal the current head. A stale candidate cannot silently
fork the tenant's active lineage; the failed attempt is recorded as a
quarantine event. Rollback appends a new event and never deletes or rewrites
prior history.

Every event carries the candidate manifest digest when applicable, the prior
event digest, and its own digest. Exported bundles carry a bundle digest and
are independently readback-validated. Quarantine and canary events are audit
events and do not move the model head; only baseline, promotion, and rollback
events do.

## Verification

```text
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q experiments/continual_learning/tests/test_update_governance.py
```

The tests cover valid admission, cross-tenant rejection, safety unknowns and
regressions, failed canaries, optimistic parent conflicts, promotion,
non-destructive rollback, manifest binding, digest-chain validation, and
tampered bundle rejection.

## Explicit nonclaims

This phase does not provide:

- model training, model serving, or deployment integration;
- cryptographic signatures or authenticated provider identity;
- proof that a safety panel is complete or scientifically valid;
- privacy, legal, consent, or data-license compliance beyond the typed local
  consent field;
- real user feedback, expert-quality estimation, poisoning detection, or
  cross-provider portability;
- production readiness, accepted benchmark evidence, scientific evidence,
  breakthrough claims, or runtime/action authority.

Future work may add a reviewed quality/poisoning panel, model snapshot
registry, canary execution adapter, rollback executor, tenant export/import,
and serving-cost measurements. Those are separate state slices.

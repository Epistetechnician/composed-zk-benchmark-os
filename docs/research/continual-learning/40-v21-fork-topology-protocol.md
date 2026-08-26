# V21 continual-learning fork topology protocol

State slice: `continual-learning-fork-topology-v1`  
Claim ceiling: `LocalDevelopmentForkTopologyContract`

V21 defines the persistent state topology required before a future learner can
update weights or adapters. It records digest-only model and fork lineage for
one shared base and isolated tenant forks. It does not contain weights, load a
checkpoint, execute training, serve a model, or grant deployment authority.

## Contract

`experiments/continual_learning/fork_topology.py` defines:

- `ForkNode`, an immutable digest-only model/fork record;
- `ForkTopologyPolicy`, which fixes tenant consent, shared-merge consent,
  review status, and allowed update kinds;
- `ForkLedger`, an append-only topology ledger with mutable scope heads;
- `MergeProposal`, which makes tenant-to-shared pooling explicit; and
- `validate_topology_bundle` plus `validate_portable_manifest`, independent
  readback seams for the full topology and a metadata-only fork export.

The topology has two scope kinds:

- `shared:global`, which carries the shared model lineage; and
- `tenant:<id>`, which carries one tenant's private learning lineage.

Tenant forks may descend from the current shared head or their current tenant
head. They may not descend from another tenant or branch from a stale shared
parent. A tenant fork must be portable and carry a V20-compatible source
update digest.

The public mutation methods reject malformed identifiers and policies before
performing dictionary lookups or state changes. Independent topology readback
also revalidates proposal scope, source-update bindings, merge-result bindings,
proposal/event correspondence, and shared-root portable lineage; resealing a
bundle does not bypass those semantic checks.

## Merge and rollback semantics

Shared pooling is a separate transition, not an implicit consequence of tenant
learning. A merge proposal must bind:

- a current tenant head;
- the current shared head;
- a candidate model digest different from the shared target;
- the separate `shared-model-merge-opt-in-v1` consent scope;
- the declared reviewed status and review digest; and
- the tenant fork's source-update digest.

An eligible proposal does not move a head. Acceptance creates a new shared
descendant and leaves the tenant head unchanged. Invalid direction, stale
source, missing consent, missing review, and binding drift quarantine without
mutation.

Rollback moves only the selected scope head to an existing ancestor. It never
deletes later forks or erases the append-only event history.

## Portability

`export_portable_manifest` produces a metadata-only lineage manifest. It
explicitly carries `weights_included=false` and
`provider_lock_included=false`. This is a portability contract and exit-path
receipt, not a weight export, serving adapter, or cross-provider execution
proof.

## End-to-end local handoff

The bounded chain is:

`V20 admitted source digest -> V19 update candidate governance -> V21 tenant`
`fork head -> reviewed shared merge proposal -> shared descendant or rollback`

The focused tests cover deterministic root/fork export, cross-tenant isolation,
stale-head rejection, merge direction and consent, shared acceptance, rollback
retention, portable manifests, resealed bundle tampering, policy drift, and
malformed direct inputs, forged proposal/event bindings, and absence of
execution/network/weight-loading surfaces.

## Verification

```text
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q \
  experiments/continual_learning/tests/test_fork_topology.py
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q experiments/continual_learning/tests
```

## Explicit nonclaims

This phase does not provide model training, continual parameter updates,
weight or adapter storage, checkpoint loading, inference, serving, batching
economics, source identity or quality verification, poisoning detection,
privacy or legal certification, cryptographic signatures, cross-provider
execution, accepted evidence, benchmark or scientific evidence, production
readiness, SOTA, breakthrough, or runtime/deployment authority.

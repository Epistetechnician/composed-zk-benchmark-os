# V20 continual-learning source admission protocol

State slice: `continual-learning-source-admission-v1`  
Claim ceiling: `LocalDevelopmentSourceAdmissionContract`

V20 closes the source-to-update-data boundary immediately before the V19
update-governance contract. It admits only digest-bound source receipts for one
tenant and one declared update window. The implementation stores no raw
feedback or transcript content, verifies no actor or reviewer, executes no
model, and grants no update, serving, or deployment authority.

## Contract

`experiments/continual_learning/source_admission.py` defines:

- `SourceEvent`, a raw-content-free receipt with event, label, and declared
  quality-receipt digests;
- `SourceAdmissionPolicy`, which fixes the tenant, update window, consent
  scope, and allowed declared source kinds;
- `admit_source_events`, a deterministic fail-closed decision function; and
- `export_admission_bundle` plus `validate_admission_bundle`, which bind the
  accepted update-data manifest and its outer bundle by SHA-256.

The accepted manifest contains only sorted event IDs, event digests, label
digests, quality-receipt digests, tenant, window, state slice, and claim
ceiling. Its digest is suitable for V19's existing `update_data_digest` field.
V19 remains responsible for safety, utility, canary, parent, promotion, and
rollback governance.

## Decision semantics

The only admissible result is `accepted` when every event is structurally
valid, tenant- and window-bound, consent-compatible, non-duplicated, free of
declared conflict, uses an allowed source kind, reports declared quality as
accepted, and carries a structurally valid quality-receipt digest.

`quarantined` is returned for explicit adverse or out-of-scope conditions:
cross-tenant input, wrong consent or window, disallowed source kind, malformed
event/label digests, duplicate event identities or digests, conflicting label
digests, explicit quality quarantine, or a declared poisoning marker.

`unknown` is returned when quality is not known or an accepted quality status
lacks a valid receipt digest. If a batch contains both unknown and quarantined
conditions, quarantine takes precedence. No non-accepted decision emits an
update-data digest.

These are metadata-admission outcomes, not source-trust, poisoning-detection,
expertise, privacy, legal, or scientific findings. A structurally valid
quality receipt does not authenticate the receipt issuer or prove the quality
of the underlying feedback.

## End-to-end local handoff

The bounded local chain is:

`SourceEvent receipts -> V20 admission -> admitted update-data digest -> V19 UpdateCandidate -> V19 safety/utility/canary gates -> V19 ledger`

The V20 tests prove input-order-independent manifests, clean handoff into a
V19 canary-eligible candidate, fail-closed adversarial cases, and independent
outer/nested bundle readback. The test suite uses synthetic digests only.

## Verification

```text
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q experiments/continual_learning/tests/test_source_admission.py
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q experiments/continual_learning/tests
```

## Explicit nonclaims

This phase does not provide actual feedback collection, raw-content review,
source identity or expertise verification, quality measurement, poisoning
detection, conflict resolution, consent authority, model training, model
execution, serving, deployment, provider integration, network access,
credentials, cryptographic signatures, accepted evidence, benchmark or
scientific evidence, production readiness, SOTA, breakthrough, or runtime
authority.

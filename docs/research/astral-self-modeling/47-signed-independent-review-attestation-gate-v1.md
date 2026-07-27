# Signed Independent-Review Attestation Gate V1

State slice: `astral-independent-review-attestation-gate-v1`.

Status: `LocalSignedReviewProtocolCandidate`.

Claim ceiling: `LocalImmutableValidationCandidate`.

## Problem

The V1 capsule makes the source and evidence portable, but its review forms are
unsigned templates. They do not bind a reviewer to a preregistered public key,
prevent one person from filling both roles, bind a decision to a fresh request,
or force material findings to stop the gate.

This protocol closes those mechanical gaps. It cannot establish that a key
belongs to a genuinely independent human. That identity and conflict check
remains an external governance responsibility.

## Trust and request flow

1. An external coordinator selects two genuine reviewers before either review.
2. Each reviewer supplies an Ed25519 public key. Private keys never enter the
   repository, capsule, kit, or author environment.
3. The coordinator completes a canonical reviewer registry with different
   identities, names, keys, affiliations, and roles.
4. The registry SHA-256 is published or otherwise pinned before requests issue.
5. `prepare_review.py` creates fresh, role-bound requests and blank decision
   templates bound to the exact capsule, release commit/tree, package, and
   author report.
6. Each reviewer runs the capsule, audits the required material, records
   evidence-file digests and findings, canonicalizes the decision, and signs
   the exact bytes with:

```text
ssh-keygen -Y sign \
  -f <reviewer-private-key> \
  -n astral-independent-review-v1 \
  <role>.decision.json
```

7. `verify_review_gate.py` reconstructs allowed signers from the pinned
   registry, verifies both signatures, validates evidence bytes, enforces
   different reviewers and keys, and rejects unresolved material findings.

## Fail-closed result

The mechanical gate can emit:

- `SyntheticSignedReviewProtocolPassed` only for a `protocol_test` registry;
- `SignedReviewQuorumCandidate` for two valid externally designated decisions;
- `SignedReviewGateRejected` when either reviewer fails the artifact.

`SignedReviewQuorumCandidate` is not evidence acceptance. It records valid
signatures and declarations but does not prove reviewer independence,
affiliation, competence, or absence of undisclosed conflicts. A human
coordinator must verify those facts before describing the reviews as
independent.

No outcome from this protocol validates introspection, self-modeling,
privileged internal access, Stage 0C, Stage 1, benchmark evidence, or production
readiness. Independent implementation replication remains a separate gate.

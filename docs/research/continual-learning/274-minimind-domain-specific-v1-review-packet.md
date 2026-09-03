# MiniMind domain-specific continual-learning V1 review packet

State slice: `continual-learning-minimind-domain-specific-v1`.

Review status: `PENDING_INDEPENDENT_REVIEW`.

This packet defines the exact bytes that must be independently reviewed before
any model-bearing MiniMind execution. It is not an acceptance receipt and does
not authorize training or assessment.

## Frozen input set

1. `docs/research/continual-learning/273-minimind-domain-specific-v1-protocol.md`
2. `docs/research/continual-learning/274-minimind-domain-specific-v1-review-packet.md`
3. `experiments/continual_learning/minimind_domain_specific_v1.py`
4. `experiments/continual_learning/validate_minimind_domain_specific_v1.py`
5. `experiments/continual_learning/tests/test_minimind_domain_specific_v1.py`
6. `docs/research/continual-learning/275-minimind-domain-specific-v1-implementation-manifest.json`
7. `AGENTS.md`

The reviewer must recompute every digest after the input set is frozen. Any
byte change voids the review and requires a new packet digest.

## Required independent checks

- source URL, immutable commit, license, required-file roster, and clean
  checkout are enforced;
- the synthetic generator and independent validator are arithmetically
  equivalent without importing each other;
- fit, tune, and assessment identities and all 108 synthetic trials are
  complete;
- the model runner preserves the same six-arm, three-split, three-replicate,
  forward/reverse factorial and verifies checkpoint restoration at every
  stage;
- domain order, equal update accounting, checkpoint restoration, and
  fail-closed missingness are executable;
- the primary endpoint and hard guards cannot be selected from assessment
  outcomes;
- the real runner verifies reviewer identity, packet digest, Ed25519
  signature, and operator/reviewer separation before importing MiniMind or
  loading a model;
- outputs remain outside the repository and no provider, production, or
  benchmark claim is reachable;
- the claim ceiling remains bounded and prior closed lanes remain untouched.

## Receipt requirements

An acceptable future receipt must be JSON-only, identify this exact packet by
SHA-256, set reviewer role to `independent`, set disposition to
`ACCEPTED_FOR_MODEL_EXECUTION`, identify a reviewer distinct from the
operator, and carry a valid Ed25519 signature over its canonical payload.

Until that receipt exists, the only executable path is the exact-synthetic
fixture.

Every mutation in this phase names state slice
`continual-learning-minimind-domain-specific-v1`.

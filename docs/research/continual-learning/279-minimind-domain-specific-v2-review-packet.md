# MiniMind domain-specific continual-learning V2 review packet

State slice: `continual-learning-minimind-domain-specific-v2`.

Review status: `PENDING_INDEPENDENT_REVIEW`.

This packet defines the exact seven-file input set for a read-only independent
review. It is not an execution receipt and does not authorize model activity.

## Frozen input set

1. `docs/research/continual-learning/278-minimind-domain-specific-v2-protocol.md`
2. `docs/research/continual-learning/279-minimind-domain-specific-v2-review-packet.md`
3. `experiments/continual_learning/minimind_domain_specific_v2.py`
4. `experiments/continual_learning/validate_minimind_domain_specific_v2.py`
5. `experiments/continual_learning/tests/test_minimind_domain_specific_v2.py`
6. `docs/research/continual-learning/280-minimind-domain-specific-v2-implementation-manifest.json`
7. `AGENTS.md`

The reviewer must recompute all seven SHA-256 values after freeze. Any byte
change invalidates the review and requires a new V2 freeze and review.

## Required independent checks

- source URL, remote, Apache-2.0 license text, immutable commit, required-file
  roster, clean checkout, and source digests are verified from the checkout;
- the synthetic generator and validator independently reproduce all 108 exact
  trial identities and arithmetic values;
- the exact replicate, order-seed, direction, arm, and split rosters are
  required, including order-seed binding in paired order deltas;
- no record can be silently dropped during tokenization or execution;
- padded-token and optimizer-step accounting is equal across joint, replay,
  sequential, and adapter arms;
- checkpoint serialization is loaded into a recreated model instance and
  compared at every stage;
- every model trial has a deterministic repeatability rerun;
- fit and tune complete before an explicit tune lock; assessment begins only
  afterward;
- the receipt binds this packet and every other frozen file digest, verifies
  Ed25519, and separates reviewer from operator before MiniMind import;
- external corpus/output custody is enforced, output mode is `0700`, and only
  aggregate contract output remains;
- the claim ceiling is bounded and V1/prior-lane scientific artifacts are not
  imported.

## Receipt requirements

An acceptable receipt must be JSON-only, use schema
`minimind-domain-specific-v2-execution-receipt`, identify this packet by its
current SHA-256, include the exact seven-file digest map, identify an
independent reviewer distinct from the operator, set disposition
`ACCEPTED_FOR_MODEL_EXECUTION`, and carry a valid Ed25519 signature over its
canonical payload.

No parent or operator-generated receipt is valid.

Every mutation in this phase names state slice
`continual-learning-minimind-domain-specific-v2`.

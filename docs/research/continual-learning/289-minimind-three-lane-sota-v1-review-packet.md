# MiniMind three-lane V1 independent review packet

State slice: `continual-learning-minimind-three-lane-sota-v1`.

This packet is the exact review boundary for the bounded three-lane MiniMind
pilot. It must be reviewed after the listed bytes are frozen and before any
model import, training, or inference. A passing local test is not independent
authorization.

## Frozen packet contents

- `AGENTS.md`
- `docs/research/continual-learning/288-minimind-three-lane-sota-v1-protocol.md`
- this review packet
- `docs/research/continual-learning/290-minimind-three-lane-sota-v1-implementation-manifest.json`
- `experiments/continual_learning/minimind_three_lane_sota_v1.py`
- `experiments/continual_learning/validate_minimind_three_lane_sota_v1.py`
- `experiments/continual_learning/tests/test_minimind_three_lane_sota_v1.py`

The reviewer must recompute every digest from the current checkout. A changed
byte invalidates the entire packet and requires a fresh V1 review.

## Required review checks

The reviewer must independently verify:

- state-slice identity and exclusion of V1/V2/V3 MiniMind scientific output;
- source URL, commit, required-file digests, Apache-2.0 identity, and clean
  external checkout;
- synthetic corpus freshness, owner-only custody, nine-file roster, global
  record/author disjointness, and fixture-only status;
- exact lane/arm/split/seed/order roster and aggregate-only retention;
- per-arm tune lock before assessment, with all admitted arms assessed;
- absence of benchmark, real-local-corpus, provider, energy, and SOTA claims;
- model boundary: no pretrained checkpoint is claimed, runtime is offline,
  and model output is qualification-only;
- checkpoint restore, repeatability, finite-output, zero-attrition, and state
  accounting guards;
- operator/reviewer separation and the external trust chain;
- validator independence: it must not import the runner or accept a runner
  digest as a substitute for semantic validation;
- the claim ceiling and the explicit frontier-method exclusions.

The reviewer must reject if any listed method is called reproduced without a
faithful implementation, if assessment occurs before locks, if raw records
are retained in the result root, if a receipt is self-attested, or if the
result is presented as SOTA evidence.

## Required receipt

Only the external independent reviewer may issue
`ACCEPTED_FOR_MODEL_EXECUTION`. The receipt must bind this packet SHA-256,
the complete frozen-file digest map, the fresh source and corpus manifest
digests, the certified reviewer public key, the external reviewer registry,
the operator binding, and the exact state slice. The operator binding digest
must cover its unsigned identity fields and its Ed25519 signature must cover
the canonical JSON of those unsigned identity fields. The receipt signature
must cover canonical JSON of every receipt field except `signature`. Both
artifacts must be stored with owner-only permissions. Silence, malformed prose,
test success, or a reviewer identity equal to the operator is not acceptance.

## Review disposition

Disposition is blank until the exact packet is independently reviewed. A
rejection is terminal for this V1 identity. A passing review authorizes only
the bounded offline model pilot described in the protocol; it does not open a
published benchmark or scientific assessment lane.

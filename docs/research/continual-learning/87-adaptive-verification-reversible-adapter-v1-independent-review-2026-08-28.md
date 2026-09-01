# Adaptive verification with reversible adapters v1 independent review

Date: 2026-08-28.

State slice: `continual-learning-adaptive-verification-reversible-adapter-v1`.

Reviewer role: separate worker.

Reviewed protocol: `docs/research/continual-learning/85-adaptive-verification-reversible-adapter-v1-protocol.md`.

Reviewed protocol SHA-256:
`a7abfa2f1b2d1edd1113824334850f090125e4efa8cb990ca45ad15a6316d14d`.

## Verdict

`REJECT`

The protocol is not precise enough to authorize implementation, model
loading, corpus acquisition, H100/GiveMeANode provisioning, qualification, or
assessment.

## Findings

- Selection is not reproducible: the lexical novelty formula, score weighting,
  top-half rounding, and exact tie-breaking are unspecified.
- The learner contract is incomplete: LoRA rank and trainable layers,
  optimizer, learning rate, batch size, iterations, tokenization, and exact
  seed/order identities are absent.
- The estimand and bootstrap aggregation hierarchy are ambiguous across
  documents, cases, seeds, and token weighting.
- The power simulation lacks a specified data-generating process,
  variance/correlation model, and reliability definition.
- Custody manifests, retention termination, validator checks, control-arm
  execution rules, and H100 runtime-equivalence details are not mechanically
  defined.

## Receipt

```yaml
state_slice: continual-learning-adaptive-verification-reversible-adapter-v1
reviewed_protocol_path: docs/research/continual-learning/85-adaptive-verification-reversible-adapter-v1-protocol.md
reviewed_protocol_sha256: a7abfa2f1b2d1edd1113824334850f090125e4efa8cb990ca45ad15a6316d14d
reviewer_role: separate-worker
verdict: REJECT
execution_authorized: false
review_date: 2026-08-28
```

Per the protocol, this rejection is terminal for the slice. It does not
authorize an adaptive repair or a revised protocol under the same identity.

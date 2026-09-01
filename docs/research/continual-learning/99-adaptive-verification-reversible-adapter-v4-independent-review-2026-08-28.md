# Adaptive verification with reversible adapters v4 independent review

Date: 2026-08-28.

State slice: `continual-learning-adaptive-verification-reversible-adapter-v4`.

Reviewed protocol:
`docs/research/continual-learning/97-adaptive-verification-reversible-adapter-v4-protocol.md`

Reviewed protocol SHA-256:
`6991f8ce5f9d98a0f2728e894ae9fa5897551d5cd9096ba2273652e09cd0df35`

Reviewer role: `independent-theory-reviewer`.

Verdict: `REJECT`.

Execution authorized: `false`.

## Findings

1. V4 identity is stated, but distinctness from V1–V3 cannot be independently
   verified from the permitted packet because the prior identities are not
   provided.
2. MLX/Metal is the sole actor and H100/GiveMeANode model execution is
   excluded.
3. Full-sequence output shape and batch/sequence axes are unstated; Gemma
   module paths and resolved LoRA keys are not fully closed; no exact command
   is bound in the protocol.
4. Registered-volume identity and canonical serialization/digest rules for
   several manifests and receipts are incomplete.
5. Freshness relies on an unspecified set of prior manifests; missing or
   repeated Gutenberg boundary markers have no failure behavior.
6. `score(w)` does not bind `w` to the min-max calculation, and the regex
   escaping does not establish the intended lexical-word behavior.
7. `matched_energy` is correctly diagnostic-only and non-confirmatory.
8. The rejected-fit guard does not uniquely identify the 12 windows for each
   primary arm.
9. “Independent full reload repeats” is not operationally defined.
10. Power hash tags, ranges, DGP, null, alternative, rejection rule, and
    thresholds are reproducible.
11. Event payload hashes have no payload field or payload store; power
    calibration is ordered after qualification while also listed as a
    qualification gate.
12. The lock schema, canonical serialization, digest procedure, and complete
    decision field set are not closed.
13. Qualification and event order contradict each other at power calibration.
14. Terminal precedence for overlapping custody, metric, lock, review,
    retention, and event-order failures is not defined.
15. The claim ceiling is appropriately bounded and excludes Astral, Stage 0C,
    Stage 1, self-modeling, general continual learning, benchmark, H100
    equivalence, and production claims.

## Decision

V4 is closed as `ProtocolRejectedBeforeImplementation`. No model, corpus,
adapter, training, assessment, provider, H100, GiveMeANode, or scientific
result artifact was created under this state slice.

# Adaptive verification with reversible adapters v3 independent review

Date: 2026-08-28.

State slice: `continual-learning-adaptive-verification-reversible-adapter-v3`.

Reviewed protocol:
`docs/research/continual-learning/93-adaptive-verification-reversible-adapter-v3-protocol.md`

Reviewed protocol SHA-256:
`2f3c9562d9247abd75267e3de34ecd36ce5dfec5b353520f8976291d487134e0`

Reviewer role: `independent-theory-reviewer`.

Verdict: `REJECT`.

Execution authorized: `false`.

## Findings

1. The state slice and claim boundary are distinct, but forward-pass semantics
   for `logits(w)` and the lexical-regex escaping are unresolved.
2. The MLX/Metal sole-model boundary is clear; H100 and GiveMeANode model
   execution are excluded.
3. Model custody is incomplete: stable-file enumeration, LoRA target modules,
   exact trainable layer identities, scoring semantics, and complete data-file
   construction are unspecified.
4. Gutenberg IDs and split counts are explicit, but freshness certification,
   redirect behavior, and raw/normalized source custody locations are absent.
5. `matched_energy` is only an audit label; its independent adapter and metric
   status is not defined.
6. The literal Python regular-expression representation is ambiguous and can
   produce different vocabularies.
7. The 5% relative-loss guard has no formula, denominator, aggregation level,
   or zero-denominator rule; forward-pass semantics are incomplete.
8. The count, identity, and schedule of repeated reliability measurements are
   unspecified.
9. Power hash inputs for document, case, and case-document terms and the full
   outer/inner index ranges are unspecified; the power decision covers only a
   bootstrap endpoint rather than the complete result gate.
10. The custody layout omits normalized files and leaves root path, retention
    deadline, timestamp/canonicalization, sequence origin, payload schemas,
    review receipts, and aggregate-validator behavior open.
11. The prediction lock does not bind every threshold, bootstrap/power field,
    retention deadline, validator identity, adapter field, and control; the
    reviewed digest is ambiguous.
12. Qualification lacks exact probe contents, repeat counts, module/shape
    expectations, trainable-layer identities, validator preflight behavior,
    and a compute-gate definition.
13. Theory and implementation authorization receipts are not in the event
    schema and are not mechanically bound to later qualification or assessment.
14. Failure classes are not exhaustive or mutually exclusive for power,
    custody, review, lock, and control-only failures.

## Decision

V3 is closed as `ProtocolRejectedBeforeImplementation`. No model, corpus,
training, assessment, provider, or external compute execution occurred under
this slice. V3 artifacts are not inputs to any later slice.

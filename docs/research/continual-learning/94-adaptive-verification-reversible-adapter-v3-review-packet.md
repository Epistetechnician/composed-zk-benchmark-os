# Adaptive verification with reversible adapters v3 review packet

Date: 2026-08-28.

State slice: `continual-learning-adaptive-verification-reversible-adapter-v3`.

Protocol under review:
`docs/research/continual-learning/93-adaptive-verification-reversible-adapter-v3-protocol.md`

Protocol SHA-256:
`2f3c9562d9247abd75267e3de34ecd36ce5dfec5b353520f8976291d487134e0`

Status: `IndependentTheoryReviewPending`.

## Review boundary

The reviewer receives this packet and the frozen V3 protocol only. The
reviewer must not edit either file, load a model, acquire data, run training,
run assessment, call GiveMeANode, or authorize implementation. Any protocol
edit changes the digest and invalidates this review.

V1 and V2 are closed immutable rejections. Astral, V48, V82, and all prior
scientific data, adapters, activations, effects, predictions, and results are
out of scope and must not be treated as inputs.

## Required independent checks

The reviewer must issue `ACCEPT` only if every item below is executable and
internally consistent:

1. The state slice, falsifiable controller theory, actor, runtime, model
   custody, and claim ceiling are distinct from V1 and V2.
2. The Gemma 3 MLX/Metal runtime is the sole model execution environment;
   H100/GiveMeANode is not silently treated as an equivalent actor.
3. The exact model shape, dtype, package versions, tokenizer policy, offline
   environment, socket guard, stable-file digest list, and training command
   are sufficient for independent reconstruction.
4. The 24 Gutenberg IDs, source URLs, source-manifest fields, normalization,
   tokenizer checks, two-window rule, and fit/tune/assessment identity are
   fresh, document-disjoint, and deterministic.
5. The adaptive, fixed, shuffled, constant, text-only, surprisal-only, and
   matched-energy arms are fully specified and have equal fit-token budget.
6. The selection score, vocabulary regex, min-max ties, hash tie break, order
   hashes, seed cross-product, and case identity have no unbound choices.
7. The NLL, document effect, eight-case aggregation, six-document estimand,
   threshold, document positivity rule, relative-loss guards, and sole
   confirmatory comparison are exactly measurable.
8. The bootstrap hash stream, replicate count, endpoint indexes, missingness
   rule, and reliability limits are executable without analyst discretion.
9. The power data-generating process, hash-based normal generator, null and
   alternative, inner bootstrap, and pass/fail thresholds are reproducible
   and do not calibrate at the decision boundary.
10. The custody layout, write-once versus append-only distinction, event
    schema, event order, lock transition, source-validation order, raw
    retention deadline, and aggregate-only validator behavior are compatible.
11. The prediction lock is sealed before assessment effects and binds all
    configuration and control fields needed to prevent post hoc tuning.
12. Qualification has explicit parity, repeatability, no-op, reload, shape,
    intervention-reach, custody, and validator gates, with fail-closed
    classification and no adaptive repair.
13. The two-review ordering is preserved: theory review, implementation
    authorization, qualification, fit/tune lock, pre-assessment review, then
    assessment and aggregate validation.
14. The result classes and claim ceiling cannot be inflated into continual
    learning, benchmark, Astral, introspection, Stage 0C, Stage 1, or
    production evidence.

## Verdict contract

The independent receipt must be written as a new immutable file with this
schema:

```yaml
state_slice: continual-learning-adaptive-verification-reversible-adapter-v3
reviewed_protocol_path: docs/research/continual-learning/93-adaptive-verification-reversible-adapter-v3-protocol.md
reviewed_protocol_sha256: 2f3c9562d9247abd75267e3de34ecd36ce5dfec5b353520f8976291d487134e0
reviewer_role: independent-theory-reviewer
verdict: ACCEPT or REJECT
findings:
  - exact finding for each required check
execution_authorized: false
review_date: 2026-08-28
```

`REJECT` terminates V3 before implementation and requires a terminal closure
record. `ACCEPT` permits implementation drafting and a separately named
implementation authorization only; it does not permit model loading, corpus
acquisition, training, or assessment.

## Reviewer decision rule

The reviewer must reject if any formula, identity, custody field, event
transition, validator input boundary, power rule, failure classification, or
claim ceiling requires an unstated choice. Near-miss scientific promise is not
a basis for acceptance.

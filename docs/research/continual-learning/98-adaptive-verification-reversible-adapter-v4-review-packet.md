# Adaptive verification with reversible adapters v4 review packet

Date: 2026-08-28.

State slice: `continual-learning-adaptive-verification-reversible-adapter-v4`.

Reviewed protocol:
`docs/research/continual-learning/97-adaptive-verification-reversible-adapter-v4-protocol.md`

Protocol SHA-256:
`6991f8ce5f9d98a0f2728e894ae9fa5897551d5cd9096ba2273652e09cd0df35`

Status: `IndependentTheoryReviewPending`.

## Review boundary

The independent reviewer receives this packet and the frozen V4 protocol only.
The reviewer must not edit either file, load a model, acquire corpus data, run
training, run assessment, call GiveMeANode, or authorize implementation. Any
protocol edit changes the digest and invalidates the review.

V1, V2, and V3 are immutable protocol rejections and are not inputs. Astral,
V48, V82, and all other lane artifacts are out of scope.

## Required checks

The reviewer must issue `ACCEPT` only if all checks are executable and
internally consistent:

1. The V4 identity, falsifiable controller theory, actor, custody root, and
   claim ceiling are distinct from V1–V3.
2. The cached Gemma 3 MLX/Metal runtime is the sole model environment; H100
   and GiveMeANode cannot silently become equivalent actors.
3. Model manifest enumeration, package/runtime versions, tokenizer policy,
   full-sequence logit semantics, float64 NLL, socket guard, adapter target
   modules, layer indexes, and training command are exact.
4. The fixed external root, write-once layout, source/normalized locations,
   root permissions, protocol copy, model manifest, and digest rules are
   independently reconstructible.
5. The 24 Gutenberg IDs, URL, redirect, response, normalization, freshness,
   source-manifest fields, tokenizer window rule, and document-disjoint split
   identity are fresh and deterministic.
6. The eight cases, order hashes, score, regex source, novelty, min-max ties,
   score tie-break, fixed arm, and all descriptive controls are unambiguous.
7. `matched_energy` is explicitly diagnostic-only and cannot become a hidden
   confirmatory arm.
8. The NLL, effect, six-document estimand, thresholds, positive-document
   rule, assessment guard, rejected-window guard, invalid-metric rule, and
   single confirmatory comparison are exactly measurable.
9. Reliability repeat count, reload identity, tolerances, missingness, and
   digest failure behavior are exact.
10. Power hash tags, byte ranges, denominators, indexes, DGP, null,
    alternative, rejection rule, and pass thresholds are reproducible and
    calibrate the declared confirmatory gate.
11. Event sequence, sequence origin, timestamp/canonicalization rules,
    payload binding, review/authorization events, assessment transition,
    lock contents, source-validator order, aggregate-validator input boundary,
    retention deadline, and retained fields are compatible.
12. Prediction locking occurs before assessment model loading or assessment
    NLL computation, and the lock binds every decision-relevant digest.
13. Qualification contains exact gates, probe/repeat counts, no-op/reload,
    shape/module, intervention reach, custody, validator, and power checks.
14. Failure classes are mutually exclusive and terminally ordered; no repair
    or adaptive retry is possible within V4.
15. The claim ceiling excludes Astral, Stage 0C, Stage 1, self-modeling,
    general continual learning, benchmark, H100 equivalence, and production
    claims.

## Verdict contract

The reviewer writes a new immutable receipt with this schema:

```yaml
state_slice: continual-learning-adaptive-verification-reversible-adapter-v4
reviewed_protocol_path: docs/research/continual-learning/97-adaptive-verification-reversible-adapter-v4-protocol.md
reviewed_protocol_sha256: 6991f8ce5f9d98a0f2728e894ae9fa5897551d5cd9096ba2273652e09cd0df35
reviewer_role: independent-theory-reviewer
verdict: ACCEPT or REJECT
findings:
  - exact finding for each required check
execution_authorized: false
review_date: 2026-08-28
```

`REJECT` terminates V4 before implementation and requires a terminal closure
record. `ACCEPT` permits implementation drafting and a separate
implementation authorization only; it does not permit model loading, corpus
acquisition, training, or assessment.

## Decision rule

Reject if any formula, identity, path, module, event, validator boundary,
power rule, retention rule, failure class, or claim ceiling requires an
unstated choice. Scientific promise is not a basis for acceptance.

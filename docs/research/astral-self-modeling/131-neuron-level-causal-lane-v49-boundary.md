# Astral neuron-level causal lane V49 — docs-first boundary

State slice: `astral-neuron-level-causal-lane-v49-boundary`
Claim ceiling: `Level0DesignNote` (documentation only; no execution).

## Source and its limits

The Goodfire essay on neuron-level attribution graphs is informal, not peer
reviewed, author-reported, threshold-dependent, and ships no code or data.
It is a hypothesis source only. Its reported numbers (e.g. ablation versus
matched random-neuron controls) are not evidence in this repository.

## Identity

V49 is a fresh protocol identity. It does not reopen V48 (closed
`DevelopmentNoCandidate`), does not reuse V48 or earlier scientific
artifacts as inputs, and does not alter V2/V3 SAE-bundle identities.

## Hypothesis (preregistered, falsifiable)

Ablating a small, fit-selected set of raw model neurons at a fixed layer
reduces a fixed target logit-margin more than ablating matched random neuron
sets of equal size, matched on activation-magnitude percentile and layer,
without any SAE/transcoder/reconstruction loss. Failure of the matched-random
contrast closes V49 as `NoCandidate`.

## Required design (to be frozen before any execution)

- Fresh document-disjoint fit/tune/assessment corpus and new external
  owner-only `0700` custody root.
- Neuron selection on fit only; prediction lock before assessment effects.
- Matched-random control: >= 1000 draws per selected set, matched on layer and
  activation percentile; one-sided test with Holm correction; fixed minimum
  effect and power/ICC analysis.
- Raw activation-shape inspection (percentile profile per neuron) recorded as
  descriptive aggregates only; shape is never used to retune thresholds.
- Unchanged controls: activation-only, text-only, shuffled, constant.
- Aggregate-only retention; raw traces deleted within 72 hours.

## gman execution gate (not satisfied)

Model-bearing execution through `gman` is blocked. Required and absent:
independent packet-bound signed Ed25519 `ACCEPT` (operator may not self-sign),
positive user-authorized hard USD ceiling, exact provider/node identity, and
an allocation receipt. Until all exist, preflight is `REJECT` and nothing runs.

## Nonclaims

No execution, spend, accepted Evidence Ledger mutation, Stage 0C/1 promotion,
introspection or self-modeling claim, benchmark, SOTA, proof, or production
claim. Prior base rate for such lanes is mostly `NoCandidate`.

# Astral V42 Causal-Target Reliability Protocol

State slice: `astral-stage0c-qwen36-causal-target-reliability-v42`.

Status: executed as a fresh, separately authorized development slice on
2026-08-27. V42 is closed after a validated tune reliability failure. This
protocol does not reopen V28/V29 or reuse V25, V39, V40, or V41 scientific
artifacts.

## Purpose

V38 established only `LocalDevelopmentInstrumentFeasibilityOnly`: the cached
Qwen3.6 layer-capture and replacement seam could be exercised, but no causal
target-validity result followed. V39, V40, and V41 changed target-observer
representations and each stopped before a validated candidate. V42 isolates
the unresolved target question: does the directly measured layer-19 paired
replacement effect remain reliable under two fixed prompt wrappers and
independent captures on fresh external text?

The result ceiling is deliberately narrow. A passing V42 result would support
only a bounded local causal-target reliability result and would be an input to,
not a pass of, the existing Stage 0C gate. It would not establish
introspection, causal self-modeling, Stage 0C, Stage 1, benchmark evidence, or
production readiness.

## Frozen custody and identity

- Model: `Qwen3.6-35B-A3B-MLX-4bit`.
- Architecture: `Qwen3_5MoeForConditionalGeneration`.
- Runtime: Python environment with MLX `0.31.2` and MLX-LM `0.31.3`.
- Model execution: offline only, against the already cached checkpoint. No
  downloads, network calls, training, adapter updates, or weight updates.
- Target seam: final-position capture and replacement at layer `19` of a
  40-layer stack with hidden width `2048`.
- Replacement: the captured donor vector replaces only the final position;
  all other positions remain the recipient activation.
- Source, runtime, model, protocol, runner, and output digests are recorded.
- Corpus custody is external to the repository and contains only the fresh
  V42 Gutenberg text/RDF files, manifests, and independent validator receipt.
- V42 cannot consume V41 corpus, panel, feature, prediction, effect, or
  result files. The cached model bytes are re-bound through a new V42 custody
  manifest; this is custody revalidation, not reuse of V41 scientific output.

## Fresh data slice

The corpus has 18 single-work, English, public-domain Project Gutenberg
documents: six each for fit, tune, and assessment. The sealed IDs are
`23, 47, 106, 113, 175, 209, 289, 491, 690, 996, 1695, 1998, 61, 2009,
2048, 2440, 3021, 3543`, assigned in that order to fit, tune, and assessment
blocks. They are excluded from the complete V39–V41 ID inventory. Authors are
disjoint across splits. No collected-work or multi-work title is eligible.

The panel contains four deterministic families per document, for 24 families
per split and 72 total. Each family uses a source excerpt, one unique target
word, and an equal-length distractor not present in that excerpt. Concepts,
source n-grams, authors, documents, and split membership are sealed before
model effects. Both ordinary and counterfactual prompts are exactly 320
tokens.

## Direct target measurement

For each family and wrapper, the runner separately captures clean ordinary and
counterfactual final-position layer-19 activations and their two-token response
logits. It then measures reciprocal replacement in both directions:

1. replace the ordinary prompt's final activation with the clean
   counterfactual activation;
2. replace the counterfactual prompt's final activation with the clean ordinary
   activation;
3. compute the paired effect as half the sum of the ordinary and
   counterfactual response-margin changes.

Two fixed wrappers are used for every family. They are selected before any
effect and cannot be adaptively chosen or tuned. Each wrapper is captured and
measured twice. The repeatability check compares the aggregate effect vectors
from the two complete captures.

## Controls and retention

The direct paired activation replacement is the activation-only target. The
control panel is fixed before measurement:

- exact-copy/no-op replacement: the recipient's own captured activation;
- shuffled donor: deterministic cross-document donor;
- constant donor: split-level mean activation;
- matched donor: deterministic cross-document donor matched on source length
  with norm adjustment;
- text-only: the clean response-margin aggregate without activation replacement.

Raw prompts, excerpts, tokens, activations, logits, traces, per-family effects,
and predictions are not written to V42 result roots. Only aggregate split
statistics, gate booleans, custody digests, and review/lock metadata may be
retained. The external raw corpus remains custody material, not an effect
result.

## Gates and ordering

Qualification runs first and must pass native parity, deterministic repeat,
zero replacement, nonzero intervention reach to logits, layer count, hidden
width, exact model/runtime/source custody, and no-network/no-training/no-raw
retention checks. Any failed qualification gate stops V42.

Fit and tune are measured before assessment. The fixed tune reliability gates
are:

- minimum wrapper effect standard deviation: `0.05`;
- wrapper Pearson correlation: at least `0.25`;
- same-sign agreement: at least `0.70`;
- two-sided bootstrap 95% lower correlation bound: at least `0.10`;
- exact-copy mean absolute effect: at most `1e-5`;
- shuffled, constant, and matched mean absolute control effects: at most
  `0.25`;
- repeat maximum absolute effect difference: at most `1e-5`;
- matched donor integrity: zero same-document violations and norm error at
  most `0.02`.

The thresholds, wrapper identities, split assignment, donor rules, and output
schema are configuration, not fit-derived parameters. Configuration locking
occurs before any assessment effect. Assessment would require a separate
independent review receipt verifying custody, fresh data identity, controls,
prediction-lock state, privacy retention, claim ceiling, and validator
behavior. Since tune failed, no review packet was accepted and no assessment
effect was measured.

## Result classes and advancement

- `InstrumentFeasibility`: qualification only.
- `TargetReliabilityNoCandidate`: qualification passed but the fixed tune
  reliability gate failed or the target was degenerate.
- `BoundedTargetReliability`: tune and assessment reliability passed with
  review, retention, and independent validation.

V42's observed class is `TargetReliabilityNoCandidate`. This closes the
current layer-19 target-reliability slice. It does not authorize an adaptive
threshold change, a new wrapper, another V42 run, Stage 0C, Stage 1, accepted
Evidence Ledger mutation, benchmark evidence, V82 advancement, or sharing
evidence with the separate Neural Chameleon branch.

## External artifacts

- Corpus: `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v42-corpus-r1-2026-08-27`
- Qualification: `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v42-qualification-r1-2026-08-27`
- Invalid first panel attempt, quarantined after validator detection:
  `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v42-panel-r1-2026-08-27-invalid-registry-digest`
- Valid panel: `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v42-panel-r2-2026-08-27`
- Reliability: `/Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v42-reliability-r3-2026-08-27`

Implementation is additive under
`tools/astral-stage0c-qwen36-v42/`. Every mutation belongs to this named
state slice.

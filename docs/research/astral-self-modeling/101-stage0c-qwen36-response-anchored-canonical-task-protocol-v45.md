# Astral V45 Qwen3.6 response-anchored canonical-task protocol

State slice: `astral-stage0c-qwen36-response-anchored-causal-target-v45`.

Status: fresh protocol authorization recorded; final execution is reported in
`102-v45-execution-record-2026-08-28.md` as
`CanonicalTaskNoCandidate`.

## Why this is a new question

V44 established that the qualified Qwen3.6 replacement seam is measurable, but
its direct effects did not remain stable across broad wrapper paraphrases and
absolute final/penultimate positions. V45 does not relabel that result and does
not search V44's outcomes for a winning configuration. It tests a narrower
estimand:

> On fresh author- and document-disjoint text, can a fixed response-margin
> predictor, trained only from activation geometry at a predeclared content
> anchor, predict held-out direct replacement effects for one exact canonical
> answer task while the unchanged causal controls remain valid?

The response-anchored design is a measurement audit with a distinct scientific
rationale. The measured position is inside the passage at a fixed offset from
the tokenized passage/suffix boundary, rather than at wrapper-dependent prompt
endpoints. The one canonical task is selected for semantic minimality and exact
answer-token control before V45 effects; no alternative wrapper is tried after
seeing results.

This slice cannot guarantee a positive scientific result. A positive result is
available only if the frozen held-out prediction and control gates pass. A
qualification positive control, if implemented, is instrument evidence only.

## Authorized scope and exclusions

This authorization permits additive V45 protocol/implementation source and
hermetic tests under `tools/astral-stage0c-qwen36-v45/`, a repository-external
fresh Gutenberg corpus and output custody chain, re-custodied cached Qwen3.6
qualification, fit/tune prediction locking, an independent aggregate-only
validator, and V45 protocol/execution records plus navigation updates.

It does not reopen V28/V29, reinterpret V25, treat V30–V37 as scientific
evidence, consume V61 documentation, consume V82 artifacts, or reuse V39–V44
scientific corpus, panel, activations, effects, predictions, or result files.
The cached checkpoint may be re-custodied as an execution dependency only. No
network is permitted during model execution; no training, adapter update,
accepted Evidence Ledger mutation, benchmark claim, production traffic, or
Stage 0C/Stage 1 promotion is authorized.

## Frozen model, runtime, and measurement

The model is the already-cached `Qwen3.6-35B-A3B-MLX-4bit` directory with
architecture `Qwen3_5MoeForConditionalGeneration`, 40 layers, and hidden width
2048. The runtime is MLX `0.31.2` and MLX-LM `0.31.3`, with fresh model,
configuration, runtime, and Qwen implementation-source digests. Qualification
must pass before any panel effect is accepted.

The fixed candidate layers are `12`, `19`, and `26`. Each uses one
`content_anchor` position defined as eight token positions before the exact
tokenized passage/suffix boundary. The panel validator must prove that the
ordinary and counterfactual prompts have identical token lengths and identical
anchor indices. No final, penultimate, wrapper-dependent, or post hoc position
is eligible.

The canonical prompt contract is fixed before acquisition effects:

```text
Use the passage to choose which listed word occurs in it. Respond with only A or B.
Passage:
{passage}
Options:
A) {target}
B) {distractor}
Answer:
```

The response tokens are exactly one tokenizer token for ` A` and ` B`. Target
and distractor words must have equal tokenizer length. Each ordinary and
counterfactual prompt is exactly 320 tokens. The counterfactual changes only
the first occurrence of the target word to the distractor.

## Fresh corpus and custody

The corpus must contain 24 fresh English public-domain Project Gutenberg
single works: eight documents in each of fit, tune, and assessment, with
authors disjoint across splits and four globally distinct concept families per
document. Exact Gutenberg IDs are sealed in the V45 selection manifest before
panel construction. Acquisition rejects every ID and source digest present in
the V39–V44 freshness exclusion inventory, rejects collected/anthology/volume
works, and writes canonical text, RDF metadata, source URLs, rights/language
checks, byte counts, and source digests.

The corpus validator independently verifies the selection manifest, author and
document disjointness, source custody, family census, tokenizer lengths,
content-anchor indices, and absence of raw model-run fields. Network is allowed
only for this separate intake command.

Panel construction is also sealed: passages contain 20–75 words and at least
15 distinct words, candidates are ranked by the V45 canonical digest, at most
96 eligible paragraphs per document are considered, and at most 64 equal-token-
length distractor candidates are considered for each target. These limits bound
deterministic intake computation; they do not inspect model effects or alter the
canonical task, feature map, controls, or gates.

## Qualification-first gates

Qualification runs before fit/tune measurement and stops the slice on any
failure. It must independently verify:

- native versus wrapped logit parity;
- deterministic repeatability;
- exact no-op replacement and finite zero replacement;
- nonzero replacement reach to selected logits at all three layers;
- 40-layer/2048-width capture and replacement shapes;
- response-token one-token identity and ordinary/counterfactual anchor equality;
- model, runtime, configuration, and source digests; and
- offline execution, no training, and no raw-intermediate retention.

## Direct effects, predictor, and unchanged controls

For each family and candidate layer, the direct activation-only label is the
same reciprocal paired replacement effect used in V44:

`0.5 * ((margin_A(ordinary <- counterfactual) - margin_A(ordinary)) +`
`       (margin_B(counterfactual <- ordinary) - margin_B(counterfactual)))`.

The fixed activation feature is the signed 32-block mean of the ordinary-to-
counterfactual hidden-state difference at `content_anchor`; hidden width 2048
therefore yields 32 contiguous blocks of 64 coordinates, with alternating
predeclared block signs. No feature selection, whitening, wrapper baseline, or
assessment fitting is permitted. The only ridge candidates are alphas
`0.1`, `1.0`, `10.0`, and `100.0`.

The unchanged controls are `activation_only`, `text_only`, `exact_copy`,
`shuffled`, `constant`, and `matched`. Clean baselines and intervention chunks
use the fixed MLX batch size `16`. Exact-copy mean absolute effect must be at most
`1e-5`; shuffled, constant, and matched mean absolute bias must be at most
`0.25`; repeatability delta must be at most `1e-5`; and target effect standard
deviation must be at least `0.05`.

## Fit, tune, locking, and assessment

Fit trains each predeclared layer/alpha ridge predictor using fit-only
activation features and fit-only direct effects. Tune predictions are emitted
before tune effects are generated. The ordered selection rule is lowest layer
then lowest alpha among candidates passing all tune gates:

- prediction/effect correlation at least `0.25`;
- sign agreement at least `0.70`;
- bootstrap lower 95% correlation bound at least `0.10`;
- target effect standard deviation at least `0.05`; and
- every unchanged control and repeatability gate above.

If no candidate passes, classify V45 as
`CanonicalTaskNoCandidate` and keep assessment closed. If one passes, freeze
the predictor, selected layer/alpha, prediction digest, corpus/model digests,
control configuration, and assessment-closed state. An independent reviewer
must verify custody, fresh data identity, anchor semantics, feature map,
controls, prediction ordering, privacy retention, claim ceiling, and validator
behavior before assessment opens. The assessment predictor and per-family
predictions are locked before any assessment intervention effect is generated.

Assessment retains only aggregate prediction/effect summaries, control and
gate arithmetic, custody digests, and lock metadata. Raw prompts, tokens,
activations, logits, traces, per-family effects, and per-family predictions are
forbidden in the result root.

## Independent validation and claim ceiling

The validator independently recomputes corpus, panel, anchor, qualification,
source, lock, raw-field rejection, aggregate gate arithmetic, and ordered
selection. It must fail closed on missing receipts, mismatched digests,
assessment effects before prediction lock, or any raw retention.

Allowed classifications are:

- `InstrumentFeasibility` for qualification-only success;
- `CanonicalTaskNoCandidate` for a complete fit/tune execution with no passing
  locked predictor; and
- `BoundedCanonicalTaskTargetValidity` only after reviewed, locked, held-out
  assessment effects pass all fixed gates and independent validation.

The highest V45 ceiling is
`LocalDevelopmentV45CanonicalTaskBoundedTargetValidity`. Even that ceiling
would not establish introspection, causal self-modeling, consciousness,
benchmark superiority, production readiness, Stage 0C, or Stage 1. Stage 0C
requires a complete validated causal-target result through the existing gate;
Stage 1 remains blocked until Stage 0C passes. V82 remains a separate stopped
Neural Chameleon branch until the required Gemma/oracle/monitor artifact bundle
exists.

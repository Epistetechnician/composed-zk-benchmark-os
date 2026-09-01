# Astral V46 answer-aligned causal-target protocol

State slice: `astral-stage0c-qwen36-answer-aligned-causal-target-v46`.

Status: separately authorized and executed through fit/tune. The final
classification is `AnswerAlignedNoCandidate`; assessment is closed.

## Scientific rationale

V39 through V44 showed that the local Qwen3.6 replacement seam is usable, but
the tested activation geometries did not yield a stable held-out target. V45
then fixed the task and content anchor, but its signed contiguous-coordinate
block basis still failed the complete tune prediction gate. V46 tests one
materially different, preregistered hypothesis:

> Can a fixed response-readout projection of the local counterfactual-minus-
> ordinary hidden-state difference predict the directly measured held-out
> A/B response-margin replacement effect?

The A/B response-token readout is fixed by the cached model's quantized
language-model head and the one-token response identities. It is not fitted
from target effects, tune outcomes, or assessment outcomes. V45 and earlier
scientific corpus, panel, activation, effect, prediction, and result artifacts
are not V46 inputs; earlier results supply rationale only.

## Authorized boundary

V46 permits additive source and hermetic tests under
`tools/astral-stage0c-qwen36-v46/`, a new external Project Gutenberg custody
root, re-custodied cached Qwen3.6 qualification, a new panel, fit/tune
measurement, an aggregate-only result, and independent validation. The
already-qualified local capture/replacement execution kernel is reused only as
source-level implementation infrastructure; no V45 scientific artifact is
read or consumed.

The slice does not reopen V28/V29, reinterpret V25, treat V30-V37 as
scientific evidence, consume V61, consume V82, train or update a model, use
network access during model execution, adapt layers/wrappers/positions/
thresholds/controls after effects, mutate the accepted Evidence Ledger, make
benchmark or production claims, or promote Stage 0C or Stage 1. V82 remains a
separate stopped Neural Chameleon branch pending its Gemma/oracle/monitor
artifact bundle.

## Frozen actor and custody

The actor is the already-cached
`Qwen3.6-35B-A3B-MLX-4bit` directory at
`/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit`.
Its expected architecture is `Qwen3_5MoeForConditionalGeneration` with 40
layers and hidden width 2048. Runtime custody is Python 3.14.5, MLX 0.31.2,
MLX-LM 0.31.3, and the Qwen source digests recorded in the execution record.
The model directory is re-custodied by a fresh manifest for this slice.

The fixed layers are 12, 19, and 26. The fixed position is
`content_anchor`, defined as eight token positions before the tokenized
passage/suffix boundary. The canonical wrapper, 320-token prompt length,
equal-token target/distractor requirement, and response tokens ` A` and ` B`
are fixed before effects.

The new corpus contains 24 English public-domain single works from Project
Gutenberg, with eight documents per fit, tune, and assessment split. Authors
are disjoint across splits, each document supplies four globally distinct
families, and the selection is document-disjoint from the V39-V45 candidate
and reservation inventory. V46 selected IDs and custody are sealed in the
external manifest; the repository contains no corpus payload.

## Measurement and controls

For each family, the direct activation-only label is the reciprocal paired
replacement effect:

```text
0.5 * ((margin_A(ordinary <- counterfactual) - margin_A(ordinary)) +
       (margin_B(counterfactual <- ordinary) - margin_B(counterfactual)))
```

The V46 feature is one scalar per candidate layer:

```text
lm_head(counterfactual_hidden - ordinary_hidden)[A]
- lm_head(counterfactual_hidden - ordinary_hidden)[B]
```

The language-model head is the frozen model readout. No weights are learned,
no feature selection occurs, and no layer is selected from prior outcomes. The
only ridge candidates are alphas 0.1, 1.0, 10.0, and 100.0. The unchanged
controls are `activation_only`, `text_only`, `exact_copy`, `shuffled`,
`constant`, and `matched`, with batch size 16 and repeatability checks.

## Qualification, lock, and validation gates

Qualification runs before panel-effect measurement and must pass native parity,
deterministic repeatability, exact no-op replacement, finite zero replacement,
nonzero replacement reach to the selected logits at every candidate layer,
40-layer/2048-width capture and replacement shapes, response-token identity,
model/config/runtime/source custody, offline execution, no training, and no raw
intermediate retention.

Fit uses fit-only features and effects. Tune predictions are emitted and
digested before tune intervention effects are generated. A candidate must pass
all fixed reliability gates, prediction correlation at least 0.25, sign
agreement at least 0.70, and bootstrap lower 95% correlation at least 0.10.
The ordered selection rule is lowest numeric layer then lowest alpha. If no
candidate passes, the slice stops with `AnswerAlignedNoCandidate`; no review or
assessment is opened.

If a candidate had passed, an independent review would have verified model and
data custody, feature/readout identity, control definitions, prediction-lock
ordering, aggregate-only retention, claim ceiling, and validator behavior
before assessment. Assessment effects are forbidden without that review and a
sealed configuration lock.

The result root may retain only aggregate summaries, gate arithmetic, custody
digests, source digests, and lock metadata. Prompts, tokens, activations,
logits, traces, per-family effects, and per-family predictions are forbidden.

## Claim ceiling

Permitted V46 classifications are `InstrumentFeasibility`,
`AnswerAlignedNoCandidate`, and a bounded target-validity classification only
after reviewed locked assessment effects and independent validation. Even a
bounded V46 result would not establish introspection, causal self-modeling,
consciousness, benchmark superiority, production readiness, Stage 0C, or
Stage 1. Stage 0C requires a complete validated causal-target result through
the existing gate; Stage 1 remains blocked until Stage 0C passes.

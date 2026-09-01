# Astral V43 Qwen3.6 causal-target localization protocol

State slice: `astral-stage0c-qwen36-causal-target-localization-v43`.

Status: authorized and executed as a fresh, local, development-only successor
to V42. V43 does not reopen V28/V29, reuse V25, consume V39–V42 scientific
artifacts, share evidence with V61 or V82, or promote any result to Stage 0C,
Stage 1, benchmark evidence, introspection, causal self-modeling, or
production readiness.

## Boundary and falsifiable question

V42 showed a reachable layer-19 paired replacement effect but failed its fixed
two-wrapper reliability gate. V43 therefore tests a narrower localization
hypothesis rather than changing the target wrapper or adapting the estimator:

> On a fresh author- and document-disjoint corpus, the direct paired
> final-position replacement effect is reliable at at least one predeclared
> candidate layer, and the effect is not explained by no-op, shuffled,
> constant, norm-matched, or text-only controls.

The fixed candidate set is layers `12`, `19`, and `26`. The intervention
position is always the final input position before the response token. No
other layer, position, wrapper, threshold, or corpus member may be selected
after seeing tune or assessment effects.

The selection rule is sealed before execution: choose the lowest numeric
candidate layer passing every tune gate. If no candidate passes, classify the
slice as `TargetLocalizationNoCandidate` and do not open assessment.

## Custody and fresh identity

The model is the already-cached
`Qwen3.6-35B-A3B-MLX-4bit` checkpoint, architecture
`Qwen3_5MoeForConditionalGeneration`, re-custodied by a fresh model manifest.
The locked runtime is MLX `0.31.2`, MLX-LM `0.31.3`, with source digests for
the Qwen3.5 and Qwen3.5-MoE implementation modules. Model execution is
offline; network is permitted only during the separate Gutenberg intake.

The fresh corpus contains 18 English public-domain Gutenberg single works,
with six documents in each of fit, tune, and assessment. Authors are
disjoint across splits. The IDs are disjoint from all V39–V42 inventories:

| Split | Gutenberg IDs |
| --- | --- |
| fit | 2641, 3268, 2868, 19476, 22541, 67979 |
| tune | 601, 3011, 37106, 72, 17460, 3296 |
| assessment | 33823, 393, 19771, 15399, 560, 58820 |

The intake records canonical text, RDF metadata, source URLs, byte counts,
SHA-256 digests, rights/language checks, a complete freshness exclusion
inventory, and an independent corpus-validator receipt. The panel creates
four deterministic concept families per document, globally disjoint target
and distractor words, document-derived excerpts, and fixed 320-token prompts
under two new fixed wrappers. The panel is independently recomputed from the
external corpus and tokenizer and is sealed before model effects.

## Qualification-first gate

Qualification must pass before panel effects are accepted. It checks native
versus wrapped logit parity, deterministic repeated forward output, exact
no-op replacement parity, explicit zero-vector replacement reach and shape,
nonzero final-position replacement reach to logits for layers 12, 19, and 26,
40-layer and 2048-width capture/replacement shapes, exact model architecture,
model manifest, runtime, and source custody, plus no network during model
execution, no training, and no raw intermediate retention.

Any failed qualification gate stops V43 without scientific execution.

## Direct measurement and controls

For every fit and tune family, each wrapper and each candidate layer is
captured in memory. The direct activation-only effect is the preregistered
reciprocal replacement effect:

`0.5 * ((margin_A(ordinary <- counterfactual) - margin_A(ordinary)) +
        (margin_B(counterfactual <- ordinary) - margin_B(counterfactual)))`.

The controls are fixed:

- `activation_only`: reciprocal paired activation replacement at the candidate
  layer and final position;
- `text_only`: the clean ordinary/counterfactual text margin change with no
  activation replacement;
- `exact_copy`: replace with the receiving prompt's own captured vector;
- `shuffled`: replace with a deterministic donor from another document;
- `constant`: replace with the split mean ordinary/counterfactual vector;
- `matched`: use the shuffled donor after receiver-norm matching.

Only aggregate summaries are retained in the result root. Raw prompts,
tokens, activations, logits, traces, per-family effects, and predictions are
not permitted in the aggregate result or validator receipt.

## Fixed gates and review ordering

Each candidate layer must satisfy, on tune, both wrapper effect standard
deviations at least `0.05`, wrapper correlation at least `0.25`, wrapper sign
agreement at least `0.70`, bootstrap correlation lower 95% bound at least
`0.10`, exact-copy mean absolute effect at most `1e-5`, shuffled/constant/
matched mean absolute bias at most `0.25`, and repeatability delta at most
`1e-5`.

Fit and tune are measured first. The configuration lock binds the protocol,
candidate set, selection rule, panel, qualification, model, measured splits,
and assessment-closed state. An independently authored review must verify
custody, fresh data identity, controls, prediction-lock ordering, privacy
retention, claim ceiling, and validator behavior before any assessment effect
could open. V43's observed tune failure made that review/assessment branch
unnecessary and it remained closed.

## Result ceiling

Allowed classifications are `InstrumentFeasibility`,
`TargetLocalizationNoCandidate`, and `BoundedTargetValidityResult`. The last
classification is available only if a candidate passes tune and the
separately reviewed assessment is completed and independently validated.

The V43 no-candidate ceiling is
`LocalDevelopmentV43TargetLocalizationNoCandidate`. It is not a Stage 0C
pass. Stage 0C still requires a complete validated causal-target result, and
Stage 1 remains blocked until Stage 0C passes.

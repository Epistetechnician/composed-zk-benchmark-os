# Astral V44 Qwen3.6 causal-target measurement-invariance protocol

State slice: `astral-stage0c-qwen36-causal-target-measurement-invariance-v44`.

Status: authorized and executed as a fresh, separately sealed successor to
V43. V44 does not reopen V28/V29, reinterpret V25, treat V30–V37 as scientific
evidence, consume V61 documentation, consume V82 artifacts, or reuse V39–V43
scientific corpus, panel, activation, effect, prediction, or result artifacts.
The cached Qwen3.6 checkpoint may be re-custodied as an execution dependency;
its prior scientific outputs are not inputs.

## Boundary and falsifiable question

V43 tested final-position localization across three layers and failed the
fixed wrapper-invariance gates. V44 holds the direct paired replacement,
controls, thresholds, and review ordering unchanged while testing whether a
candidate is measurement-invariant across a fresh three-wrapper panel and two
predeclared input positions:

> On fresh author- and document-disjoint text, does at least one predeclared
> layer-position cell produce a non-degenerate direct activation effect that
> remains reliable across all three fixed wrappers while the unchanged controls
> remain within their fixed bounds?

The candidate cells are ordered and sealed as:

`12:final`, `12:penultimate`, `19:final`, `19:penultimate`, `26:final`,
`26:penultimate`.

`final` means the last input position before the response; `penultimate` means
the second-to-last input position before the response. The selection rule is
the first cell in that order passing every tune gate. No layer, position,
wrapper, threshold, split, or control may be selected after seeing effects.

## Fresh data identity and custody

V44 uses 18 fresh English public-domain Project Gutenberg single works, with
six documents per fit, tune, and assessment split; authors are disjoint across
splits and each document yields four globally distinct concept families. The
sealed Gutenberg IDs are:

| Split | Gutenberg IDs |
| --- | --- |
| fit | 2465, 2680, 31635, 452, 10148, 11982 |
| tune | 468, 26563, 16433, 70854, 36965, 451 |
| assessment | 20546, 46976, 20628, 14818, 48438, 57669 |

The intake records canonical text, RDF metadata, source URLs, language and
public-domain checks, byte counts, source digests, freshness exclusions, and
an independent corpus-validator receipt. The panel records fixed 320-token
ordinary/counterfactual prompts for these three wrappers:

- `wrapper_alpha`: `Read the passage and select the listed word found in it.`
- `wrapper_beta`: `Examine the passage and choose the option that occurs in the text.`
- `wrapper_gamma`: `Review the text and identify which offered word appears within it.`

The exact model custody is the external
`Qwen3.6-35B-A3B-MLX-4bit` directory with architecture
`Qwen3_5MoeForConditionalGeneration`, 40 layers, and hidden width 2048. The
locked runtime is MLX `0.31.2` and MLX-LM `0.31.3`, with Qwen implementation
source digests. Network is permitted only for the separate corpus-intake
command; model execution is offline.

## Qualification-first gate

Qualification runs before panel effects are accepted and checks native parity,
deterministic repeatability, exact no-op replacement, finite zero replacement,
nonzero intervention reach to selected logits for all six layer-position cells,
40-layer/2048-width shapes, exact architecture, model/config/runtime/source
digests, and the no-network/no-training/no-raw-retention controls. Any failed
gate stops V44 before fit, tune, or assessment measurement.

## Direct measurement and unchanged controls

For every fit and tune family, V44 captures the candidate layer vectors at both
fixed positions and measures the reciprocal paired replacement effect:

`0.5 * ((margin_A(ordinary <- counterfactual) - margin_A(ordinary)) +`
`       (margin_B(counterfactual <- ordinary) - margin_B(counterfactual)))`.

The unchanged control set is:

- `activation_only`: reciprocal paired activation replacement;
- `text_only`: clean ordinary/counterfactual text margin change;
- `exact_copy`: each receiving prompt receives its own captured vector;
- `shuffled`: a deterministic donor from another document;
- `constant`: split mean ordinary/counterfactual replacement vectors;
- `matched`: shuffled donor vectors norm-matched to the receiving vector.

The three wrappers are measured independently. Wrapper invariance is the
minimum pairwise correlation, sign agreement, and bootstrap lower 95% bound
over the three wrapper pairs. Tune gates are unchanged from V43: target effect
standard deviation at least `0.05`, pairwise wrapper correlation at least
`0.25`, pairwise sign agreement at least `0.70`, bootstrap lower bound at least
`0.10`, exact-copy mean absolute effect at most `1e-5`, shuffled/constant/
matched mean bias at most `0.25`, and repeat delta at most `1e-5`.

Clean baselines and intervention chunks use the same fixed MLX batch size.
This is part of the measurement contract because batch-size-sensitive numerical
drift would otherwise make the exact-copy control invalid.

## Locking, review, retention, and validation

Fit and tune are measured before any assessment effect. The configuration lock
binds the protocol and state slice, fresh panel, qualification result, model
manifest, wrappers, layers, positions, controls, selection order, measured
splits, and assessment-closed state. Prediction locking precedes any possible
assessment effect. V44 retains only aggregate summaries, custody digests,
gate arithmetic, and lock metadata; raw prompts, tokens, activations, logits,
traces, per-family effects, and predictions are forbidden in the result root.

Before assessment could open, an independent reviewer would verify custody,
fresh data identity, predeclared wrappers/layers/positions, unchanged controls,
prediction-lock ordering, privacy retention, claim ceiling, and validator
behavior. A tune candidate therefore yields `ReviewRequired` with assessment
still closed unless a separately authorized assessment command consumes a
valid review receipt. Independent validation recomputes corpus, panel, and
qualification receipts, checks the lock digest, rejects raw fields, recomputes
all aggregate gate arithmetic, and recomputes the ordered passing-target set.

## Result ceiling

V44 permits only these narrow classifications:

- `InstrumentFeasibility` for qualification-only success;
- `MeasurementInvarianceNoCandidate` when no tune cell passes;
- `BoundedTargetValidityResult` only after a separately reviewed, independently
  validated assessment effect result.

None establishes introspection, causal self-modeling, Stage 0C, Stage 1,
benchmark evidence, or production readiness. Stage 0C still requires a
complete validated causal-target result, and Stage 1 remains blocked until
Stage 0C passes. The Neural Chameleon V82 branch remains separate and stopped
at missing Gemma/oracle/monitor artifacts.

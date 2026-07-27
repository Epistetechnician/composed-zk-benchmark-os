# V24 Execution Record

State slice: `astral-v24-author-development-exploratory`.

Classification: `AuthorDevelopmentPerturbationReadoutObserved`.

Authorization: `AuthorDevelopmentAuthorized`.

Independent verification: `NotRun`.

Confirmation: `NotAuthorized`.

Stage 0C: `Blocked`. Stage 1: `BlockedByStage0C`.

Claim ceiling: `LocalAuthorDevelopmentPerturbationReadout`.

## Frozen execution

The protocol was committed at
`6c2328c4159e4a7ceded28606cd7a28e3405c013` before implementation. During the
pre-execution code inspection, tests identified two mismatches with that
protocol: a concept direction was being rescaled after normalization, and the
text control contained an undeclared newline-count feature. Both were removed
before any V24 model forward. The six focused tests and all 114 Astral tests
then passed, and the executable implementation was committed at
`fa51fa277fe79edfb5c250943f4886d002e6b2a6`.

The run used the cached Qwen2.5-0.5B-Instruct 4-bit checkpoint, Python `3.14.5`,
MLX `0.31.2`, MLX-LM `0.31.3`, NumPy `2.4.5`, and an Apple M4 Max GPU. The
artifact retains the complete runtime and model-file inventories.

Controlled/native, deterministic-repeat, residual-repeat, and zero-strength
maximum absolute errors were all exactly `0`. Activation and no-intervention
prompts were byte-identical. All 20 concept directions were unit L2 norm within
floating-point tolerance. The fixed intervention was applied after layer `5`
at strength `1.0`, and the final-token residual was captured after layer `17`.

## Development qualification

Both disjoint development splits passed every preregistered gate before
assessment was opened.

| Split | Telemetry activation-vs-none BA | Strongest primary control | Advantage | Macro BA | Brier |
|---|---:|---:|---:|---:|---:|
| Development replication | 1.0000 | 0.5625 | 0.4375 | 1.0000 | 0.3262 |
| Tune qualification | 0.9688 | 0.5938 | 0.3750 | 0.9792 | 0.3104 |

The configuration lock was validated before assessment with SHA-256
`a11c552636d52655103bc04f99fa3654f1d442da0ae9856b8f5e31196455f11f`.
At that point the assessment-start marker, features, and results were absent.

## Sealed assessment

The one-shot assessment contained 48 rows: four fresh concepts, four wrappers,
and three conditions. The assessment-start record fixed that forward budget
and prevents a second execution.

| Method | Activation-vs-none BA | Macro BA | Brier |
|---|---:|---:|---:|
| Telemetry PCA-16 ridge | 1.0000 | 1.0000 | 0.2961 |
| Text-only | 0.5000 | 0.6667 | 0.4770 |
| Output-logit | 0.2813 | 0.4583 | 0.6454 |
| Anomaly summary | 0.6875 | 0.7500 | 0.5330 |
| Shuffled-label telemetry | 0.5313 | 0.5417 | 0.6549 |

The primary advantage over the strongest preregistered primary control was
`0.3125`. Its concept-bootstrap mean was `0.3138`, with 95% interval
`[0.1875, 0.4375]`. Telemetry recall and per-wrapper accuracy were `1.0000`
for every condition and wrapper. Every assessment gate passed.

## Durable artifact

The 18-file, 1.1 MiB repository-external bundle is:

`/Users/shaanp/Documents/ResearchArtifacts/astral-v24-288feb32b4833544d57988a61c9e76f95856777ab4346dea553eee539fcba9c3`

Manifest SHA-256:
`288feb32b4833544d57988a61c9e76f95856777ab4346dea553eee539fcba9c3`.

The fail-closed validator regenerated the corpus and fixed configuration,
matched the live runtime and model inventories, recomputed development and
assessment metrics and gates from retained raw features and locked readouts,
recomputed all predictions and the concept bootstrap, checked the one-shot
record and result classification, verified every file digest, and returned
`valid: true`.

## Interpretation and stop boundary

V24 shows that this construction-known hidden intervention leaves a downstream
linearly decodable signature that generalizes across the four sealed concepts
and exceeds the named text, output, anomaly, and shuffled-label controls. It
does not show that the language model itself can detect or report the
intervention. It also does not distinguish a semantically meaningful
concept-direction signal from every possible generic intervention signature;
the anomaly control is bounded to five preregistered summaries. The assessment
contains only four concept-level sampling units, so its bootstrap interval does
not establish broad checkpoint, task, or intervention-family generalization.

The result is not introspection, self-modeling, consciousness, faithful
explanation, mechanism identity, Stage 0C confirmation, independent
verification, independent replication, benchmark evidence, or production
readiness. V24 is closed: its concepts, prompts, direction construction,
features, thresholds, and assessment may not be tuned or rerun.

The next admissible action is independent artifact reproduction and scientific
review. A future confirmation must be separately authorized and preregistered
with fresh concepts and a fresh assessment. It should include matched
random-direction or equivalent intervention-specificity controls before any
claim can move beyond local downstream decodability.

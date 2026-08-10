# V21 Execution Record

State slice: `astral-heterogeneous-natural-text-replication-v21`.

Execution: `NaturalTextResidualReplicationNoCandidate`. Confirmation:
`NotAuthorized`. Stage 1: `BlockedByStage0C`.

## Integrity and qualification

V21 deterministically extracted 600 globally distinct prose lines from 120
repository Markdown documents outside the Astral research tree. Fit, tune, and
assessment used 80/20/20 disjoint documents and 400/100/100 rows.

The cached Qwen target had exact repeat parity. After subtracting the frozen
fit-only wrapper-by-hint cell means, the residual target remained
non-degenerate:

- fit residual standard deviation: `0.6370`;
- tune residual standard deviation: `0.5973`;
- assessment residual standard deviation: `0.6124`;
- fit bin counts: `80 / 80 / 80 / 80 / 80`;
- tune occupied all five fit-frozen bins;
- every wrapper-by-hint fit cell contained 25 rows.

Six 160-update LoRA adapters and one 20-update Qwen smoke adapter trained
offline. The smoke run stayed below the 75% physical-memory stop rule. Reported
training peak memory remained approximately 1.9 GB for Qwen and 2.8 GB for
Llama.

The independent lock validator confirmed 100 assessment predictions while
assessment effects were absent. Prediction-lock SHA-256:
`9f970f1c4ff375b2d0346829407ddec4da226d14a5fb6459c03daf8cdee30405`.

The first assessment finalization attempt exposed a code-only seed-indexing
defect: a reused V20 ensemble helper requested V20 seed `2003` after all 100
V21 effects had been written. The repair preserved those once-generated
effects, replaced the helper with the preregistered V21 seed panel, and did not
rerun the target. Predictions remained the previously validated locked values.

The complete bundle independently validated with manifest SHA-256:
`9c7ee7be93c09e9d2dcd5390b0d56e66abf5d24628c4d92d5e108d0405347817`.

Repository-external bundle:
`/tmp/astral-lm-v21-20260727-run1`.

## Primary result

| Method | MSE | MAE | Pearson | Calibration slope |
|---|---:|---:|---:|---:|
| Trained Qwen ensemble | 0.37794 | 0.45341 | 0.02586 | 5.2785 |
| Trained Llama ensemble | 0.37666 | 0.45234 | -0.10089 | -6.0349 |
| Best Llama seed (`2101`) | 0.37588 | 0.45184 | 0.02717 | 3.5161 |
| Untrained Qwen | 0.41716 | 0.49468 | -0.02420 | -0.1098 |
| Zero residual | 0.37510 | 0.45060 | 0.00000 | 0.0000 |
| Fit-only hint mean | 0.37510 | 0.45060 | 0.18924 | approximately 0 |
| Fit-only source-length mean | 0.39034 | 0.46567 | -0.09238 | -0.7159 |

Qwen seed MSEs were `0.37562`, `0.37658`, and `0.39163`. None beat the
zero-residual control. The ensemble improved over untrained Qwen by `9.40%`,
which is below the preregistered 10% requirement. It was `0.34%` worse than the
Llama ensemble, `0.55%` worse than the best Llama seed, and `0.76%` worse than
zero residual. Paired-bootstrap lower bounds were not positive for those
comparisons.

The near-zero correlation and excessive calibration slope independently fail
the candidate gate. Removing the visible four-template shortcut did not reveal
a transferable same-model advantage.

## Disposition

V21 establishes that the residual target and sealed workflow are mechanically
viable on heterogeneous, document-disjoint natural text. It refutes the tested
claim that a text-only Qwen explainer predicts these Qwen residual effects
better than the preregistered cross-model and source-blind controls.

The exposed target, source corpus, wrappers, seeds, bins, centroids, adapters,
and thresholds are closed. More wrapper, bin, seed, or LoRA tuning is not an
admissible next step. Stage 0C remains blocked. Any future study must introduce
a materially different source of information or causal target and explain why
it can identify the proposed mechanism rather than repeat text-only effect
forecasting.

Claim ceiling: `LocalDevelopmentNaturalTextResidualReplication`. This is not
activation access, introspection, self-modeling, faithful explanation, Stage 0C
confirmation, Stage 1 authorization, benchmark evidence, or production
readiness.

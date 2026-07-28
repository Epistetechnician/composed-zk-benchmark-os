# V20 Execution Record

State slice: `astral-continuous-margin-replication-v20`.

Execution: `ContinuousMarginReplicationNoCandidate`. Confirmation:
`NotAuthorized`. Stage 1: `BlockedByStage0C`.

## Integrity and qualification

V20 froze 400 new ambiguous-language families with no V19 family reuse. The
cached Qwen target had exact repeat parity. Fit/tune continuous effects were
non-degenerate:

- fit effect standard deviation: `0.5774`;
- tune effect standard deviation: `0.5861`;
- fit bin counts: `58 / 59 / 63 / 56 / 64`;
- tune occupied all five fit-frozen bins.

The fit-only boundaries were `0.84375`, `1.171875`, `1.459375`, and `1.75`.
All boundaries and centroids were frozen before assessment processing.

Six 240-update LoRA adapters plus the Qwen smoke adapter trained offline.
Reported peak memory remained approximately 1.7 GB for Qwen and 2.5 GB for
Llama.

The independent lock validator confirmed that all 50 assessment predictions
existed while assessment effects were absent. Prediction-lock SHA-256:
`57d110721f03a49b3f88722b37f047f601056d0316b164c1324651bf43281f77`.

Each assessment ablation then executed once. The complete bundle independently
validated with manifest SHA-256:
`03772cab10160e875e579180951e4fef54f7bf4a10959e98bbf6aa4eb643b02a`.

Repository-external bundle:
`/tmp/astral-lm-v20-20260727-run1`.

## Primary result

Assessment effect standard deviation was `0.5945`.

| Method | MSE | MAE | Pearson | Calibration slope |
|---|---:|---:|---:|---:|
| Trained Qwen ensemble | 0.2589 | 0.4085 | 0.6054 | 2.0068 |
| Trained Llama ensemble | 0.2248 | 0.3788 | 0.6660 | 1.7283 |
| Best Llama seed (`2027`) | 0.2145 | — | — | — |
| Untrained Qwen | 0.8877 | 0.8059 | 0.5098 | 9.7019 |
| Fit mean | 0.3568 | 0.4989 | 0.0000 | 0.6469 |
| Hint-option mean | 0.3241 | 0.4686 | 0.3099 | 0.8406 |
| Template mean | 0.2131 | 0.3732 | 0.6373 | 1.0895 |

Qwen seed MSEs were `0.2680`, `0.2317`, and `0.3111`; every seed beat the fit
mean. Training therefore learned real predictive structure relative to the
untrained and coarse-mean controls.

The primary same-model comparison failed:

- Qwen was `15.19%` worse than the Llama ensemble;
- Qwen was `20.67%` worse than the best Llama seed;
- Qwen was `21.47%` worse than the template-mean control;
- paired-bootstrap MSE differences were negative for those comparisons;
- Qwen calibration slope `2.0068` exceeded the allowed upper bound `1.5`.

The fit-only template mean was the strongest tested method. The continuous
effect is substantially organized by the four visible prompt templates, so the
trained explainers did not provide incremental target-specific value beyond
that structure.

## Disposition

V20 validates continuous effect measurement and demonstrates supervised
improvement over untrained Qwen, but it does not replicate V18's same-model
advantage. V18 cannot rescue this failure. The exposed families, bins,
centroids, adapters, and thresholds are closed.

The next admissible step is not another hint-strength, bin-count, or LoRA
hyperparameter search. A materially different study must remove the visible
template shortcut, use substantially more heterogeneous natural inputs, and
separate target-specific preference prediction from template-conditioned
effect magnitude before any new same-model claim.

Claim ceiling: `LocalDevelopmentContinuousMarginEffectReplication`. This is not
introspection, self-modeling, faithful explanation, activation access, Stage 0C
confirmation, Stage 1 authorization, benchmark evidence, or production
readiness.

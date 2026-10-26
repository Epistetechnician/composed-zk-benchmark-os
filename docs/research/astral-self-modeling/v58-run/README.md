# V58 result (LocalDevelopmentUnreviewed, exploratory, post-hoc, not independent)
Per-neuron analysis on the locked V54 selection (k=32 reselection matched), Pythia-2.8b, node v51-full-r1, protocol doc 140. RC 0; spend USD 0.53 of the 2.50 cap (runner meter; wake minutes extra). Campaign total about USD 44 of 50.00. Node stopped.

## Pre-registered readings
- **H-concentration: TRUE.** Top-8 single-unit effects sum to 0.762 logits = 92.5% of the joint k=128 effect (0.824); top-4 = 75.1%. Joint ablation of the top 8 gives 0.736 (close to the sum of singles, so roughly additive). One unit alone, L18 #20414, gives 0.322 logits (39% of the joint effect).
- **H-direct-path: FALSE.** Spearman(single-unit effect, direct logit attribution) over the 128 selected units = 0.43 (< 0.5 frozen).
- **H-agreement-selective: FALSE as defined.** 5 of the top 8 units had positive DLA in both singular-correct and plural-correct items (need >= 6). All top-8 single effects exceed the maximum of 300 matched-random control single effects (0.010).
- Controls: 300 matched-random units, max single effect 0.010, max |DLA| 0.0008.

## Top units (single effect, layer, DLA in singular / plural items, mean activation singular / plural)
| unit | layer | effect | dla_sing | dla_plur | act_sing | act_plur |
|---|---|---|---|---|---|---|
| 20414 | 18 | 0.322 | -0.029 | 0.481 | 0.17 | 2.74 |
| 25229 | 26 | 0.141 | 0.018 | 0.172 | -0.09 | 0.98 |
| 24862 | 26 | 0.089 | 0.116 | 0.008 | 0.66 | -0.05 |
| 13691 | 18 | 0.067 | 0.119 | 0.019 | 0.40 | -0.07 |
| 2952 | 10 | 0.050 | -0.004 | 0.060 | 0.09 | 1.24 |
| 22664 | 26 | 0.041 | 0.073 | 0.006 | 0.93 | -0.09 |
| 28532 | 26 | 0.029 | 0.0005 | 0.008 | -0.05 | 0.54 |
| 14134 | 18 | 0.024 | 0.013 | -0.013 | 0.95 | 1.15 |

## Post-hoc descriptive observation (NOT a pre-registered result)
The units are number-selective: each is active mainly for one subject number (four fire for plural subjects, three for singular) and its direct write is positive in that same class, i.e. it pushes toward the correct verb form for the number it responds to; 7 of the top 8 show this, and unit 14134 does not. The pre-registered "positive in both classes" criterion was mis-specified for number-selective units (they are near zero in the other class), which is why H-agreement-selective is false as written. The direct path (Spearman 0.43) accounts for only part of single-unit effects, consistent with V56's finding that about 24% of the total effect is indirect.

## Limits
Correlational, linear direct-path approximation of DLA only, one model and split, post-hoc relative to V54, no circuit or general-mechanism claim. Safe wording: "a small set of MLP neurons (mostly layers 18 and 26) carries most of the agreement effect in this Pythia-2.8b run; individual units appear number-selective, each active for one subject number; the direct logit path explains only part of their causal effect."
Files: `results/out_v58.json`, `results/out_v58.json.jsonl`.

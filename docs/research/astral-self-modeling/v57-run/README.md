# V57 result (LocalDevelopmentUnreviewed, exploratory, post-hoc, not independent)
Robustness on the locked V54 selection (k=32 reselection matched), Pythia-2.8b, node v51-full-r1, protocol doc 139. RC 0; spend USD 0.80 of the 2.50 cap (runner meter; wake minutes extra). Campaign total about USD 43.1 of 50.00. Node stopped.

## A. Dose-response (assess split, 100 matched-random controls per k)
| k | effect (logits) | control max | per unit |
|---|---|---|---|
| 4 | 0.505 | 0.027 | 0.126 |
| 8 | 0.587 | 0.016 | 0.073 |
| 16 | 0.729 | 0.021 | 0.046 |
| 32 | 0.709 | 0.020 | 0.022 |
| 64 | 0.744 | 0.017 | 0.012 |
| 128 | 0.824 | 0.018 | 0.006 |

- Every k beats all 100 controls (p = 1/101 = 0.0099 floor).
- **Pre-registered "dose-response supported" = false**: strict monotonicity fails because k=16 (0.729) is slightly above k=32 (0.709), a 0.02-logit inversion at the level of the noise scale (~0.03). Not retuned.
- Descriptive reading: the effect is **saturating and concentrated**. Four units already carry about 0.5 logits (about 70% of the k=32 effect) and k=128 reaches only about 16% more than k=32. The finding is not a diffuse sum over many weak units.

## B. Mean ablation (k=32)
- Mean-ablation effect 0.723 vs zero-ablation 0.709 (1.02x); all 100 controls under mean ablation are <= 0.015 (p = 0.0099). **Supported** (>= 50% of zero ablation and above all controls). The effect is not an artifact of zeroing activations.

## Not done / limits
- Counterfactual swap and cross-task specificity (gender agreement) need new items; deferred. Still one model, one split, 100 controls (p floor 0.0099), post-hoc relative to V54. V54 remains the H1 verdict. No mechanism or general claim.
- Lead for the next design: a handful of units carry most of the effect, so per-neuron analysis of the top 4-8 units (output-weight alignment with verb-number directions, direct logit attribution) is now a tractable mechanism test.
- Files: `results/out_v57.json`, `results/out_v57.json.jsonl`.

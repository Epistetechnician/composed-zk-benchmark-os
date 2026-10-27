# Dossier: a null-calibrated, pre-registered neuron-claim pipeline (V50-V60)
Status: owner-attested exploratory research, ceiling `OwnerSelfAttestedLocalDevelopment` / `LocalDevelopmentUnreviewed`; not independently reviewed. Documentation only: no model run, spend, or ledger mutation in this document. Slice: v53-v56-review-packet-v1.

## Thesis
The durable contribution is the instrument, not one neuron map. Each claim is pre-registered, tested against matched-random controls and a noise gate, ledgered with hashes, and failures are kept. The Pythia-2.8b subject-verb agreement result is the demonstration.

## Method (what makes a claim count)
1. Protocol document committed before any code or run; thresholds frozen; no retuning after data.
2. Selection on fit data only; prediction lock; assessment on held-out, item-disjoint text.
3. Matched-random controls (layer- and magnitude-matched, 100-1000 draws; p floor 1/(n+1)) under the identical operation.
4. Noise gate (sign-flip), known-bad shuffles, positive and near-miss controls; many-item specificity control.
5. Allocation receipt and hard spend guard per run; offline model with hash-verified weights; raw traces outside the repo.
6. Hash-chained claim ledger; negative results recorded with the same weight as positives.

## Results (Pythia-2.8b, single split per test)
| Question | Result | Run |
|---|---|---|
| Necessary? | 96 selected units: 0.81/0.71 logit drop, p=0.001 vs 1000 controls, fresh books | V53/V54 |
| Concentrated? | ~8 units carry >90%; top unit alone 0.32 | V57/V58 |
| Zeroing artifact? | No: mean ablation 1.02x zero | V57 |
| Sufficient? | Class swap 1.31 logits (ctl max 0.07) | V59 |
| Sufficient, cleaner? | Last-position swap 1.05; donor patch 1.40 (ctl max 0.012) | V60 |
| Transfers to reflexives? | 0.061 logits, above controls, below 0.1 floor | V59 |
| Other model / circuit / dose-response? | Not supported (recorded negatives) | V55, V56, V57 |

## Honest limits
One model; single splits; 100-1000 controls; V57-V60 post-hoc relative to V54; donors are different sentences, not minimal pairs; AI-assisted label audits; owner-attested only. No circuit, general-mechanism, proof, Level2+, SOTA, benchmark, production, or independent claim.

## Reproduce
Protocols `131`-`141`, `200`; run records under `v5x-run/` and `v60-run/`; review packet `neuron-v53-v56-review-packet/` (manifest hashes, unsigned decision template). Hermetic tests live under `tools/astral-neuron-level-causal-lane-v*/tests/`.

## Next
Scale test with a scale-aware floor committed in advance (needs a ceiling above USD 50); minimal-pair donors; independent replication by an outside reader (only route above the current ceiling).

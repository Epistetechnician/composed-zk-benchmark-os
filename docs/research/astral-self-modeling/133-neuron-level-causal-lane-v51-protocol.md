# V51 protocol: item-fresh Pythia-2.8B re-test under a null-calibrated instrument gate

Slices: astral-neuron-level-causal-lane-v51-execution, instrument-validity-gate-v3. Ceiling: LocalDevelopmentUnreviewed. Written and committed before any V51 data or model run.

## Why this exists, and what it is not
V50 (results in `v50-run/results/`) closed both Pythia lanes as InstrumentNotValid. Diagnosis from the code and saved aggregates:
- The V50 known-bad control is a sign-flip readout. Under that control the estimator has a computable noise floor: with per-document ablation drops d_i over n documents, a random sign-flip mean has standard error s = sqrt(mean(d_i^2)/n). The V50 fixed bounds (max 0.05 logits, 10% of effect) did not account for s, so they can fail from sampling noise alone. On 2.8B the observed max was 0.063 against an effect of 0.563.
- On 1.4B the selected effect (0.189) was also below the frozen 0.5 minimum, so that lane would have failed regardless.
- The single-item "constant" control (effect 0.195 on 1.4B, 0.469 on 2.8B) is weak evidence either way; it is kept unchanged.

V51 is a new protocol identity. It is **not** a retune of V50 and does not reopen V50. The gate was redesigned after seeing V50 outcomes; that is disclosed here and travels with every V51 result. V51 results are exploratory.

## Design (frozen)
- Model: EleutherAI/pythia-2.8b at revision 2a259cdd96a4beb1cdf467512e3904197345f6a9, same file hashes as V50. Layers 10, 18, 26. k=32, 1000 matched-random draws, seed 71 for controls. Pythia-1.4B is not run (budget, and V50 min-effect failure).
- Corpus: the same 36 Gutenberg books (raw bytes already local; no new download), same document-disjoint splits, same extraction and balance rules, but **every item id used in the V50 corpus is excluded**, so V51 items are item-disjoint from V50. **Waiver, decided before any V51 data was built:** a first build attempt showed V50 consumed almost all attractor items (remaining attractor fraction 0.7% against the V50 minimum of 30%). V51 therefore waives the attractor-fraction minimum; the fraction is reported, and V51 is a near-natural-frequency regime that must not be pooled or compared as like-for-like with V50. The non-'The' fraction and document-leakage gates stay. Documents are shared with V50, so this is not independent text; it is a fresh-item re-test only.
- Label audit: 100 sampled items judged by Claude (AI-assisted, not independent). More than 5% error closes the run before any model effect.
- Gate v3 replaces only the known-bad rule. Let s = sqrt(mean(d_i^2)/n) over the assessment documents for the selected set, and kb_1..kb_20 the 20 sign-flip draws:
  - null consistency: max |kb_j| <= 4.0 * s, and |mean(kb)| <= 4.0 * s / sqrt(20);
  - signal over noise: selected effect >= 10.0 * s;
  - selected effect >= 0.5 logits (unchanged).
  Z_NULL=4.0 and Z_SIGNAL=10.0 are fixed before data. All other gate checks (positive control, near-miss, activation shape, two readouts) and all hypothesis rules are unchanged from V50.
- Spend: hard cap USD 5.50 for V51 (raised from a first-drafted 4.50 before any data, because the 2.8B run alone billed 3.67 in V50 and the added gate evaluations lengthen it) on one fresh GiveMeANode h100-1 node; allocation receipt before any paid action. Total across V49, V50 and V51 stays well inside the USD 30 ceiling.
- A failed gate, label audit, spend breach, or missing receipt closes V51 without retuning. No Level2+, accepted-evidence, proof, SOTA, general, or mechanism claim; `mechanism_wording_allowed` stays false unless the unchanged V50 path rules pass on a valid Candidate, and even then the ceiling is LocalDevelopmentUnreviewed.

# V60 protocol: cleaner sufficiency tests (last-position-only swap, counterfactual donor activation patching)

Slices: astral-neuron-level-causal-lane-v60-execution, instrument-validity-gate-v3, governed by neuron-control-lanes-unreviewed-execution-v1. Ceiling: LocalDevelopmentUnreviewed. Authorized by the owner in chat 2026-10-26 ("option 1"). Committed before any V60 code or model run. Exploratory, post-hoc relative to V54/V58/V59.

## Why
V59's headline (swapping 7 number-selective units to opposite-class means drops the verb margin by 1.31 logits vs control max 0.07) used constants written at ALL positions, a heavy out-of-distribution edit. V60 removes that caveat two ways, on the same locked units and the same 800 assess items.

## Units and items (fixed from V59)
swap_units = [20414, 25229, 2952, 28532, 24862, 13691, 22664] (plural-selective 4 + singular-selective 3). Run aborts unless a fresh k=32 reselection equals the locked V54 selection and V58 top units equal the frozen list. Items: V54 assess split (800).

## Task L: last-position-only class swap
Same as V59 Task A (opposite-class fit mean per unit) but written at the LAST position only; earlier positions untouched. Controls: 100 matched-random 7-unit sets (layer and magnitude matched), identical operation. Supported iff the singular-correct and plural-correct mean drops each exceed the control maxima and the combined mean drop >= 0.1 logits.

## Task P: counterfactual donor activation patching
For every assess item, a donor is drawn by a seeded permutation from items of the OPPOSITE correct-form class (donor = a different real sentence with the other number; not a minimal pair, disclosed). The donor prefix is run unpatched and the last-position activations of the units are captured; they replace the recipient's last-position activations. Metric: margin drop (baseline - patched), singular and plural reported separately and combined. Controls: the same donor pairing and operation on the 100 matched-random 7-unit sets. Supported iff both directional drops exceed the control maxima and the combined drop >= 0.1 logits.
Diagnostic (not a gate): the same patch from a SAME-class donor for the 7 units; should be near 0 and is reported.

## Decision rule (frozen)
"Headline hardened" iff L and P are both supported. If only one holds, report it as such; if neither, the V59 swap effect is attributed mainly to the all-position intervention. No threshold changes after data. V59's 1.31 is reported alongside for comparison only; no expectation on magnitude.

## Budget and rules
Hard cap USD 1.50 on node v51-full-r1 (new receipt), expected about USD 0.40. Campaign ceiling USD 50.00 (about 45 spent). One run, no new data or downloads, offline model. A selection mismatch, spend breach or missing receipt closes V60 without retuning. Claims: single model, single split, 100 controls (p floor 0.0099); no mechanism, circuit, general, proof, Level2+, independent, SOTA, benchmark or production claim.

## Addendum 1 (2026-10-27): local execution (V60-local), before any local model run
The cloud run (cmd-kq5i9, exit 0) completed but its output stayed on node v51-full-r1, which re-queued for about 53 h; the owner then said "take it out of queue and let's do it locally end to end" (chat 2026-10-27). The node was stopped (disk intact; billing stopped). Scope of V60-local, same frozen protocol and decision rule, no threshold changes: run on this Mac (Apple MPS or CPU) in an isolated venv under the session scratchpad; network only for (a) PyPI packages (torch, transformers, spaCy 3.8.16 and en_core_web_sm 3.8.0, numpy), (b) rebuilding the V54 corpus from the frozen gutenberg.org book list (35 books; must reproduce manifest digest 59c514f0c5a89a1cf046f94a64e4abbe1254158bf3e992f37fbcf5e754a33221, else abort), (c) EleutherAI/pythia-2.8b config.json and model.safetensors at revision 2a259cdd96a4beb1cdf467512e3904197345f6a9 (about 5.7 GB), verified against the packet SHA-256 values before use. Raw text and weights stay outside the repo. No spend. A digest mismatch, hash mismatch or selection mismatch closes V60-local without retuning. Numerics on MPS (dtype per backend) differ from the H100's bfloat16 run, so this is a separate execution and is labeled V60-local; the unretrieved cloud output, if later read, is a distinct record. Ceiling unchanged: LocalDevelopmentUnreviewed; same claim limits.

# V60 result (LocalDevelopmentUnreviewed, exploratory, post-hoc, not independent)
Cleaner sufficiency tests for the V59 headline: last-position-only class swap (Task L) and counterfactual donor activation patching (Task P), locked V54 selection, 7 swap units, Pythia-2.8b, 800 assess items, node v51-full-r1, protocol doc 200. Spend USD 0.51 of the 1.50 cap (runner meter). Campaign total about USD 45.5 of 50.00. Node stopped.

## Task L: last-position-only swap: SUPPORTED
Mean margin drop **1.045** logits (singular 1.051, plural 1.039). 100 matched-random 7-unit sets, same operation: mean 0.004, max 0.011 (singular 0.013, plural 0.012). p = 0.0099 (100-draw floor).

## Task P: counterfactual donor patching: SUPPORTED
Patching the 7 units' last-position activations from an opposite-class donor sentence: mean drop **1.398** (singular 1.530, plural 1.265). Controls: mean 0.004, max 0.012. Same-class-donor diagnostic: 0.105 (not a gate; small but nonzero, partly sentence-level differences between donors).

## Decision (frozen rule)
Headline hardened = true: both L and P supported. The V59 sufficiency effect survives removal of the all-positions caveat (1.31 -> 1.05 with a last-position-only write) and holds under real-activation donor patching.

## Limits
Donors are different real sentences, not minimal pairs; one model, one split, 100 controls (p floor 0.0099), post-hoc relative to V54. No circuit, general-mechanism, proof, Level2+, SOTA or independent claim.
Files: `results/out_v60.json`, `results/out_v60.json.jsonl`, `allocation-receipt.json`.

## V60-local (protocol doc 200, addendum 1): CLOSED, selection mismatch, no result
Checks that passed: Pythia-2.8b config and weights match the packet SHA-256 values (revision 2a259cdd); the rebuilt V54 corpus (35 books, 2400 items, counts 800/800/800) reproduces manifest digest 59c514f0...; spaCy 3.8.16 / en_core_web_sm 3.8.0. Tokenizer files (tokenizer.json, tokenizer_config.json, special_tokens_map.json from the same revision) are not hash-pinned in the packet; their SHA-256 values are recorded here only for provenance: c24618a1..., 70e38394..., 6f50ab5a....
Failure: on Apple MPS (torch 2.14.1, bfloat16) the fit-split reselection of 32 units differed from the locked V54 selection, so the frozen guard raised `V50Error: k=32 reselection differs from the locked V54 selection` before any swap or patch measurement. Per the protocol, a selection mismatch closes V60 without retuning; no dtype, device, tolerance or threshold change was tried. Zero spend.
Reading: the unit scores depend on numerics; the H100 and MPS bfloat16 runs rank near-ties differently. A local result for these units therefore needs either the cloud output or a new, separately authorized protocol (for example float32 reselection with its own locked set), which would be a different experiment.
`corpus54-rebuild-public.json` is the public record of the local corpus rebuild (IDs, sizes, hashes, manifest).


**Correction (2026-10-27):** the cloud run section previously written here said the output was unretrieved; that was wrong. The cloud result above was retrieved by a separate session (commit 16601b02), and my earlier README overwrote it by mistake. Restored. Local (MPS float32, held-out selection) results for the same tests are the separate V61-local run in `../v61-local-run/` (T0/L/P 1.36/1.09/1.45), which is consistent with the cloud V60 numbers (1.05 / 1.40).

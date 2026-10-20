# V49 campaign independent review packet (UNREVIEWED)

Manifest sha256: `accf60050bc7b1c9b45af0cf4a251620ebcf3fdaf7d598bbd9e973285b53fec1` (file `manifest.json`). Ceiling: LocalDevelopmentUnreviewed. This packet is evidence for a reviewer, not an acceptance.

## Reproduce the claim checks
1. Verify every `sha256` in the manifest against the repo blobs; check `first_commit` of each run script precedes its result file's commit (preregistration order).
2. Hermetic tests: `python3 tools/astral-neuron-level-causal-lane-v49/tests/test_v49.py` (8 tests, fake backend).
3. Re-derive verdicts from `*.json` results (fields `v49_run`, `gate`, `readouts`, `known_bad`).
4. Optional rerun: gman h100-1, pytorch-2.13-cuda12.9, pinned model revisions in the manifest, `HF_HUB_OFFLINE=1`; scripts are uploaded as-is.

## Questions the reviewer should answer
- Is selection (fit only) leak-free from assess documents/templates? Are corpus groups truly document-disjoint?
- Do matched controls actually match on layer and activation decile, and are 1000 draws adequate for the claimed p?
- Is the known-bad control a valid broken-instrument test given the residual 8-9%?
- Do disclosed post-hoc changes (lens criterion, known-bad rule) invalidate the gate passes?
- Is "causal share of agreement preference in small LMs" the most the data support?

## Caveats
- Independent ACCEPT waived by owner; no reviewer has seen this
- r1 selection sign defect found after reading result; r2 mistaken launch of unfixed code discarded unread
- Lens criterion changed after r3 (post hoc); known-bad rule changed after g1/c1 (preregistered for c1/b1/b2)
- r4 reuses r3's neurons (not independent)
- Single runs, no power/ICC analysis, p at 1000-draw floor
- Zero-ablation + first-order selection; no path/circuit analysis; residual label-independent effect (known-bad 8-9% of selected)
- One phenomenon (subject-verb number), small LMs, heuristic wikitext labels
- Lane D measured on this run's checkpoints, not closed-family artifacts (spec deviation)
- Lane C fine-tune loss is unbounded (margin ~125): degenerate update

## Decision
Fill `review-decision-template.json` (identity, independence, decision, findings, signature). Without a genuinely independent signed decision, nothing here is accepted evidence.

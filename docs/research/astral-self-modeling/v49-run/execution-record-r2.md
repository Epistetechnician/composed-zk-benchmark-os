# Astral V49 execution record r2 (LocalDevelopmentUnreviewed)

Slices: astral-neuron-level-causal-lane-v49-execution, neuron-control-lanes-unreviewed-execution-v1.
Fresh identity: seed 50 (r1 used seed 49 and is disclosed in execution-record-r1.md).

- Fix vs r1: fit score is now `max(0, +d margin/d mask)` (the margin drop under ablation); r1 selected units whose ablation raised the margin.
- Same node `astral-v49-neuron-r1` (h100-1), same model revision 720c0434..., offline. Node total across r1+r2: 30.53 min = $2.5648 of the USD 30 ceiling. Node stopped.
- Procedure incident: one mistaken launch ran the unfixed r1 code under seed 49 because a macOS `sed -i` edit silently failed; I killed it, its output was never read or retained, then relaunched with verified edits (file sizes 5993/654 B).
- Result (result-r2.json, sha256 36af8a3b...): `Candidate`. Ablating the 32 fit-selected neurons drops the agreement margin by 1.19 (tune) and 1.24 (assess) versus matched-random sets (gap 1.19 / 1.24, p = 0.000999 = the 1000-draw floor, Holm rejects both). Controls: text-only 0.0, shuffled-label -0.04, constant-prompt 0.0, none separate.

## Limits (read before citing)
- One model, one templated subject-verb-agreement task (6 templates x 18 fillers); documents are split by id but share templates, so "document-disjoint" is weak.
- Selection uses a first-order gradient attribution; ablation is zeroing at all positions of three layers (10/16/22).
- Matched on layer and activation-magnitude decile only; no tail-shape, both-sign, or two-lens check (Lane B was not applied to this run).
- Unreviewed (independent ACCEPT waived by owner), single run, no power/ICC analysis.

Claim ceiling `LocalDevelopmentUnreviewed`. Not accepted evidence, Level2+, proof, SOTA, benchmark, introspection, or production claim.

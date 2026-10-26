# Neuron-level V53-V59 independent review packet (UNREVIEWED)

`manifest.json` lists SHA-256, size and first/last commit for all code (V50-V56 runners and hermetic tests), the seven frozen protocols (docs 132-138), result JSON and incremental logs, corpus public records, label audits, receipts and the two owner-attested ledgers. Build it again with `python3 build_manifest.py` from the repo root (its digest changes only if a listed file changes). This packet is evidence for a reviewer, not an acceptance.

## Claim under review (and nothing more)
"In an exploratory Pythia-2.8b study, owner-attested, 96 units selected on fit data causally move subject-verb agreement margins far beyond 1000 matched-random draws, specific to agreement context; replicated on fresh text." Not claimed: mechanism (V56 H2' false), other models (V55 failed the frozen floor), proof, general, Level2+, SOTA, benchmark, production.

## Reproduce
1. Verify each manifest `sha256` against the repo blobs; confirm each protocol doc's commit precedes the commit of its result (preregistration order: 135 before V53 result, 136 before V54 corpus and run, 137 before V55, 138 before V56).
2. Hermetic tests, no GPU: run `python3 -m unittest` for each `tools/astral-neuron-level-causal-lane-v5*/tests/test_*.py` (all pass at build time: v50 11+10+12, v51 7, v52 2, v53 6, v54 2, v55 2, v56 3).
3. Re-derive verdicts from `results/out_v53.json`, `out_v54.json`, `out_v55.json`, `out_v56.json` (fields `status`, `gate`, `results`, `specificity`, `controls`, `path`/`h2_prime`) and spot-check the incremental `.jsonl` logs.
4. Corpus: `corpus-public.json` lists Gutenberg IDs, sizes, SHA-256; re-fetch and rebuild with `tools/astral-neuron-level-causal-lane-v54/build_corpus_v54.py` (spaCy 3.8.16 / en_core_web_sm 3.8.0; older murmurhash/preshed/cymem/numpy needed on the build host) and compare the manifest digest `59c514f0...`.
5. Optional rerun: GiveMeANode h100-1, pytorch-2.13-cuda12.9, pinned model revisions and file hashes (V50 packet), `HF_HUB_OFFLINE=1`.

## Questions for the reviewer
- Is fit-only selection leak-free from tune/assess documents? Are splits document-disjoint (and, for V54, book-disjoint from V50-V53)?
- Do matched-random controls match on layer and activation magnitude bin; is 1000 draws (p floor 0.001) adequate?
- Is the gate v3 (null-calibrated sign-flip noise, known-bad shuffles, absolute floor 0.5 logits) a valid broken-instrument test, given it was designed after V50-V52 results?
- Is the many-item constant control (bare "The" prefix with each item's verb pair) a valid specificity check?
- Does the attractor-fraction waiver (V51 onward) or AI-assisted label audit (1-2% error) matter?
- Is V56's absolute-effect path statistic sensible, and do mediators at the selected layers make the patching analysis self-referential?

## Caveats (all disclosed in the run records)
- Owner and operator are not independent; independent ACCEPT waived by the owner; no reviewer has seen this.
- Gate v3, the constant control, and H2' were redesigned after seeing earlier results (V50 gate, V52 constant control, V51-V54 H2); V54 is a pre-registered replication of V53 but not blind to the design.
- One model (V55 on 1.4B failed the frozen 0.5-logit floor); one phenomenon; one split per run; p at the 1000-draw floor.
- Label audits by an AI (Claude), not an independent human; Gutenberg IDs and years AI-recalled with title checks.
- Failed or inconclusive attempts exist (V50 old gate, V51 budget stops, V52 NoCandidate on a one-item control); see their run records.

## Decision
Complete `review-decision-template.json` (identity, independence, decision, findings, Ed25519 signature) only if you are independent of the operator. Without that, nothing here is accepted evidence.

## Update (V57-V59)
The manifest now also covers V57 (dose-response, mean ablation), V58 (per-neuron analysis) and V59 (class-swap sufficiency, reflexive transfer) with protocols 139-141 and the V59 reflexive-item record. Added claim under review: "swapping seven number-selective units to the other number's mean activation lowers the verb margin by 1.31 logits vs a matched-random maximum of 0.07 (post-hoc, single model)". Extra caveats: the swap writes class-mean constants at all positions; V59 addendum 1 (reflexive items from all books, minimum 40 per class) was made after counting items but before any effect.

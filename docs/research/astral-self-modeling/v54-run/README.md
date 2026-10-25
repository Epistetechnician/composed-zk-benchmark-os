# V54 run records (LocalDevelopmentUnreviewed, exploratory, not independent)
Corpus: 35 fresh Gutenberg books (disjoint from V50's 36), 2400 items (800/split, exact class balance), attractor fraction 47.0%, non-"The" 77.7%; spaCy 3.8.16 / en_core_web_sm 3.8.0 (murmurhash/preshed/cymem/numpy pinned down to run on this host). Dropped: 28333 title mismatch; 2554 and 1342 deliberate year rejects. Label audit: 200 items judged by Claude (AI-assisted), 1 error (0.5%), see `label-audit.json`. Text not stored; `corpus-public.json` has IDs, sizes, SHA-256 and the manifest digest 59c514f0c5a89a1cf046f94a64e4abbe1254158bf3e992f37fbcf5e754a33221.

# V54 result (LocalDevelopmentUnreviewed, exploratory, not independent)
Node v51-full-r1, code 6f714209, protocol doc 136. Run completed (RC 0); spend USD 3.93 of the 4.80 cap (runner meter; node wake/upload minutes extra). Campaign total now about USD 39.1 of the 40.00 ceiling, so there is no room for another run without a new owner decision. Node stopped.

- Status: **Candidate**; gate v3 InstrumentValid, no failures. Selected effect 0.709 logits, signal/noise 22.5, positive control 0.852, near-miss 0.014, both signs true.
- Matched-random contrast: tune effect 0.660 (p = 0.001), assess effect 0.709 (p = 0.001, 1000 draws); Holm rejects both.
- Specificity (n = 800 assessment items): constant-prefix ablation -0.0025 vs 0.709 on real items; paired gap 0.711, z = 33.9; passes. text_only 0.0 and shuffled 0.016 do not separate.
- Path analysis: h2 false ("too few valid control draws"); **no mechanism or circuit wording**.
- Pre-registered replication rule (doc 136): met. Replicates V53's verdict on 35 different books (item and text disjoint from V50-V53), with a somewhat smaller effect (0.71 vs 0.81).
- Caveats: still one model (Pythia-2.8b), same gate and control design chosen after seeing V50-V52 results, attractor waiver, AI-assisted label audit (1/200 error), no independent review, not retuned. Ceiling LocalDevelopmentUnreviewed; V54 closed.
- Safe wording: "in this exploratory single-model run on fresh text, the selected 96 units move subject-verb agreement margins far beyond matched-random units, specific to agreement context; replicates V53."
- Files: `results/out_v54.json`, `results/out_v54.json.jsonl`.

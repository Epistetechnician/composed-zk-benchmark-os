# V54 protocol: fresh-text replication of V53

Slices: astral-neuron-level-causal-lane-v54-execution, instrument-validity-gate-v3. Ceiling: LocalDevelopmentUnreviewed. Committed before any V54 data, download or model run.

## Why
V53 (doc 135) returned Candidate on Pythia-2.8b using item-disjoint but text-shared books (same 36 as V50-V52). V54 asks whether the same pre-registered procedure gives the same verdict on **different books**. Owner chose "replicate on fresh text" in chat on 2026-10-24.

## Frozen (identical to V53 unless listed)
Model pythia-2.8b with the V50-packet revision and file hashes; layers, k=32/layer, 1000 matched-random draws, seed 71; gate v3 (Z_NULL 4.0, Z_SIGNAL 10.0, min effect 0.5); many-item constant control and specificity rule (const < 0.5, gap >= 0.5, z >= 4.0); H1/H2 rules; attractor waiver as V51-V53 (fraction reported, not gated). No threshold or code change in the experiment path.

## Changes
- Corpus: fresh Project Gutenberg books from `tools/astral-neuron-level-causal-lane-v54/books_v54.py` (list frozen here; AI-recalled IDs, title checked against the Gutenberg header, mismatches dropped without replacement; declared year >= 1900 else dropped; books in V50's list excluded). Document-disjoint fit/tune/assess split with seed "v54-docs"; same extraction rules, per-doc cap 400, exact class balance. 200-item label audit (AI-assisted, <= 5% error else V54 closes unrun).
- Network (owner amendment in AGENTS.md): at most 55 candidate documents from gutenberg.org, <= 300 MB, plus isolated spaCy venv. No other hosts.
- Spend: hard cap USD 4.80 on the reused node v51-full-r1 under a new receipt; total campaign stays <= USD 40.00 (about 35.2 already spent per the V53 meter; node wake/upload minutes slightly extra, so the cap may leave under-spent margin). If the cap watchdog fires before a verdict, V54 closes inconclusive and the incremental log is the only record.
- Interpretation rule fixed now: V54 "replicates" only if status Candidate with gate InstrumentValid, matched-random p <= 0.01 on tune and assess, and specificity pass. Anything else is reported as a non-replication, not retuned.
- Closed after one run. No Level2+, proof, mechanism (path analysis is run only after a Candidate and H2 stays unclaimed unless it passes), general, independent, SOTA, benchmark or production claim.

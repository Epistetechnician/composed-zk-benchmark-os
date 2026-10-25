# V55 result (LocalDevelopmentUnreviewed, exploratory, not independent)
Pythia-1.4B (rev fedc38a1, weights verified against the V50 packet SHA-256), V54 corpus, node v51-full-r1, code aec896df, protocol doc 137. Run completed (RC 0); spend USD 2.50 of the 4.00 cap (runner meter; wake/download minutes extra). Campaign total about USD 41.6 of the 50.00 ceiling. Node stopped.

- Status: **InstrumentNotValid** (gate v3 failure: `min_effect`). Pre-registered replication rule not met; recorded as a non-replication on this model, not retuned.
- Selected effect 0.239 logits, below the frozen absolute floor of 0.5 logits. Signal/noise 11.9 (passes), positive control 0.406, near-miss -0.053, both signs true.
- Matched-random contrast still strong: tune 0.210 (p = 0.001), assess 0.239 (p = 0.001); Holm rejects both.
- Many-item constant control: -0.0009 vs 0.239 on real items; paired gap 0.240, z = 14.9. Specificity z is far above 4, but the frozen gap floor (>= 0.5) fails, so the control is counted as "separating" (that is why `controls.constant` reads 0.5/true).
- Path analysis not run (only after a valid Candidate). No mechanism wording.
- Reading (descriptive, not a new verdict): on the smaller model the selected units still move the agreement margin well beyond matched-random units and specifically for agreement context, but at a lower absolute size than the thresholds frozen from the 2.8b runs. Whether the floor is appropriate for a smaller model is a protocol question for a new, separately committed run; V55 is closed and the floor is not changed here.
- Files: `results/out_v55.json`, `results/out_v55.json.jsonl`.

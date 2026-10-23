# V52 result (LocalDevelopmentUnreviewed, exploratory, not independent)
Node v51-full-r1, code c6c7c355, protocol doc 134. Run completed (RC 0); spend USD 3.48 of the 10.00 cap (run only; node wake/upload minutes billed outside the runner's meter, so total V52 is slightly higher). Neuron-campaign total about USD 31.6 (<= 40 ceiling).

- Instrument gate v3: **InstrumentValid** (no failures). Selected effect 0.812 logits; flip scale 0.0339; signal/noise 24.0; sign-flip max |kb| 0.088 (<= 4s = 0.135); positive control 0.970; near-miss 0.043; both signs true.
- Matched-random contrast: tune effect 0.792 (gap 0.801), assess effect 0.812 (gap 0.817), both p = 0.001 (1000 draws); Holm rejects both.
- Controls: text_only 0.0 and shuffled -0.005 do not separate, but the single-item **constant control separates (0.605 >= 0.5)**. Per the unchanged H1 rule this makes the status **NoCandidate**. Path analysis was not run; mechanism wording not allowed.
- Reading: the selected 96 units causally move the subject-verb margin far beyond matched-random units on a now-valid instrument, but the pre-registered rule that a constant-item ablation must not also reach 0.5 failed, so no candidate is declared. The constant control was noted as weak in doc 133 and kept unchanged; it is not retuned here. Exploratory single run, one model, gate designed after V50.
- Files: `results/out_v52.json`, `results/out_v52.json.jsonl` (incremental log). V52 closed; no retuning.

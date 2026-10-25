# V56 result (LocalDevelopmentUnreviewed, exploratory, post-hoc, not independent)
H2' path analysis on the locked V54 selection (reselection matched exactly), Pythia-2.8b, node v51-full-r1, code c1a22e15, protocol doc 138. RC 0; spend USD 0.62 of the 3.00 cap (runner meter; wake minutes extra). Campaign total about USD 42.3 of 50.00. Node stopped.

- **H2' = false; mechanism wording not allowed.** Frozen rule needs both absolute tests to reject AND top-2 mediator share >= 0.5.
- All 1000 control draws now had defined statistics (the V51-V54 abort is fixed). Selected units: total effect 0.930 logits on the <=64 path docs; direct (last-position, through final norm to the unembedding) 0.706, so indirect = 0.224 (24% of total). Controls: indirect mean -0.0007, top-2 absolute mean 0.0011.
- Both matched-random tests reject: indirect p = 0.001, top-2 absolute p = 0.001 (Holm rejects both).
- Top-2 mediators by activation patching: `mlp_L18` and `mlp_L26`, share of the indirect effect **0.458 < 0.5**, so H2' fails the pre-registered share rule.
- Reading, descriptive only: most (about 76%) of the ablation effect acts directly on the output logits from the selected units' own last-position contributions; the smaller indirect part is concentrated in later MLPs but not enough to meet the frozen threshold. Note that mlp_L18 and mlp_L26 are the layers that contain the selected units, so mediator patching there is partly self-referential; this analysis does not identify a downstream circuit.
- Files: `results/out_v56.json`, `results/out_v56.json.jsonl`. V56 closed; no retuning.

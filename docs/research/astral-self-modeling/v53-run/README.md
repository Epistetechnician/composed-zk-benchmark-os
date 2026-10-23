# V53 result (LocalDevelopmentUnreviewed, exploratory, not independent)
Node v51-full-r1, code d60c23ee, protocol doc 135. Spend USD 3.54 (runner meter) of the 6.00 cap; campaign total about USD 35.2 of the 40.00 ceiling (node wake/upload minutes slightly extra).

- Status: **Candidate** (gate v3 InstrumentValid, no failures). Same numbers as V52 for everything but the constant control: selected effect 0.812 logits, 24x noise, matched-random p=0.001 on tune and assess, Holm rejects both.
- Many-item constant control (n=800 assessment docs): constant-prefix ablation effect **-0.003**, versus 0.812 on real items. Paired specific gap 0.815, z = 39.2; specificity passes. The V52 single-item 0.605 was a one-item artifact, not a generic verb bias.
- text_only 0.0 and shuffled -0.005 do not separate.
- Path analysis (H2) ran after the Candidate but returned "too few valid control draws": **H2 false, mechanism wording not allowed**. No circuit/mechanism claim.
- Caveats: one model (Pythia-2.8b), one split, same books as V50/V51/V52 (item-disjoint, not text-independent), attractor waiver (near-natural regime), gate and constant-control both redesigned after seeing earlier results, AI-assisted label audit, not independent. Ceiling LocalDevelopmentUnreviewed; closed, no retuning.
- Safe wording: "in this exploratory single-model run, the selected 96 units causally move subject-verb agreement margins far beyond matched-random units, and the effect is specific to the agreement context (not a generic verb bias)."

# Neuron-level subject-verb agreement: V53 + V54 summary
Ceiling: OwnerSelfAttestedLocalDevelopment (owner self-attested, NOT independent). Level1LocalReplay ledger entries exist for both runs (v53-run/accepted-ledger, v54-run/accepted-ledger).

## Finding
In Pythia-2.8b, ablating 96 units (32 per layer at three layers, chosen on fit data) lowers the correct-vs-wrong verb margin on held-out subject-verb agreement items.

| | V53 (same books as V50-V52) | V54 (35 fresh books) |
|---|---|---|
| selected effect (logits) | 0.812 | 0.709 |
| signal / noise | 24 | 22.5 |
| matched-random p (tune, assess) | 0.001, 0.001 | 0.001, 0.001 |
| bare-prefix control effect | -0.003 | -0.0025 |
| paired specific gap, z | 0.815, 39.2 | 0.711, 33.9 |
| instrument gate v3 | valid | valid |
| status | Candidate | Candidate |

The effect is far outside 1000 matched-random draws and disappears when the sentence is replaced by a bare prefix with the same verb pair, so it is tied to agreement in context rather than a generic verb preference. It reproduced on text from different books, with a somewhat smaller size.

## Safe wording
"In an exploratory single-model (Pythia-2.8b) study, owner-attested, the selected units causally move subject-verb agreement margins far beyond matched-random units, specific to agreement context; the result replicated on fresh text."

## Update: V55 on Pythia-1.4B (not a replication)
Same corpus and procedure, new model: gate `InstrumentNotValid` because the selected effect 0.239 logits is below the frozen 0.5 floor. The effect is still far from matched-random (p = 0.001) and specific (z = 14.9), but the pre-registered rule is not met, so the finding is currently **one model, Pythia-2.8b**. See v55-run/README.md. Spend about USD 41.6 of the 50.00 ceiling.

## Update: V56 path analysis (post-hoc, exploratory)
With ratio-free statistics (all 1000 control draws valid), the selected units' indirect effect (0.224 logits) and top-2 mediator effect both beat matched-random (p = 0.001), but the top-2 mediators (mlp_L18, mlp_L26, the layers holding the selected units) explain only 45.8% of the indirect part (< 0.5 frozen), and about 76% of the total effect is direct on the logits. H2' false: **no mechanism wording**. See v56-run/README.md. Spend about USD 42.3 of 50.00.

## Update: V57 robustness (post-hoc, exploratory)
On the locked V54 selection: mean ablation reproduces the effect (1.02x zero ablation, above all controls). Dose-response over k = 4..128 is saturating and concentrated (4 units: 0.505 logits, 32: 0.709, 128: 0.824; every k beats all controls), but the pre-registered strict-monotone rule failed on a 0.02-logit k=16 vs k=32 inversion, so "dose-response supported" is false as defined. See v57-run/README.md. Spend about USD 43.1 of 50.00.

## Update: V58 per-neuron analysis (post-hoc, exploratory)
Concentration is real: the top 8 of the 128 selected units carry 92.5% of the joint effect (one unit, L18 #20414, alone 0.32 logits), all beating 300 matched-random units. The pre-registered direct-path (Spearman 0.43 < 0.5) and "agreement-selective in both classes" (5/8 < 6) hypotheses were false as defined; post-hoc, 7 of the top 8 units look number-selective (active for one subject number, writing the matching verb form). See v58-run/README.md. Spend about USD 44 of 50.00.

## Update: V59 sufficiency and transfer (post-hoc, exploratory)
**Sufficiency supported:** swapping 7 number-selective units to the opposite number class's mean activation lowers the verb margin by 1.31 logits (singular 1.45, plural 1.16) vs a matched-random max of 0.072, so these units are a causal handle on verb number, not only a dependency. **Transfer not supported by the frozen floor:** ablating the 8 units lowers reflexive-pronoun agreement margin by 0.061 logits (above all 100 controls, max 0.020, but < 0.1 floor); the units are mostly verb-form-specific. See v59-run/README.md. Spend about USD 45 of 50.00.

## Not claimed
Mechanism or circuit (path analysis returned "too few valid control draws" in both runs, H2 false); other models or tasks; independence (owner and operator are not independent; the label audits, 1-2% error, were AI-assisted); proof, Level2+, SOTA, benchmark, production, introspection or self-modeling.

## Caveats
One model; gate v3 and the many-item control were designed after seeing V50-V52 results; attractor-fraction waiver (V51 onward); the V50-V52 history includes failed gate/control attempts that are disclosed in v50-run to v53-run; corpus built from AI-recalled Gutenberg IDs with title checks.

## Spend
About USD 39.1 of the former 40.00 ceiling at the end of V54; ceiling raised to 50.00 on 2026-10-25.

## Next (needs a new protocol and per-run cap)
A second model for scope; a redesigned path analysis for any mechanism wording; independent review for any higher ceiling.

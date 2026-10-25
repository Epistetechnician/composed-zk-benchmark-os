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

## Not claimed
Mechanism or circuit (path analysis returned "too few valid control draws" in both runs, H2 false); other models or tasks; independence (owner and operator are not independent; the label audits, 1-2% error, were AI-assisted); proof, Level2+, SOTA, benchmark, production, introspection or self-modeling.

## Caveats
One model; gate v3 and the many-item control were designed after seeing V50-V52 results; attractor-fraction waiver (V51 onward); the V50-V52 history includes failed gate/control attempts that are disclosed in v50-run to v53-run; corpus built from AI-recalled Gutenberg IDs with title checks.

## Spend
About USD 39.1 of the former 40.00 ceiling at the end of V54; ceiling raised to 50.00 on 2026-10-25.

## Next (needs a new protocol and per-run cap)
A second model for scope; a redesigned path analysis for any mechanism wording; independent review for any higher ceiling.

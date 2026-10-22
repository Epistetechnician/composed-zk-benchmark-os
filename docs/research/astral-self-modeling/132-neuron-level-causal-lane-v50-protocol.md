# Astral neuron-level causal lane V50: docs-first protocol

State slice: `astral-neuron-level-causal-lane-v50-protocol`
Claim ceiling: `Level0DesignNote`. Documentation only. No execution, spend, download, or node action is authorized by this file.

## Why V50 exists

V49 produced a Candidate verdict in every run but its instrument gate was inconsistent: the known-bad (shuffled-readout) control failed in g1, c1 and r2, r3 failed a lens rule, and r4 passed only after a post-hoc criterion change. The V49 records also show the broken readout still moves the result by 0.08 to 0.11 logits in the runs that passed. V49 used Qwen3 and SmolLM2 models, templated sentences, and "The ..." subjects from Wikipedia, so it cannot support a general or mechanism claim.

V50 is a fresh identity. It does not reuse V49 selections, neurons, corpora, thresholds as tuned, or results as inputs. V49 is not reopened.

## Hypothesis (preregistered)

H1. In a model family other than Qwen3 and SmolLM2, a small fit-selected set of raw MLP neurons carries a causal share of subject-verb number agreement preference on non-templated text, measured as a larger margin drop under ablation than matched-random neuron sets.

H2 (mechanism wording gate). The effect of the selected set is partly mediated through identifiable downstream components, beating the same decomposition for matched-random sets. Without H2, no mechanism wording is permitted, whatever H1 shows.

Failure of H1, or a failed instrument gate, closes V50 as `NoCandidate` or `InstrumentNotValid` without retuning.

## Fixed design (frozen before any model execution)

**Models.** Primary: `EleutherAI/pythia-1.4b`. Replication: `EleutherAI/pythia-2.8b`. Both are the GPT-NeoX family with non-gated GELU MLPs, which differs from the gated MLPs in Qwen3 and SmolLM2. Exact revisions, file hashes, and licenses are recorded at freeze and checked before use. Execution is offline from pre-materialized weights. If either model is unavailable or its license check fails, V50 stops; no substitution.

**Corpus.** Natural prose from Project Gutenberg, English, published 1900 or later, with a fixed document list recorded by ID and hash before labeling. Agreement items come from a dependency parser (spaCy, pinned version and model) over present and past forms of be, do, and have. Rules: subjects must not be limited to sentence-initial "The ..."; at least 30% of items must contain an intervening attractor noun of the opposite number; each item uses the same verb pair as its gold form. Class balance is exact per document group (singular and plural gold). Splits are document-disjoint into fit, tune, and assessment. A fixed random sample of 200 labels is hand-audited before any model run; if label error exceeds 5%, the corpus is rejected and V50 stops.

**Selection.** 32 MLP neurons across three fixed layers (relative depth 0.3, 0.55, 0.8), chosen on fit only by first-order attribution, then locked. Prediction lock (selected IDs, direction, minimum effect) is hashed before tune and assessment effects are computed.

**Matched-random control.** At least 1000 draws per selected set, matched on layer and activation-magnitude percentile. One-sided test, Holm correction across tune and assessment. Minimum effect 0.5 logits on the margin. Controls: text-only, shuffled-label, and constant, unchanged from V49.

**Instrument gate (replaces the V49 rule).** Preregistered, with no z-score arm:
1. Known-bad control: 20 independent shuffled-label readouts. The maximum observed effect must be at most 10% of the selected-set effect and at most 0.05 logits in absolute terms. Both bounds must hold.
2. Positive control: top-512 ablation exceeds the selected-set effect.
3. Near-miss: ranks 33 to 64 give a smaller effect than the selected set.
4. Both-sign inspection and raw activation-shape summary, recorded as descriptive aggregates only.
5. Two readouts (margin and log-probability) must agree in sign and significance.
The 10% and 0.05 bounds are fixed here. They may not be changed after any data is seen. Failing any item sets the run to `InstrumentNotValid`.

**Path analysis (H2).** For the selected set and each matched-random draw, compute: (a) direct effect, from the neuron outputs to the unembedding through the frozen final norm; (b) total effect under ablation; (c) indirect share, (b minus a) over b. Then activation-patch the selected neurons' outputs and record which downstream attention heads and MLP layers account for at least half of the indirect effect. H2 holds only if the selected set's indirect share and its identified mediator effect both exceed the matched-random distribution at the same Holm-corrected level. This is correlational patching on one phenomenon; it does not establish a circuit.

**Replication.** The full pipeline runs once on Pythia-1.4B (primary) and once on Pythia-2.8B, with independent selection. Results are reported per model with no pooling.

## Execution gate (not satisfied)

None of the following exists yet, so nothing runs:
1. A fresh execution authorization in `AGENTS.md` for state slice `astral-neuron-level-causal-lane-v50-execution`. The existing slices cover V49 and do not authorize V50.
2. A frozen, digest-bound packet: this protocol, the corpus document list and hashes, the label audit, model revisions and hashes, the code commit, and the lock schema.
3. Spend ceiling: at most USD 14.00 for V50. Total campaign spend to date is USD 13.041 of USD 30, which leaves USD 16.959; the V50 cap keeps a margin.
4. A fresh GiveMeANode node identity and allocation receipt recorded before any paid action. The parked V49 node is not reused unless its raw V49 traces are confirmed deleted and its identity is re-receipted.
5. Raw traces in a fresh owner-only `0700` custody root, deleted within 72 hours; aggregate-only retention.

## Claim ceiling

Default: `LocalDevelopmentUnreviewed`. Raising V50 to owner self-attested requires a separate owner attestation slice. Nothing here permits proof, general, Level2+, independent, SOTA, benchmark, production, mechanism-circuit, or introspection claims. A passing result supports only the scoped statement for the models, corpus, and phenomenon tested.

## Stop rules

Any of these closes the affected run without retuning: label audit failure, model or license check failure, missing receipt, spend above the cap, failed instrument gate, failed matched-random contrast, or any threshold change after data is seen.

## Prior expectation

Prior base rate for neuron-attribution lanes is mostly `NoCandidate`. A negative result under this stricter gate is an acceptable and informative outcome.

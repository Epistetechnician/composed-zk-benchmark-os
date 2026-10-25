# V55 protocol: model-scope replication on Pythia-1.4B

Slices: astral-neuron-level-causal-lane-v55-execution, instrument-validity-gate-v3. Ceiling: LocalDevelopmentUnreviewed. Committed before any V55 download or model run. Chosen by the assistant under the owner's "whatever is best" (chat 2026-10-25), after the owner raised the campaign ceiling to USD 50.00.

## Why
V53/V54 are one model (Pythia-2.8b). V55 asks whether the same pre-registered procedure gives the same verdict on a smaller model of the same family, selecting units afresh on that model's own fit data.

## Frozen (identical to V54)
Corpus: the exact V54 corpus (35 fresh books; manifest digest 59c514f0c5a89a1cf046f94a64e4abbe1254158bf3e992f37fbcf5e754a33221, no new text). Gate v3, k = 32 units per layer, 1000 matched-random draws, seed 71, many-item constant control and specificity rule (const < 0.5, gap >= 0.5, z >= 4.0), H1/H2 rules. Model: EleutherAI/pythia-1.4b at revision fedc38a16eea3bd36a96b906d78d11d2ce18ed79 with the V50-packet file hashes (config.json 6ea552aa..., model.safetensors ad438863...), layers [7, 13, 19]. No threshold or code change in the experiment path; the min-effect absolute rules are unchanged although a smaller model may have smaller effects (reported, not retuned).

## Changes
- Weights: download `config.json` and `model.safetensors` from huggingface.co (EleutherAI/pythia-1.4b, that revision, ~2.9 GB) onto node v51-full-r1, verified against the packet hashes before use; tokenizer files copied from the already-verified Pythia-2.8b directory (same GPT-NeoX tokenizer family). No other hosts.
- Spend: hard cap USD 4.00 (new receipt), total campaign <= USD 50.00 (about 39.1 spent). Expected ~USD 2-3.
- Replication rule: Candidate with gate InstrumentValid, matched-random p <= 0.01 on tune and assess, and specificity pass. Anything else is a non-replication on this model, not retuned. Closed after one run. No mechanism, general, independent, Level2+, proof, SOTA, benchmark or production claim.

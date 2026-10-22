# V50 results (LocalDevelopmentUnreviewed; AI-assisted labels; unreviewed)

Packet digest 43ae57ec...adec; node v50-full-r1 (allocation cdd08400-b8a7-492a-82ad-d8c4e27183db). Aggregate-only outputs; no raw traces written.
Total V50 billed: $8.40 (smoke $1.74 + full $6.66) of the USD 14 cap. Nodes stopped; disks parked (hold corpus text and weights).

| model | selected effect (assess) | matched-random gap | Holm | instrument gate |
|---|---|---|---|---|
| pythia-1.4b | 0.189 logits | 0.191 (p=0.001) | reject (both splits) | InstrumentNotValid: known_bad fail |
| pythia-2.8b | 0.563 logits | 0.567 (p=0.001) | reject (both splits) | InstrumentNotValid: known_bad fail |

Both runs fail the pre-frozen instrument gate (known-bad max 0.028 and 0.063 vs the rule max(10% of selected effect, 0.05 logits) failing under the frozen rule; constant-ablation control also did not separate). Per protocol the affected lanes close without retuning: no Candidate, path analysis not run, no mechanism wording. The matched-random contrast is significant but cannot be cited as a result while the instrument is invalid.
State slices: astral-neuron-level-causal-lane-v50-execution, instrument-validity-gate-v2.

# V38 Execution Record — Qwen3.6 Layer-Instrument Feasibility

State slice: `astral-qwen36-layer-instrument-feasibility-v38`.

Status: `Executed / LocalDevelopmentInstrumentFeasibilityOnly`.

Command:

```text
python3 tools/astral-qwen36-layer-instrument-feasibility-v38/probe_v38.py
```

## Result

- 40 layers observed;
- hidden width observed: 2048;
- baseline repeat maximum absolute logit delta: `0.0`;
- zero-intervention maximum absolute logit delta: `0.0`;
- nonzero layer-19 intervention maximum absolute logit delta: `0.53125`;
- layer-norm repeat maximum absolute delta: `0.0`;
- assessment opened: `false`;
- training: `false`;
- network access: `false`;
- raw trace retained: `false`.

The runner also emitted a model manifest digest, prompt digest, and MLX source
digests. The model manifest binds the four local weight shards and local
configuration files; the raw files remain outside the repository.

## Interpretation

This is a positive local instrument-feasibility result. The new actor is a
candidate for a separately authorized scientific protocol because the local
MLX path is deterministic on the tested input and supports a nonzero
layer-local replacement whose effect reaches logits.

It is not evidence that the layer signal predicts held-out intervention
effects, that the model reports the signal faithfully, or that any mechanism
has been recovered. The Astral claim ceiling and V25 status remain unchanged;
Stage 0C and Stage 1 remain blocked.

## Validation boundary

No assessment split, observer, causal target, prediction lock, Evidence Ledger
mutation, provider/API call, credential, PII, reasoning trace, or scientific
claim was introduced.

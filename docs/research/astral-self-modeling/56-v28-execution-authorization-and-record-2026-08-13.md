# V28 Execution Authorization and Record — 2026-08-13

State slice: `astral-opaque-causal-channel-separation-v28-execution`.

## Authorization boundary

This was one offline local execution of the separately identified V28
protocol. It used no network, provider API, V25 artifact, V26 artifact, V27
result data, raw reasoning trace, credential, PII, or production state.

The exact runner/aggregator/validator/preflight sources were compiled or run
from the checkout. The runner streamed derived trial summaries directly to the
aggregator through a pipe. The aggregate result is the only retained result.

## Exact custody

- actor:
  `/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.5-9B-GGUF/Qwen3.5-9B-Q4_K_M.gguf`;
- actor SHA-256:
  `cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`;
- runtime:
  `/opt/homebrew/Cellar/llama.cpp/10050/lib/libllama.0.0.10050.dylib`;
- runtime SHA-256:
  `25aa1419a298e05a6bbd340c5bccafffb836e15e1ac42460b31fcd4a089df2ff`;
- public header SHA-256:
  `2331631b6a3567311abc0402c55aa9a867ee99759f2550bdfa261ec3693a21f6`;
- runner source SHA-256:
  `64a5c3a0762ece508e9dc36ffdb5c15eef4ef8e10a8c80050681187d9a1f59d9`;
- aggregator source SHA-256:
  `96ea362077a152b4466466c247efe3958cce34db61f2c0aafadc66cc73a4095a`;
- validator source SHA-256:
  `caa38f05096a8c7365f007fe338678f8bd65efec0ea06f55092661a9fb46ac56`;
- preflight source SHA-256:
  `c7c17ca3faae7598a91d5bc186ea27f1181fb882a7cfbed297683efd32e6dd4c`;
- aggregate result root: `/tmp/astral-v28-public-abi-20260813`;
- aggregate result SHA-256 captured at execution:
  `006d01a02d4ed9b25b154fcfa5b1f7b3b51d5b221c61d7db6b278034d097aaf9`.

The aggregate JSON was written to the external transient result root during
execution. That `/tmp` root is not present in the current environment, so the
file is not currently re-openable from this checkout. The captured hash,
aggregate metrics, and validator output remain in this record.

## Validation

```text
python3 tools/astral-opaque-causal-channel-separation-v28/validator_v28.py /tmp/astral-v28-public-abi-20260813/result.json
{"errors": [], "valid": true}
```

The runner compiled with `clang -O2 -std=c11 -Wall -Wextra -Werror`. The three
V28 hermetic tests passed. The first execution attempt exposed only a JSON
serialization defect in the runner; it produced no accepted result. The
corrected runner was recompiled and the frozen execution was repeated before
the result below was accepted.

## Result

| Metric | Result |
|---|---:|
| Classification | `OpaqueCausalChannelOrderingSignalOnly` |
| Trials | 16 (`8/4/4` fit/tune/assessment) |
| Assessment target variance | `0.0023824371` |
| Rich relative assessment MSE | `30.9123` |
| Opaque relative assessment MSE | `30.4607` |
| Shuffled relative assessment MSE | `33.4430` |
| Channel-order gate | passed |
| Utility gate (`relative MSE < 1`) | failed |
| Prediction lock | passed |
| Network access | `false` |
| Raw intermediate retained | `false` |

## Interpretation

The rich and opaque channels were slightly better than the shuffled control in
this small local comparison, but neither channel predicted held-out effects
usefully relative to the assessment mean baseline. The result is therefore a
negative utility finding with a weak ordering signal, not a breakthrough in
causal-channel separation.

It does not establish that an opaque provider artifact preserves faithful
computation, that a decoder recovers reasoning, that final embeddings are
mechanistic telemetry, or that any report is causally faithful. It does not
advance V25, unblock V26, Stage 0C, or Stage 1, and it does not mutate the
Evidence Ledger.

# V29 Execution Record — 2026-08-13

State slice: `astral-calibrated-opaque-causal-channel-v29-execution`.

Disposition: `CalibratedOpaqueCausalChannelDiagnosticOnly`.

## Custody

- actor: `/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.5-9B-GGUF/Qwen3.5-9B-Q4_K_M.gguf`;
- actor SHA-256:
  `cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`;
- runtime SHA-256:
  `25aa1419a298e05a6bbd340c5bccafffb836e15e1ac42460b31fcd4a089df2ff`;
- header SHA-256:
  `2331631b6a3567311abc0402c55aa9a867ee99759f2550bdfa261ec3693a21f6`;
- runner SHA-256:
  `7197af3c051acae4acd3fd72de315a115f8856893f7c2a2a3cc06922f6874d84`;
- aggregator SHA-256:
  `03eb9265216bee2402afc42ad92eab86b1fb2e4eec18136f10e9142488fb714d`;
- validator SHA-256:
  `33c9919d7d3d7c83511c28778ab5c3dd5f4500fb0ef2ff62fc18fd7d00960e23`;
- preflight SHA-256:
  `6694da4f2ba1ff4e41fc0e4d4a2b97d2f7c59613508d13616c915c166741b2b4`;
- result root: `/tmp/astral-v29-calibrated-20260813`;
- result SHA-256 captured at execution:
  `3cc596fcebaf5a816b0a1c1922e9e7e27e3e79a8fffe7d602a215d26d0b70ee5`.

The aggregate JSON was written to the external transient result root during
execution. That `/tmp` root is not present in the current environment, so the
file is not currently re-openable from this checkout. The captured hash,
aggregate metrics, and validator output remain in this record.

No raw embeddings, logits, prompts, controls, model output, credentials, PII,
or runtime logs were retained.

## Validation

```text
clang -O2 -std=c11 -Wall -Wextra -Werror ... -o /tmp/astral-v29-runner
python3 -m unittest discover -s tools/astral-calibrated-opaque-causal-channel-v29/tests -p 'test_*.py' -v
Ran 3 tests ... OK
python3 tools/astral-calibrated-opaque-causal-channel-v29/validator_v29.py /tmp/astral-v29-calibrated-20260813/result.json
{"errors": [], "valid": true}
```

## Result

| Metric | Result |
|---|---:|
| Classification | `CalibratedOpaqueCausalChannelDiagnosticOnly` |
| Trials | 32 (`16/8/8` fit/tune/assessment) |
| Selected ridge | `1.0` for rich, opaque, and shuffled controls |
| Assessment target variance | `0.0136776702` |
| Rich relative assessment MSE | `5.9990` |
| Opaque relative assessment MSE | `5.0911` |
| Shuffled relative assessment MSE | `1.0046` |
| Utility gate | failed |
| Prediction lock | passed |
| Network access | `false` |
| Raw intermediate retained | `false` |

## Interpretation

The larger split and tune-only ridge selection reduced estimator instability,
but neither channel approached useful held-out prediction. The shuffled
control substantially outperformed both proposed channels. V29 therefore does
not support causal-channel separation, opaque-projection sufficiency, or
effect-prediction utility.

This result does not test provider artifacts or faithful reasoning recovery. It
does not alter V25, unblock V26, Stage 0C, or Stage 1, and it does not create
accepted benchmark or Evidence Ledger evidence. The V28/V29 local channel lane
is closed pending a materially different, independently authorized protocol.

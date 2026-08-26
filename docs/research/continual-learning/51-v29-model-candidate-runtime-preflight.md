# V29 model-candidate runtime preflight

Status: `ExecutedLocalDevelopmentModelAcquisitionEligibilityPreflight`.

State slice: `continual-learning-model-candidate-runtime-preflight-v29`.

## Result

The complete cached `Qwen3.6-35B-A3B-MLX-4bit` directory passed a fresh offline
MLX runtime seam and independent receipt validator on 2026-08-21. The exact
route-bound four-label readout executed successfully with:

- model manifest digest `1fe60be53b2d2046fd06df7257c82e0143e542bb6db531a59eb2a5ced71f9837`;
- runtime receipt digest `d1a69f53b5f3521b5c7450643107dd86d640d1be0e7ffc3fb256eaeddd13eec5`;
- runtime elapsed time `7820.058 ms`;
- candidate labels `A/B/C/D`;
- `network_access=false` and `training=false` in the validated receipt.

The validated external receipt is:

`/tmp/continual-learning-qwen36-runtime-v29-20260821-r1/receipt.json`.

## Learning boundary

A one-step LoRA smoke produced an adapter and an exact route-bound train
readout of `2/8`; this is a runtime/training seam smoke only. A first fresh
four-task `160`-step acquisition attempt reached the end of task 0, then the
host killed the parent with exit `137` while the parent held duplicate
Qwen3.6 model copies for readout. That partial root is quarantined at:

`/tmp/continual-learning-qwen36-acquisition-v29-20260821-r1`.

The corrected acquisition-only runner isolates every readout to one model
process and completed the fixed four-task run. The independent validator
accepted the sealed root:

`/tmp/continual-learning-qwen36-acquisition-v29-20260821-r2`.

The result digest is
`68a3afba1685cef20a4aba021bbb0e9457b0ecd12095e097e5eef328948d3e89`; the
manifest digest is
`264e57bfd33c5cc0539b5f7a7eeefb2325753f9ff57dc7192181cc7807c902cb`.

| Task | No-update train | Adapter train | Adapter held-out | Readout |
| --- | ---: | ---: | ---: | --- |
| T0 | 2/8 | 2/8 | 2/8 | constant A |
| T1 | 2/8 | 4/8 | 4/8 | B/D |
| T2 | 2/8 | 2/8 | 2/8 | constant C |
| T3 | 2/8 | 2/8 | 2/8 | constant D |

All four V28-derived eligibility gates are false: not every adapter beats its
own no-update baseline, T0 misses both the `6/8` train and held-out floors,
and T0 emits a constant label. Qwen3.6 is runtime-compatible but not
acquisition-eligible. No retention, interference, provider, production,
scientific-promotion, or breakthrough claim is authorized.

The implementation and independent validator are
`experiments/continual_learning/routed_adapter_bank_acquisition_v29.py` and
`experiments/continual_learning/validate_routed_adapter_bank_acquisition_v29.py`.

Repository verification after this slice is green: `pnpm --ignore-workspace
run lint` passed `lint:fast`, 109 focused continual-learning tests, contract
and provider suites, and the full workspace matrix (`675 passed`, `0 failed`,
`5 ignored`).

The runtime receipt subphase has ceiling
`LocalDevelopmentRuntimeExecution`; the completed acquisition subphase has
ceiling `LocalDevelopmentModelAcquisitionEligibilityPreflight`.

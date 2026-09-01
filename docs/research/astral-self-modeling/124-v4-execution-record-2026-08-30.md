# V4 trace-completeness execution record

State slice: `astral-trace-completeness-gemma3-end-to-end-v4`

Campaign: `v4-hypothesis-2-affine-pooled-20260830`

## Disposition

`QUALIFIED_PREASSESSMENT_OPEN`

Qualification SHA-256:
`9c90364b29e6992539323acea147ba0e9bd746578f40b69f0d9f3f1438493eab`

This is a measurable qualification breakthrough under the fixed V4 ceiling:
the model-matched L0-big affine transcoder passed the preregistered pooled
reconstruction gate. It is not an assessment, causal graph validation, or
independent signed `ACCEPT`.

## Measured result

| Metric | Result | Gate |
|---|---:|---:|
| Pooled global-centered NMSE | `0.04572051752036069` | `<= 0.05` |
| Feature repeat cosine | `0.9999997019767761` | `>= 0.90` |
| Native/instrumented max logit delta | `0.0` | `<= 1e-4` |
| Deterministic repeat max logit delta | `0.0` | `<= 1e-5` |
| No-op max logit delta | `0.0` | `<= 1e-5` |
| Zero-replacement max logit delta | `4.140625` | `> 1e-5` |
| Fit rows | `17` | all captured rows used |
| Fit coordinates | `231552` | finite/nonempty |

All seven qualification gates passed: native parity, deterministic repeat,
no-op identity, nonzero intervention reach, event replay, pooled
reconstruction, and feature stability. Native and repeat sampled-token matches
were true. The event stream census was exact for every run, including module,
attention, cache/state, intervention, SAE, output-distribution, sampled-token,
and behavioral-link event classes.

## Custody and independent replay

Asset QC passed with digest
`a19f47ff2d36db1591476ae1c8b3a645b282b781df2e4303fc097cf413510abb`.
The pre-load review passed with digest
`e57bc1cd62f23ac66d31442a35cb464f59a72d632324ca7fb5845f3039cddf99`.
Independent reconciliation passed with digest
`a505a0ea86f8f0ae982bd9d0c307e254ea31fdd776751a910a430cb4166c01ee`.
The raw deletion completion receipt has digest
`a01b98dff4787c1c706f3a44751fd1a4608a3ae752bde58aba62847bdce13a4d`, deleted
35 files, and records `raw_root_empty: true`.

The external custody root retains aggregate manifests and digests only. The
model remained offline during execution. The fresh corpus used 16 fit families
from the 48-family V4 corpus; tune and assessment families were not executed.

## Claim ceiling and next boundary

The only permitted claim is
`LocalDevelopmentGemma3EndToEndCausalTraceQualificationV4`: under the exact
cached model, runtime, source, L0-big asset, fresh fit corpus, and external
custody chain, the complete typed trace qualification and fixed transcoder
reconstruction gate passed.

No assessment artifact exists. No independent packet-bound signed `ACCEPT` was
obtained. V4 therefore does not claim held-out causal-effect prediction,
causal scrubbing, mechanistic completeness, introspection, causal
self-modeling, Stage 0C, Stage 1, benchmark evidence, or production readiness.

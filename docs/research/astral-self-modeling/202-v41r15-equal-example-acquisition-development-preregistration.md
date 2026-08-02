# V41R15 Equal-Example Acquisition Development Preregistration

State slice: `V41R15AcquisitionFailureDiagnosisAndAlternativeDesign`.

Status: `DiagnosisComplete / IndependentValidatorImplemented / GPUExecutionUnauthorized`.

The content-bound V41R15 diagnosis of V41R14 reports that the declared 3:1
example policy became a 63.7534% bridge, 25.1825% terminal, and 11.0641%
protected loss allocation under token weighting. Every pre-clip gradient norm
exceeded 1.0. Loss declined while acquisition remained 0.3229167, protection
fell from 1.0 to 0.75, and the model never selected one balanced label.

The diagnosis report file SHA-256 is
`86dbbcc3ce5279c50f612684171967cb9094364cc6d51ef09bce8f7d788179f8`; its
semantic diagnosis SHA-256 is
`sha256:e23d2b7970abee69c254980ed06b14592e808f05edeaffd18d7f16497431236d`.

V41R15 changes exactly one scientific variable: each of the four microbatch
losses receives weight 0.25, yielding intended example shares of 37.5% bridge,
37.5% terminal, and 25% protected. All model, adapter, optimizer, schedule,
data, reload, evaluator, and gate fields remain unchanged from V41R14.

The independent validator reconstructs this contract, rejects any receipt
whose weights are not exactly `[0.25, 0.25, 0.25, 0.25]`, and preserves every
V41R14 identity, likelihood, census, reload, manifest, and sealed-boundary
check.

This is post-outcome development on a reused instrument. Even a passing future
run could reach only
`RemoteH100EqualExampleAcquisitionDevelopmentV41R15` and would require a fresh
instrument for confirmation. GPU execution, tuning, assessment, threshold
changes, broader method changes, continual-learning claims, and
self-improvement claims remain unauthorized.

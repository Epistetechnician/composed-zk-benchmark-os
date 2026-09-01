# TimesFM3 Sidecar V1 Claim Boundary

State slice: `timesfm3-temporal-stress-scenarios-v1`.

The maximum claim is
`LocalDevelopmentTimesFM3TemporalStressScenarioQualificationV1`.

Allowed claims are limited to the existence and validation of a bounded local
sidecar contract, deterministic fake-model fixtures, digest-bound q10/q50/q90
scenario construction, and—only after its separate gates pass—local model
qualification on the named TimesFM3 identity.

Every scenario is labeled `model_derived_synthetic_input`. It is not an
observed trace, telemetry observation, benchmark result, or backend outcome.

The sidecar must not:

- generate or alter Semantic IR;
- choose Oracle expected verdicts;
- choose mutations adaptively after prediction locking;
- replace the semantic Oracle;
- populate `BackendOutcome::Accepted` or `BackendOutcome::Rejected`;
- populate ZK backend performance score axes;
- produce proof, soundness, formal, recursion, ZKML, or official benchmark
  evidence;
- mutate the accepted Evidence Ledger automatically;
- control provider authority, spend, production traffic, or assessment
  scheduling;
- couple into Astral or continual-learning mechanisms;
- turn model-derived scenarios into observed benchmark data;
- claim forecasting quality.

Forecast output may produce an advisory deterministic local shard, batch, or
bounded-resource plan. It grants no authority and cannot change hard budgets.
Raw telemetry and full per-series forecasts remain outside the repository when
large or sensitive. Repository artifacts are bounded fixtures, manifests,
digests, and aggregate reports unless a later reviewed retention decision
authorizes more.

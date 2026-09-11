# Gemma3 paper-recirculation internal multi-instance V1

State slice: `continual-learning-gemma3-paper-recirculation-internal-multimachine-v1`.

This is a new internal reproducibility lane. It does not reopen or alter the
paper-aligned V1 lane, the FineWeb-Edu V31 lane, or any rejected H100 lane.
It removes the external-review prerequisite only for an explicitly lower
claim ceiling: `LocalDevelopmentGemma3InternalMultiInstanceReplication`.
The result is not independent scientific validation, a paper replication, a
benchmark result, or production evidence.

## Fixed experiment

- Execution is offline. No download, training, adapter update, provider call,
  or Evidence Ledger mutation is allowed.
- The operator supplies an external corpus root containing exactly fit and
  assessment windows. Each selected window must re-tokenize to exactly 1024
  tokens. The source identity, corpus manifest, model manifest, runner digest,
  and validator digest are retained in every receipt.
- Fit uses only the fixed candidates `(7,2)`, `(9,3)`, `(11,4)`, and `(12,5)`.
  Candidate selection minimizes fit mean token NLL with candidate-order
  tie-breaking. The reported `(11,4)` pair is an expected target, never a
  forced selection.
- Assessment uses the selected pair with `alpha=0.15` and `beta=0.85`, with
  source-to-destination L2 norm matching. The primary endpoint is per-window
  token-NLL delta, recirculated minus native baseline.
- Controls are zero-alpha identity, deterministic repeated assessment,
  temperature-1.20 baseline, and candidate-completeness accounting.
- The aggregate decision is `InternalReplicatedEffect` only when every
  instance completes, all instances select the same pair, all fixed controls
  pass, the mean delta is strictly negative, and the one-sided 95% bootstrap
  upper bound is strictly negative. Otherwise it is `NoCandidate`.

## Instance rule

An instance records the actual host identity, process identity, runtime, and
code digests. Same-host processes are allowed as an engineering fallback, but
their aggregate disposition is `SingleMachineMultiInstanceOnly`; they cannot
be described as multi-machine evidence. A multi-machine disposition requires
at least three instances and at least two distinct host identities.

The runner also exposes a four-window `engineering-smoke` mode for measuring
plumbing and runtime. Smoke receipts are not replication receipts and the
validator refuses to aggregate them.

## Stop and retention rules

Any digest drift, missing window, control failure, non-finite metric, model
mutation, or instance disagreement stops aggregation as `NoCandidate`. Each
run writes only to a new external staging/output root. Raw per-window rows may
remain only in that external root for 72 hours after validation and must then
be deleted. No result from this lane may be copied into an earlier protocol or
claim ledger.

# V41R29 Local Substrate-Capability Boundary Preregistration

State slice: `V41R29LocalSubstrateCapabilityBoundary`.

Status: `DocsFirstPreregistered / ImplementationUnauthorized / ExecutionUnauthorized`.

## Question

V41R28 established that the local MLX surrogate faithfully reproduces V41R27
per-cell acquisition+retention dynamics (all four mirrored cells pass on
qwen2.5-0.5b). The next question is whether a **full, sentinel-gated, 48-worker
qualification campaign** can run on any local substrate. This study measures the
exact substrate property that gates that possibility.

The frozen V41R27 preflight requires, before any update, that the base model
already answers every protected row correctly (protected accuracy exactly 1.0
across all 256 protected rows) and shows acquisition novelty (at least 3 of 4
acquisition cases incorrect per panel). Only knowledge the base model already
has can be "retained," so the protected-arithmetic requirement is a genuine
substrate-capability gate, not an arbitrary threshold. A substrate that fails it
cannot host a V41R27-style qualification campaign at all.

## Frozen bindings

- V41R27 contract SHA-256:
  `sha256:ddf7f95ea4bf9b109dbdb1b02b87542a2a8ea56fd694f508c0b8647bc716ed4e`;
- acquisition instrument SHA-256:
  `sha256:0459d3c39e37c1a3fb7a8ffdbee1dca214b75b316dab456ab3e8d82dd98d1f92`;
- protected instrument SHA-256:
  `sha256:83e873627f55df68f62a90d9847a73e5838eccc76fe48fb3c77109b6122b503e`;
- preflight requirements (from the V41R27 contract): protected accuracy
  exactly 1.0 across all 256 rows; minimum 3 incorrect acquisition cases per
  panel across all 16 panels.

## Substrate panel (identities pinned)

| Substrate | model.safetensors SHA-256 | tokenizer.json SHA-256 |
| --- | --- | --- |
| qwen2.5-0.5b (4bit MLX) | `ddffab9cbc7bf6dde941c6724841eeca8981fcfa81ca20ff8efff1396326d153` | `a8506e7111b80c6d8635951a02eab0f4e1a8e4e5772da83846579e97b16f61bf` |
| llama-3.2-1b (4bit MLX) | `35e396644bca888eec399f9c0f843ec7fa78b8f8c5e06841661be62b4edf96dd` | `6b9e4e7fb171f92fd137b777cc2714bf87d11576700a1dcd7a399e7bbe39537b` |
| nemotron-3-nano-4b (MLX) | config `9df35babecfbe4267ad2714b03c238613c21963704c04577dee1d581b225076f`, tokenizer `623c34567aebb18582765289fbe23d901c62704d6518d71866e0e58db892b5b7` (2-shard weights) | — |

## Measurement protocol (scoring-only; no parameter updates)

For each transformer-architecture substrate:

1. Score all 256 protected rows with the base model. Record overall protected
   accuracy and the per-panel accuracy for all 16 panels (16 rows each).
2. Score all 64 acquisition cases with the base model. Record overall baseline
   accuracy and the per-panel incorrect-before count for all 16 panels (4 cases
   each).

For the nemotron-3-nano-4b substrate: determine architectural compatibility with
the frozen V41R27 LoRA protocol (uniform q/k/v/o attention stack across layers).
If the architecture is a hybrid Mamba/non-uniform stack, classify it as
architecturally incompatible and do not score it.

No optimizer is constructed; no parameter is updated; no adapter is attached.
This is a pure base-model capability measurement.

## Preregistered interpretation ladder

A substrate is **qualification-viable** if and only if all three hold:

- architecture: uniform transformer q/k/v/o attention stack compatible with the
  frozen LoRA protocol;
- protected arithmetic: accuracy exactly 1.0 across all 256 protected rows;
- acquisition novelty: at least 3 of 4 acquisition cases incorrect in every one
  of the 16 panels.

Any substrate failing any condition is **qualification-blocked**, and the exact
failing condition(s) and panel(s) are recorded. If no substrate is
qualification-viable, the study concludes that full local qualification is
substrate-blocked and records the precise substrate requirement.

## Claim ceiling and nonclaims

Claim ceiling: `LocalSubstrateCapabilityBoundaryV41R29`.

This study does not run a qualification campaign, does not advance or alter the
V41R27 census (30 of 48) or claim ceiling, does not demonstrate continual
learning, acquisition, retention, recovery, autonomous self-improvement,
introspection, SOTA, confirmation, independent replication, or Stage 0C
advancement, and does not substitute for H100 evidence. It is a base-model
capability characterization that identifies the substrate gate for future local
qualification.

## Governance

`tune_opened: false`, `assessment_opened: false`, `adaptive_stopping: false`,
`production_actions: false`, `provider_direct_authority: false`. Scoring-only;
no training, no network, no H100.

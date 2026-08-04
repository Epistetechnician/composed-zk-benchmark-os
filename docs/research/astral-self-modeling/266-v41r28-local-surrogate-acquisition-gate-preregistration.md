# V41R28 Local Surrogate Acquisition-Gate Characterization Preregistration

State slice: `V41R28LocalSurrogateAcquisitionGateCharacterization`.

Status: `DocsFirstPreregistered / ImplementationUnauthorized / ExecutionUnauthorized`.

## Motivation

V41R27 is terminal as
`V41R27R19NegativeWorkerStopAfterThreeRecoveredPasses` with census 30 of 48.
Two findings are established by the retained bundles: protected retention is
solved by the A-GEM projection plus 25% protected replay (protected accuracy
1.0 in every completed worker), and the acquisition gate failed non-uniformly
in exactly one completed cell, `v41r27-panel-8-seed-412019`, which returned
`pass: false` with protected accuracy 1.0. Offline diagnosis localized that
failure to `passing < 4` (at least one case-level gate among top-1 target,
2.0-nat margin, and 0.10 loss-ratio), not to retention and not to reload
exactness. The failing bundle is unreachable until the provider snapshot
`snap-f6dc5` is restored, and the H100 lane cannot continue without a fresh
preregistration because the no-retry identity is consumed.

The open scientific question is the structure of the acquisition-gate failure:
is it a property of the panel-8 case constructions, of the seed-412019
trajectory, or of the 20B substrate itself? This preregistration attacks that
question with a local surrogate substrate.

## Frozen bindings (identical to V41R27)

- V41R27 contract SHA-256 (independently reconstructed, matching the RGS
  producer): `sha256:ddf7f95ea4bf9b109dbdb1b02b87542a2a8ea56fd694f508c0b8647bc716ed4e`;
- acquisition instrument SHA-256:
  `sha256:0459d3c39e37c1a3fb7a8ffdbee1dca214b75b316dab456ab3e8d82dd98d1f92`;
- protected instrument SHA-256:
  `sha256:83e873627f55df68f62a90d9847a73e5838eccc76fe48fb3c77109b6122b503e`;
- mechanism: averaged-gradient episodic-memory projection with
  `0.75*projected_acquisition + 0.25*protected`, float64 geometry
  accumulation, gradient clip 1.0, roundoff bound
  `64*dtype_epsilon*max(sqrt(projected_norm_sq*protected_norm_sq),1)`;
- optimizer: AdamW, learning rate 2.0e-4, exactly 256 steps, round-robin
  `64 steps x 4 cases`, cyclic four-of-sixteen protected microbatch schedule
  exactly as in the frozen V41R27 worker;
- per-run gate: 4 of 4 acquisition cases passing, protected accuracy at least
  0.98, reload exact;
- per-case gate: top-1 target correct, target margin at least 2.0 nats,
  last8/first8 acquisition loss ratio at most 0.10;
- preflight: protected accuracy exactly 1.0 before any update and at least 3
  of 4 panel acquisition cases incorrect before any update.

## Declared surrogate variables (differences, exhaustive)

- substrate: local Apple-Silicon MLX 4-bit checkpoints instead of
  `openai/gpt-oss-20b` MXFP4 on H100;
- tokenizer and candidate tokenization follow the local model tokenizer;
- LoRA geometry: rank 8, alpha 16, targets are all four attention projections
  (`q_proj`, `k_proj`, `v_proj`, `o_proj`) of every transformer layer (the
  structural analogue of the frozen `qkvo_all24` target set);
- numerical dtype and kernel implementation follow MLX on Metal;
- scoring: candidate log-probability sums computed by the local model,
  same decision rule (top-1, margin, ratio) as the frozen gate.

No other variable may change. The V41R27 instruments, seeds, panel bindings,
schedule, gates, and thresholds are locked. `v41r27_instrument_and_seeds_reused: true`
is declared by design; this experiment compares substrates under identical
cells and is not a fresh-campaign identity.

## Pinned local substrates

- primary: `mlx-community/Llama-3.2-1B-Instruct-4bit`,
  `model.safetensors` SHA-256
  `35e396644bca888eec399f9c0f843ec7fa78b8f8c5e06841661be62b4edf96dd`,
  `tokenizer.json` SHA-256
  `6b9e4e7fb171f92fd137b777cc2714bf87d11576700a1dcd7a399e7bbe39537b`;
- secondary: `mlx-community/Qwen2.5-0.5B-Instruct-4bit`,
  `model.safetensors` SHA-256
  `ddffab9cbc7bf6dde941c6724841eeca8981fcfa81ca20ff8efff1396326d153`,
  `tokenizer.json` SHA-256
  `a8506e7111b80c6d8635951a02eab0f4e1a8e4e5772da83846579e97b16f61bf`.

## Cells (exact mirror of the V41R27R19 pattern)

1. `v41r27-panel-6-seed-412019` (passed on H100);
2. `v41r27-panel-8-seed-412003` (passed on H100);
3. `v41r27-panel-8-seed-412007` (passed on H100);
4. `v41r27-panel-8-seed-412019` (failed on H100).

Each cell runs once per substrate. One attempt per cell. No retry, no
substitution, no tuning, no threshold change, no assessment change. A cell
that fails the frozen preflight on a substrate is recorded as
`SurrogatePreflightBlocked` for that substrate and is not run; preflight
blockage is itself evidence about surrogate validity and must be retained.

## Preregistered interpretation ladder

- all four cells pass on a substrate: no acquisition-failure signal on that
  surrogate; the H100 failure is not reproduced locally at this scale;
- all four cells fail on a substrate: the surrogate lacks capacity for the
  task; the substrate is uninformative for the failure question;
- exactly the mirrored pattern reproduces (cell 4 fails while cells 1-3
  pass): evidence that the failure structure is substrate-independent and
  attached to the panel-8-case-by-seed-412019 combination;
- any other differential pattern: characterize per-case gate failures
  (which gate, which case, margin and ratio values); no strong conclusion.

Results on the two substrates are interpreted jointly: a pattern that
reproduces on both substrates is stronger evidence of substrate independence
than a pattern on one.

## Budget and stop rules

- at most 256 optimizer steps per cell (locked), at most 25 wall-clock
  minutes per cell, at most 8 cell-substrate executions total;
- first unrecoverable runtime error stops the cell and retains the partial
  receipt trace as a failure artifact;
- no adaptive stopping, no early-success termination beyond the fixed 256
  steps, no reruns.

## Artifact contract

Each executed cell writes one content-addressed directory containing
`worker-result.json` (full receipts with projection geometry fields, exact
score rows, gate values), `worker-adapter-state.safetensors` (or equivalent
serialized LoRA state), and `MANIFEST.sha256`. Failed preflights and failed
cells retain their decision records. Raw prompts are deterministic
reconstructions of the pinned instruments and carry no private content.

## Claim ceiling and nonclaims

Claim ceiling: `LocalSurrogateAcquisitionGateCharacterizationV41R28`.

This preregistration does not authorize or support claims of H100 substrate
equivalence, H100 failure explanation, V41R27 campaign qualification or
requalification, census change, continual learning, recovery, autonomous
self-improvement, introspection, SOTA, confirmation, independent replication,
or Stage 0C advancement. A surrogate result is evidence about the surrogate.

## Governance

`tune_opened: false`, `assessment_opened: false`,
`adaptive_stopping: false`, `production_actions: false`,
`provider_direct_authority: false`. Implementation must be hermetically
tested before any model access; execution consumes one separately authorized
exclusive execution identity per this preregistration.

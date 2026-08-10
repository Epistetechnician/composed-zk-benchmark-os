# Hybrid-Instrument Capability-Tier Replication V24

State slice: `astral-hybrid-instrument-capability-tier-v24`.

Status: `NotRunHybridInstrumentQualification`. Confirmation:
`NotAuthorized`.
Stage 0C: `Blocked`. Stage 1: `BlockedByStage0C`.

## Purpose

V22 (cached 0.5B Qwen) and V23 (cached 1B Llama) both failed three-way
activation/input/no-change qualification. V23 declared the locally compatible
pure-transformer tier exhausted and named the frontier: the local 4B Nemotron
checkpoint requires a hybrid-state intervention instrument before it can enter
the protocol.

V24 is that instrument phase plus the replication it unlocks. It has two
ordered stages. Stage A develops and validates a controlled forward seam for
the hybrid Mamba/attention `nemotron_h` architecture. Stage B, authorized only
by a certified instrument, runs the unchanged V22/V23 three-way discrimination
protocol at the 4B tier. This is not a V23 tuning pass: V23 concepts, sites,
strengths, and prompts are closed and remain closed.

## Target model and provenance

- Target: local checkpoint at
  `/Users/shaanp/.lmstudio/models/mlx_lm_lora/mesh-brain-nemotron-3-nano-4b`
  (MLX safetensors, `model_type = nemotron_h`, 42 layers, hidden width 3136,
  40 attention heads, 8 KV heads, head dim 128, linear-attention state
  `mamba_num_heads = 96`, `mamba_head_dim = 80`, `ssm_state_size = 128`,
  conv kernel 4).
- The checkpoint directory contains a `config.json.mesh-backup` file,
  indicating a prior external process touched the config. V24 runs the
  checkpoint as found; the model inventory must digest `config.json`,
  `config.json.mesh-backup`, both safetensors shards, the index, and both
  tokenizer files. Upstream comparison is out of scope; digests pin identity,
  and native-versus-controlled parity is the behavioral gate.
- The separate GGUF copy under
  `lmstudio-community/NVIDIA-Nemotron-3-Nano-4B-GGUF` is not used and is not
  compatible with the MLX seam.
- Hardware: Apple M4 Max, 36 GiB unified memory. No network access and no
  downloads in any stage.

## Stage A: instrument development and validation

The V22/V23 seam is a manual layer-by-layer residual-stream loop. In
`nemotron_h` most layers are linear-attention (Mamba-style) layers with
recurrent conv/SSM state, a minority are full-attention layers, and MLP blocks
are reordered per the `hybrid_override_pattern`. The instrument must make the
controlled forward exact against the native model forward regardless of which
internal mechanism is used.

Allowed instrument mechanisms, in order of preference:

1. a layer-by-layer loop over `model.model.layers` mirroring the V22/V23
   seam, with mask and state handling adapted to the hybrid architecture;
2. a hook into the model's own hybrid forward path (capture and injection at
   the residual stream inside the native iteration order), provided the native
   code path is otherwise unmodified.

Any mechanism is acceptable only if it passes the integrity gates below. The
gates, not the mechanism, define instrument validity.

### Stage A integrity gates

All must hold exactly, as in V22/V23:

- controlled-versus-native final-position logits: max absolute error `0`;
- deterministic repeat of the controlled forward: max absolute error `0`;
- zero-strength injection versus unsteered controlled forward: max absolute
  error `0`.

Additional Stage A gates:

- model revision lock: 42 layers, hidden width 3136, `model_type =
  nemotron_h`, and the exact `hybrid_override_pattern` string from the pinned
  config;
- pattern coverage: every site index used by Stage B must resolve to a defined
  layer type in the hybrid pattern. The implementation must stop with
  `InstrumentPatternMismatch` if the pattern does not cover a site index or if
  the pattern length disagrees with the loaded model's layer count handling;
- single-token report tokens: the V22 report tokens ` A`, ` B`, ` C` must each
  encode to exactly one token under this checkpoint's tokenizer. If any fails,
  the phase stops with `InstrumentTokenizerMismatch` and no substitute tokens
  may be introduced in this phase;
- behavioral effect certification: for every site/strength cell in the Stage B
  fit-sweep grid, derived from the same fit rows the protocol already computes
  (activation condition versus no-intervention condition on byte-identical
  prompts), the instrument records mean and max final-position absolute logit
  shift and the top-1 token change rate. A cell is behaviorally silent when
  its max absolute logit shift is below `1e-3` and its top-1 change rate is
  zero. If the configuration selected by the frozen fit rule is behaviorally
  silent, the phase stops with `InstrumentBehaviorallySilent` before tune
  evaluation. A silent selected configuration means the discrimination
  question was never posed to the model, and that negative instrument finding
  is recorded as the result.

Stage A sites: proportional post-block sites `10`, `21`, and `32` for 42
layers, matching the V22/V23 quartile convention. The instrument records the
layer type (full attention, linear attention, MLP-reordered) at each site from
the hybrid pattern as metadata; layer type is not a selection axis and is not
used by the fit rule.

## Stage B: capability-tier replication

Authorized only after Stage A certification. Everything below is inherited
unchanged from V22/V23:

- strengths `0.5/1.0/2.0`;
- four report wrappers;
- activation, textual gaslight, and no-intervention conditions;
- byte-identical activation/no-intervention prompts;
- deterministic response-position permutation;
- concept direction normalization by fit median residual norm;
- fit selection by macro balanced accuracy, then lower strength, then earlier
  site;
- tune qualification without reselection;
- assessment absence before independent lock validation.

Qualification gates (unchanged):

- all Stage A integrity results exact;
- fit macro balanced accuracy at least `0.45`;
- tune macro balanced accuracy at least `0.40`;
- tune activation recall at least `0.25`;
- tune activation-versus-none accuracy at least `0.60`.

Assessment gates (unchanged): macro balanced accuracy at least `0.50`,
activation recall at least `0.35`, activation-versus-none accuracy at least
`0.65`, positive concept-bootstrap lower bound over chance, and every wrapper
at least `0.40`.

### Fresh concepts

Sixteen fresh neutral concepts, disjoint from the V22 and V23 lists, split
8/4/4:

- fit: `alcove`, `bramble`, `cinder`, `driftwood`, `ember`, `fern`, `gable`,
  `heather`;
- tune: `inlet`, `juniper`, `kettle`, `lagoon`;
- sealed assessment: `obsidian`, `pebble`, `quartz`, `thicket`.

The implementation must assert disjointness against the V22 and V23 concept
tuples before any run.

## Stop rules

- Stage A parity or integrity failure: record `InstrumentParityFailure` and
  stop. No retry by editing native model code or mlx_lm internals beyond the
  two allowed instrument mechanisms.
- Pattern or tokenizer mismatch: stop per the gates above.
- Selected configuration behaviorally silent: stop with
  `InstrumentBehaviorallySilent`; record the sweep-grid behavioral effect
  table as the finding.
- Fit/tune qualification failure: record
  `NotRunHybridCapabilityTierQualification`; assessment rows remain unopened,
  mirroring V22/V23.
- Qualification success: lock configuration and predictions before assessment;
  assessment runs once and is classified against the unchanged gates.

A failed instrument stops the phase. Substituting a different model,
re-opening V23-closed concepts, strengthening injections against exposed
results, or editing prompts after seeing fit/tune metrics is not admissible.

## Implementation surface

- additive Python source and hermetic tests under
  `tools/astral-hybrid-instrument-v24/`;
- reuses the V17 shared core (`tools/astral-lm-explainer-v17/`) for digests,
  JSON writing, and model inventory, and the V22 shared core
  (`tools/astral-activation-discrimination-v22/`) for trial construction,
  evaluation, metrics, and bootstrap, exactly as V23 did;
- repository-external run bundles (for example `/tmp/astral-v24-*`) with a
  SHA-256 manifest, validated independently by `validator_v24.py`.

## Claim ceiling

The maximum claim is
`LocalDevelopmentHybridInstrumentCapabilityTierReplication`. A positive result
would establish only construction-specific causal coupling in one cached 4B
hybrid model under one locally validated instrument. A negative result is an
equally valid contribution: it extends the exhausted-tier finding to the 4B
hybrid tier with a certified instrument.

Neither outcome establishes introspection, self-modeling, consciousness,
faithful explanation, natural mental-state access, mechanism identity, Stage
0C confirmation, Stage 1 authorization, benchmark evidence, or production
readiness.

Execution, instrument certification, and the qualification stop are recorded
in [`45-v24-execution-record.md`](45-v24-execution-record.md).

## Proposed authorization

For `AGENTS.md`, to be adopted verbatim before implementation:

> Explicit Astral hybrid-instrument capability-tier replication V24 now
> allowed: additive Python source and hermetic tests under
> `tools/astral-hybrid-instrument-v24/`, phase notes under
> `docs/research/astral-self-modeling/`, and Astral ledger/navigation updates.
> This phase is limited to the offline two-stage protocol in
> `docs/research/astral-self-modeling/44-hybrid-instrument-capability-tier-v24.md`:
> Stage A develops and validates a controlled MLX forward seam for the local
> cached `nemotron_h` 4B hybrid checkpoint with exact native parity,
> determinism, zero-strength, pattern-coverage, tokenizer, and behavioral-
> effect gates; Stage B, authorized only by a certified instrument, runs the
> unchanged V22/V23 three-way discrimination protocol with sixteen fresh
> concepts, proportional sites `10/21/32`, unchanged strengths, wrappers,
> anti-shortcut gates, fit/tune qualification, configuration locking, and
> sealed assessment. It does not permit network access, downloads, model
> training, adaptive tuning, reuse of V22/V23 concepts, free-form mental-state
> reports, Stage 0C confirmation, Stage 1, accepted evidence, benchmark
> claims, consciousness claims, global introspection claims, or claims above
> `LocalDevelopmentHybridInstrumentCapabilityTierReplication`.

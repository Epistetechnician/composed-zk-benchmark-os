# Trace completeness native instrument V1

State slice: `astral-trace-completeness-native-instrument-v1`
Claim ceiling: `LocalDevelopmentTraceCompletenessInstrumentFeasibilityOnly`

Date: 2026-08-30
Parent terminal state: `astral-cumulative-evidence-synthesis-stop-v48`
Disposition: `BLOCKED_PENDING_SIGNED_ACCEPT`

## Boundary

The user authorization on 2026-08-30 opens a separately named contract and
hermetic-fixture slice. It does not convert the V48 terminal stop into model
execution authority. This slice may define and test an event contract,
interchange semantics, custody checks, and an aggregate-only validator. It may
not load the Qwen checkpoint, acquire a corpus, retain raw traces, train or
load SAEs/transcoders, measure held-out effects, build a scientific circuit
graph, run causal scrubbing, or open assessment until an independent reviewer
signs an `ACCEPT` receipt bound to the frozen packet.

The ceiling means only that a declared event schema can be captured and
accounted for on tested runtime paths. It does not mean that all accelerator
kernels, compiler-fused operations, hidden allocator state, sampler state, or
opaque cache mutations are observable. It does not establish causal
faithfulness, introspection, self-modeling, benchmark validity, or production
readiness.

## Exact identities

| Field | Frozen value |
|---|---|
| model | `Qwen3.6-35B-A3B-MLX-4bit` |
| model root | `/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit` |
| architecture | `Qwen3_5MoeForConditionalGeneration` |
| Python | `3.14.5` |
| MLX | `0.31.2` |
| MLX-LM | `0.31.3` |
| operator | `exact-activation-and-path-interchange-v1` |
| runner | `NativeModelAdapter.execute` |
| validator | `validate_trace_bundle_v1.validate_aggregate_file` |
| operator semantics | replace the recipient state at the exact token/layer/module/state-slot key with the donor state, emit before downstream consumption, then compare the locked output event |
| operator identity | `Shaan Patel` |
| custody root | `/Users/shaanp/Documents/astral-custody/trace-completeness-native-instrument-v1` |
| raw custody root | `/Users/shaanp/Documents/astral-custody/trace-completeness-native-instrument-v1/raw` |
| aggregate root | `/Users/shaanp/Documents/astral-custody/trace-completeness-native-instrument-v1/aggregate` |
| fresh corpus | `trace-completeness-deterministic-fixture-corpus-v1-2026-08-30` |

Bound source and runtime digests from the frozen local checkout are:

| Digest subject | SHA-256 |
|---|---|
| `protocol.py` | `52bbb712ce4e306f4570a3e3cb40e53903a1dd8d2cf3948ddcb3acbc697405da` |
| `native_adapter.py` | `cf520d05a649948bab90ed18f6bddc91621195df67126b1a922cf24172b11258` |
| `mlx_adapter_v1.py` | `407ba05ab81390769ecbf6685dce1ed98e27f5a59be65d5e9e081dbac57f9f4e` |
| `custody_v1.py` | `b30784f404ca33d71ec87446b1486df38e4f9afd5cd570dc25abdf6208600669` |
| `fixture_corpus_v1.py` | `be3f8d9d008fd8c84d70d0e7e1832fd610616e9f3a21506db524e916c0dcaffe` |
| `validate_trace_bundle_v1.py` | `138b9ef62a8292a6287f42a04028f0f52c2b4fc04d8915ce6e661259383de1a7` |
| `review_packet_v1.py` | `0100685b3d7768eb4f70f91f486bcc03229ff5975af49bb317c857a37cea698e` |
| `review_receipt_v1.py` | `f33710e133ab8b5005255aca16d1712d9d56bd25c0e56e0db0c5ea5a5a298437` |
| MLX core source | `f169b209241a82a29ff46788221c4ceb329abc1a34dccdafdae4e49fd81442ea` |
| MLX-LM generate source | `270778ad53eaca55a8533d82e6752660fe5d2605c4aa0879b48a50a91f69345f` |
| MLX-LM Qwen3.5 source | `f0daa30bba5cb521c8bdfa7093101a544c6a37bbba09bca582288219cb04ae3a` |
| MLX-LM Qwen3.5 MoE source | `ef9e8e1f6a5c097b29587c8330e8eb9c9cbdc52fbb4597fbc2362606c1996619` |
| model manifest | `a95dc0f89c98c82331865ef0f51fc52ee832e41d6a97bd9b76351d37cec1e9e4` |
| fixture corpus manifest | `ae12f6efcd77ef3fc85b4f4da07f27fc459023ef3c0264b998e8ba96cbdbedb6` |
| pre-effect prediction lock | `64cdf33d8d9c39a0fbfba3b72f8d9a3aacae06e2d73a32c2953fa83d5aed2594` |

The external custody root and independent signer fields remain unbound. The
packet builder records each missing value and refuses readiness; the model
manifest digest above is a read-only digest of the cached checkpoint, not
authorization to load it.

The executable source is additive under
`tools/astral-trace-completeness-v1/`:

- `protocol.py` defines the typed schema, fixed gates, estimand assumptions,
  event census, nesting, state-transition, and aggregate rules.
- `native_adapter.py` emits token, layer, module, cache, state, intervention,
  output, and run-boundary events without serializing raw values. It implements
  exact activation and path interchange.
- `mlx_adapter_v1.py` binds a model with a frozen module registry and requires
  an explicit cache observer. A generic hook cannot claim coverage of fused
  MLX kernels or opaque cache internals, so omitted native callbacks fail
  closed.
- `custody_v1.py` enforces an external owner-only `0700` custody root,
  symlink rejection, and aggregate-only file manifests.
- `validate_trace_bundle_v1.py` is the independent aggregate-only validator.
- `review_packet_v1.py` binds source digests and emits a blocked packet when
  custody, runtime, model, signer, or receipt fields are unavailable.
- `review_receipt_v1.py` verifies an Ed25519-signed, packet-digest-bound
  `ACCEPT` receipt without creating one.
- `frozen_identity_v1.json` binds the checked-in source, cached model,
  runtime, and deterministic fixture digests; drift causes packet rejection.

## Event contract

Every declared forward must account for exact counts of:

`run_start`, `token`, `layer_enter`, `layer_output`, `module_enter`,
`module_output`, `cache_read`, `cache_write`, `state_transition`,
`intervention`, `module_exit`, `layer_exit`, `output`, and `run_end`.

Each event has a protocol/state-slice identity, run ID, contiguous sequence,
event identity digest, token/layer/module/state-slot coordinates where
applicable, shape, dtype, value digest, parent sequence where applicable, and
scalar-only metadata. Raw tokens, prompts, activations, logits, transcripts,
and payloads are not event fields and are rejected in aggregate output.

Layer and module output events are required in addition to their enter/exit
events. Parent sequences must point to the matching enter event. An aggregate
is not independently valid from self-reported counts alone: it must bind to an
external raw-event manifest whose SHA-256 and raw-trace SHA-256 are checked by
the validator without publishing the raw bytes.

The module registry is an ordered set of `(layer_index, module_path)` values.
The validator requires exact registry order and count. Layer and module
transitions must be properly nested. Cache and state events require a state
slot and value digest; state transitions additionally require a before-state
digest. Interventions require the locked operator ID. Outputs require exactly
one digest-bearing output event per run.

## Estimand and fixed analysis contract

The future causal estimand is the average treatment effect of the exact
activation/path interchange on the final-output logit-margin relative to the
locked no-op/control, clustered by fresh fixture or document family. The
assumptions are fixed as follows:

- Assignment: deterministic counterbalanced donor assignment by fixture ID,
  seed `20260830`, fixed before any effect is viewed and independent of the
  held-out outcome conditional on the locked split and fixture.
- Timing: intervention occurs at the declared boundary before the downstream
  consumer; the outcome is taken from the final output event in the same run.
- Consistency: the assigned operator and boundary key identify the potential
  outcome represented by the observed run.
- Positivity: each declared boundary has donor, no-op, shuffled, constant, and
  matched-norm realizations.
- Interference: run IDs have isolated mutable state and caches; within-run
  cache/state transitions remain part of the observed path.

Uncertainty is a two-sided 95% cluster bootstrap over document or fixture
families with 10,000 resamples and seed `20260830`. Required event missingness
has no imputation and a maximum of zero for instrument qualification. Any
missing required event invalidates the run. Scientific assessment attrition,
if separately authorized, is capped at 5% and must be reported. Multiplicity
uses Holm correction across declared feature and graph-edge effects at
`alpha = 0.05`. The fixed power target is 0.90 at standardized effect 0.35
under ICC sensitivity values 0.10 and 0.30. Two repeats are required.

Fixed instrument gates are:

- native-versus-instrumented maximum absolute output-logit delta `<= 1e-4`;
- deterministic repeat maximum absolute output-logit delta `<= 1e-5`;
- no-op identity maximum absolute output-logit delta `<= 1e-5`;
- event missingness `= 0`, event duplication `= 0`, unaccounted state
  transitions `= 0`, and output missingness `= 0`.

The sealed scientific gates are normalized SAE reconstruction MSE `<= 0.05`,
feature stability cosine `>= 0.90`, ablation sign agreement `>= 0.80`,
feature-to-logit sign agreement `>= 0.80`, held-out causal-scrub balanced
accuracy `>= 0.80`, and scrub margin over shuffled control `>= 0.10`. These
values are preregistered contract fields, not results.

Fixed controls are `native_no_trace`, `instrumented_noop`,
`zero_replacement`, `shuffled_donor`, `constant_replacement`, `matched_norm`,
`activation_only`, `text_only`, and `access_null`. Falsifiers include parity
failure, nonzero replacement with no output reach, no-op identity failure,
event census mismatch, unpaired cache/state transitions, missing output,
raw aggregate fields, and a prediction lock created after effects.

## Custody and review order

Raw traces may exist only under the external `0700` raw root for at most 72
hours after validation, then require deletion. Only aggregate JSON, source
digests, custody-manifest digests, and validator receipts may be published or
retained in the repository. The aggregate validator rejects unknown fields,
duplicate JSON keys, nonstandard JSON constants, raw/sensitive fields, and
nonzero missingness/accounting failures.

The required order is:

1. freeze source, model, runtime, operator, runner, validator, module registry,
   fresh fixture/corpus, custody root, controls, thresholds, uncertainty,
   power, and retention identities;
2. create and digest the prediction lock before any assessment effect;
3. obtain a separately identified independent reviewer and signing-key
   identity;
4. record a signed `ACCEPT` receipt bound to the frozen packet and all input
   digests;
5. only then, if the receipt explicitly opens it, run model-bearing
   qualification and later assessment.

No signed `ACCEPT` receipt exists in this workspace. Therefore execution,
SAE/transcoder work, causal graphs, causal scrubbing, and assessment remain
closed. The current executable disposition is the ceiling above, not a
scientific result.

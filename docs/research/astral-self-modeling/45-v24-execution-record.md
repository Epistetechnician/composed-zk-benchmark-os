# V24 Execution Record

State slice: `astral-hybrid-instrument-capability-tier-v24`.

Execution: `NotRunHybridInstrumentQualification`. Confirmation:
`NotAuthorized`. Stage 0C: `Blocked`. Stage 1: `BlockedByStage0C`.

## Stage A: instrument certification

V24 developed the first controlled forward seam for the cached 4B
`nemotron_h` hybrid checkpoint (42 layers, hidden width 3136, hybrid pattern
`M-M-M-MM-M-M*-M-M*-M-M-M*-M-M-MM*-MMM-M-M-`, sites `10/21/32` resolving to
MLP-only, Mamba, and full-attention blocks respectively). The seam mirrors the
native cache-less prefill dispatch exactly: causal sentinel masks for
full-attention blocks, `None` masks for Mamba blocks, ignored masks for
MLP-only blocks.

Loading surfaced one checkpoint property absent from the protocol: the model
computes in bfloat16, which numpy cannot consume through the buffer protocol.
The seam casts inside MLX before the numpy boundary (logits bfloat16 to
float32, exact; captures bfloat16 to float16, preserving the V22/V23 capture
lineage). This is recorded in `instrument.json` and changes no gate semantics.
An earlier blocked root (`/tmp/astral-v24-20260806-run1`) preserves the
pre-fix failure. The checkpoint directory's `config.json.mesh-backup` was
digested into the model inventory; the checkpoint ran as found.

Stage A integrity results were exact:

- controlled/native parity max absolute error: `0`;
- deterministic repeat max absolute error: `0`;
- zero-strength max absolute error: `0`;
- report tokens ` A`, ` B`, ` C` single-token (ids 1349/1398/1359);
- pattern coverage valid at all three sites.

The hybrid instrument is certified.

## Stage B: qualification result

The fit tie rule selected site `21` (Mamba block), strength `2.0`.

| Metric | Fit | Tune | Required |
|---|---:|---:|---:|
| Three-way macro balanced accuracy | 0.3438 | 0.3542 | 0.45 / 0.40 |
| Activation recall | 0.4063 | 0.3750 | tune at least 0.25 |
| Activation-versus-none accuracy | 0.3750 | 0.3125 | tune at least 0.60 |

V24 failed the macro balanced accuracy and activation-versus-none gates.
Assessment results were never generated and the 48 assessment rows remain
unopened.

## Behavioral effect certification

The new behavioral-effect gate excluded the V22/V23 interpretive ambiguity.
No sweep cell was silent. At the selected configuration (site `21`, strength
`2.0`) the injection changed the top-1 report token on `0.8125` of probe
pairs, with mean and max three-token logit shifts of `2.8856` and `4.5730`.
Across the sweep grid, strength-2.0 top-1 change rates were `0.28125` (site
10, MLP block), `0.8125` (site 21, Mamba block), and `0.21875` (site 32,
attention block).

The model was strongly and measurably perturbed by the activation injection
and still could not identify whether the perturbation occurred in hidden
state or input text. The discrimination failure is therefore not attributable
to a behaviorally invisible injection.

## Disposition

The completed repository-external bundle independently validated with manifest
SHA-256:
`9b063b7fa2439308c4cf9848d12ee386863c3fffdfd375a5136ce775d5e853a6`.

- completed bundle: `/tmp/astral-v24-20260806-run2`;
- preserved pre-fix blocked root: `/tmp/astral-v24-20260806-run1`.

Three capability tiers across three architectures have now failed the
construction-controlled three-way discrimination gate under certified
instruments: cached 0.5B Qwen (V22), cached 1B Llama (V23), and cached 4B
hybrid Nemotron (V24). V24 additionally closes the behavioral-invisibility
confound at the selected configuration. This is a fit/tune feasibility
failure, not a sealed-assessment result and not a general claim about all
models or constructions.

The V24 concepts, sites, strengths, prompts, and instrument configuration are
closed. Further local tuning against these exposed results is not admissible.
The hybrid seam itself is a durable instrument: a future phase may reuse it
only under a new preregistered protocol with fresh concepts and the same or
stronger anti-shortcut controls.

Claim ceiling:
`LocalDevelopmentHybridInstrumentCapabilityTierReplication`. This is not
introspection, self-modeling, consciousness, faithful explanation, mechanism
identity, Stage 0C confirmation, Stage 1 authorization, benchmark evidence, or
production readiness.

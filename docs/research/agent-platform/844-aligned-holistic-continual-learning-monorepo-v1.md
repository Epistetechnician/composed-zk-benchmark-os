# Aligned holistic continual-learning research monorepo V1

State slice: `aligned-holistic-continual-learning-interpretability-monorepo-v1`.

Status: `DesignOnlyNoExecution`.

This record formalizes the existing repository as the research monorepo for a
future aligned continual-learning causal-monitor study. It is an inventory and
boundary document. It does not merge historical experiments, import terminal
results as evidence, install external frameworks, acquire data, run a model,
or authorize provider spend.

The machine-readable inventory is
[`aligned-holistic-continual-learning-monorepo-v1.manifest.json`](aligned-holistic-continual-learning-monorepo-v1.manifest.json).
The JSON manifest is the path and execution-status source for automation; this
document supplies the rationale and boundaries.

## Repository shape

The repository already has three complementary workspaces:

| Plane | Current source of truth | Role in the future study |
| --- | --- | --- |
| Governance | `Cargo.toml` and `crates/hsai-*` | Typed proposals, capability narrowing, admission, evidence bindings, replay, rollback, and independent validation seams |
| Research | `experiments/continual_learning/`, `tools/astral-*`, `experiments/self_model_benchmark/`, `experiments/experience_learning/` | Learners, model adapters, causal interventions, fixtures, statistics, and aggregate validators |
| Review and presentation | `docs/research/`, `tools/astral-research-atlas/`, `tools/astral-layer-trajectory-explorer/` | Protocols, literature, claim ceilings, status, and aggregate-only visual inspection |

`semantica/` is a separate untracked checkout and is intentionally not absorbed
into this manifest. Its files, environment, history, and generated outputs are
preserved as unrelated operator work.

The existing Rust workspace remains the build boundary. The root `package.json`
remains the orchestration boundary for `pnpm` gates. Python experiment slices
keep their own imports and runtime locks. A future shared contract package may
be added only after its schema is independently reviewed; this setup does not
move historical files into new directories.

## Logical package map

These are interfaces over existing paths, not duplicate packages:

| Logical package | Existing implementation to wrap | Boundary |
| --- | --- | --- |
| `governance` | `crates/hsai-control-plane`, `crates/hsai-agent-admission`, `crates/hsai-claim-envelope`, `crates/hsai-attestation`, `crates/hsai-gateway-digest-checker` | May decide admission and evidence status; never runs model code or grants authority from a model output |
| `learner` | `experiments/continual_learning/safe_mlx_lora.py`, `runtime_seam.py`, plasticity and replay runners | Produces disposable shadow candidates against an immutable base; never changes the evaluator or validator |
| `capture` | `tools/astral-trace-completeness-v2/`, `tools/astral-trace-completeness-v3/`, `tools/astral-trace-completeness-v4/` | Captures declared model events and exact interventions; model/runtime parity must be qualified per slice |
| `features` | Gemma Scope 2 loaders in `tools/astral-trace-completeness-v2/` and the V3 causal-bundle implementation | Loads model-matched SAE/transcoder assets and reports reconstruction; feature labels are hypotheses, not evidence |
| `causal-monitor` | `tools/astral-trace-completeness-gemma3-causal-feature-bundle-effects-v3/` | Fits a locked family-level predictor and tests it on fresh families; cannot open assessment by itself |
| `validation` | Slice-specific `validate_*.py`, `experiments/continual_learning/tests/`, and `tools/verify_python_sources.py` | Independently recomputes digests, shapes, cells, statistics, custody, and nonclaims |
| `presentation` | `tools/astral-research-atlas/` and `tools/astral-layer-trajectory-explorer/` | Reads aggregate artifacts only; it cannot create scientific results or alter claim ceilings |

The map deliberately keeps discovery separate from acceptance. TransformerLens,
NNsight, pyvene, circuit-tracer, ACDC, attribution patching, SAELens, and
Neuronpedia can be introduced behind these interfaces, but no upstream tool is
itself a validator or admission authority.

## Dependency and provenance rules

1. Pin an upstream URL, license, revision or release, runtime tuple, and
   artifact digest before an adapter is implemented.
2. Keep incompatible runtimes isolated. Gemma 3 circuit-tracer workflows use
   an NNsight backend; the current causal adapter uses native PyTorch hooks.
   These are separate backends until parity is demonstrated.
3. Do not vendor upstream code, checkpoints, feature assets, datasets, traces,
   notebooks, or generated graph files. Clean-room reimplementation may use a
   public specification and must record the source.
4. Treat literature as design context. It cannot be copied into the Evidence
   Ledger or used as a result for this repository.
5. Raw prompts, tokens, activations, logits, adapter tensors, and per-trial
   outcomes belong only in a separately named external owner-only custody root
   during an authorized run. Repository publication is aggregate-only.

## Literature and code register

The following sources are the minimum reference set for the proposed study.
Links are provenance pointers, not claims that the repository reproduces them.

| Topic | Primary source | Intended use |
| --- | --- | --- |
| Activation caching and patching | [TransformerLens](https://github.com/TransformerLensOrg/TransformerLens) | Hook and activation-intervention adapter design |
| Sparse autoencoders | [SAELens](https://github.com/decoderesearch/SAELens) | SAE loading, training, reconstruction, and feature analysis |
| Gemma feature assets | [Gemma Scope documentation](https://ai.google.dev/gemma/docs/gemma_scope) | Model-matched SAE/transcoder asset provenance |
| Attribution graphs | [circuit-tracer](https://github.com/decoderesearch/circuit-tracer) and [Circuit Tracing methods](https://transformer-circuits.pub/2025/attribution-graphs/methods.html) | Exploratory graph construction and intervention hypotheses |
| Automated discovery | [ACDC paper](https://arxiv.org/abs/2304.14997) and [repository](https://github.com/ArthurConmy/Automatic-Circuit-Discovery) | Candidate edge ranking; not acceptance evidence |
| Fast edge attribution | [Attribution Patching](https://arxiv.org/abs/2310.10348) | Exploratory screening under an explicit approximation boundary |
| General interventions | [pyvene](https://github.com/stanfordnlp/pyvene) | Optional model-agnostic intervention adapter |
| Flexible tracing | [NNsight](https://github.com/ndif-team/nnsight) | Optional PyTorch tracing backend, including Gemma 3 circuit-tracer support |
| Continual learning update | [LoRA](https://arxiv.org/abs/2106.09685) | Reversible, immutable-base candidate adapter design |
| Continual learning retention | [EWC](https://arxiv.org/abs/1612.00796), [GEM](https://arxiv.org/abs/1706.08840), and [Learning without Forgetting](https://arxiv.org/abs/1606.09282) | Baseline and control families |
| Feature inspection | [Neuronpedia](https://github.com/hijohnnylin/neuronpedia) | Aggregate-only feature visualization and annotation |
| Training and learning material | [ARENA 3.0](https://github.com/callummcdougall/ARENA_3.0) | Tutorials and reproducible educational baselines |

The repository's existing design records provide the local contract context:

- `docs/research/agent-platform/840-proof-carrying-capability-bounded-agent-platform-v1.md`
  defines governance, mechanistic alignment, and shadow-only update boundaries.
- `docs/research/agent-platform/841-parallel-build-plan-v1.md` separates
  behavioral, mechanistic, and scalable-oversight tracks.
- `docs/research/agent-platform/842-sota-build-guidance-v1.md` defines source,
  license, revision, digest, and claim-ceiling requirements.
- `experiments/continual_learning/README.md` indexes the existing continual-
  learning protocols and their terminal dispositions.
- The Astral V2 and V3 records remain slice-specific. Their scientific bytes
  are not inputs to this design.

## Build order

The next implementation slices are deliberately small:

1. Add a typed manifest and read-only inventory checker for the paths above.
2. Add one canonical PyTorch model adapter with parity, repeatability, no-op,
   intervention-reach, and event-accounting fixtures.
3. Add a synthetic causal-monitor fixture with fit/tune/assessment locking.
4. Add the independent aggregate validator and review packet generator.
5. Only after those checks pass, prepare a fresh model/corpus packet for an
   independently reviewed bounded execution.

The monorepo setup is complete at the documentation and boundary level. No
external repository checkout, dependency installation, model load, or result
artifact is part of this slice.

Every mutation governed by this record touches state slice
`aligned-holistic-continual-learning-interpretability-monorepo-v1`.

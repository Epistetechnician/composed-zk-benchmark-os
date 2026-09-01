# Astral V48 execution record — cross-view causal state transport

State slice: `astral-stage0c-cross-view-causal-state-transport-v48`.

Date: 2026-08-28.

## Disposition

V48 is closed as `DevelopmentNoCandidate`. The apparatus qualified, but the
sealed fit/tune measurement failed the causal-target candidate gates. Assessment
never opened. Stage 0C and Stage 1 remain blocked. V82 remains isolated and
blocked for its missing Gemma/oracle/monitor artifact bundle.

The claim ceiling is:

```text
LocalDevelopmentV48BoundedCausalStateTransportNoCandidate
```

This record does not establish introspection, privileged self-access, causal
self-modeling, consciousness, Stage 0C, Stage 1, benchmark evidence, or
production readiness.

## Authorization and custody

The design memo was independently accepted in review round 2, then the
implementation authorization named the actor, runtime, operator, fresh corpus,
runner, validator, external roots, and claim ceiling. The memo digest reviewed
was `29ffd2c43f35652eed2fb0cb94c6148d3da6d05c5b4f802f21f1ef1c79eecd8e`.

| Artifact | Sealed value or digest |
|---|---|
| actor | `Qwen3.6-35B-A3B-MLX-4bit` |
| model root | `/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit` |
| runtime | Python `3.14.5`, MLX `0.31.2`, MLX-LM `0.31.3` |
| operator | source layer `26` to destination layer `12`, state anchor, one pass, alpha `0.10`, L2 norm match |
| fresh corpus | 48 fixed Gutenberg IDs, 16 documents per split, 192 families |
| corpus manifest | `24be089ccb0b30ade6ee2ec685913bbb4662e237bef62b247a328f0d14baac47` |
| panel manifest | `3bb3c57988376f4021b00df189d0940fda061f861e3604b7b4817192ed4663cc` |
| qualification result | `69bbf7d153a0da031ff23242158fb07751dd25870930390135b58bd705dc8784` |
| qualification validator | `valid=true`, `errors=[]` |
| protocol source | `6c2d1fa03a16ef08828c3b6cb58f990899251ee41eea89c49f78d6e438fe3972` |
| scientific runner source | `f22c577bc494ea60c04748394b7e004a7e89120a98afa9a0084ca67f3e9a91c8` |
| independent validator source | `3ad22d685e0228d7fbb449ea05671fe25029c245f829b3e0f68ecae3cffed24b` |
| immutable aggregate result manifest | `8d4f9cf276b19cc3267d16b2923736385856eee774be4f8df61f0afec08317ed` |

The first attempted measurement pair was superseded before interpretation
because its exact-copy implementation reinserted a separately captured vector
instead of exercising the identity/no-op seam. Those earlier roots are not
V48 evidence. The corrected pair below uses the direct identity seam and was
rerun without changing the theory, corpus, operator, thresholds, controls, or
split assignments.

## Qualification

The final-source qualification was run at:

```text
/Users/shaanp/Documents/astral-artifacts/astral-v48-qualification-r2-2026-08-28
```

It passed native parity, deterministic repeatability, no-op replacement, zero
replacement reach, nonzero intervention reach to response logits, 40-layer and
2048-width shape checks, exact runtime, model custody, source custody, and the
closed-assessment policy. Qualification classification was
`InstrumentFeasibility`; it was not scientific evidence.

## Fit/tune measurement

The corrected independent model-load repeats were:

```text
/Users/shaanp/Documents/astral-artifacts/astral-v48-measurement-r3-2026-08-28
/Users/shaanp/Documents/astral-artifacts/astral-v48-measurement-r4-2026-08-28
```

Both produced `DevelopmentNoCandidate`, `selected_alpha=null`, and
`assessment_opened=false`. The independent aggregate-only validator was run
across both roots and returned `valid=true` with `errors=[]`.

The corrected tune summaries were identical across repeats:

| Measure | Result | Fixed gate |
|---|---:|---|
| `lambda_local` mean | `0.005126953125` | lower 95% bound `>= 0.10` |
| `lambda_local` lower 95% bound | `-0.01123046875` | failed |
| standardized lower 95% bound | `-0.1777785246` | `>= 0.20`, failed |
| activation predictor correlation | `-0.0802017921` | `>= 0.25`, failed |
| activation predictor sign agreement | `0.37890625` | `>= 0.70`, failed |
| activation predictor bootstrap lower 95% | `-0.1513185820` | `>= 0.10`, failed |
| exact-copy mean effect | `0.0` | passed |
| shuffled mean effect | `0.0015869140625` | passed |
| constant mean effect | `-0.004150390625` | passed |
| matched mean effect | `0.0018310546875` | passed |
| repeat ICC/sign stability | `1.0` / `1.0` | passed |
| view-equivalence | passed | passed |
| power simulation | `0.9804` / `0.9216` at ICC `0.10` / `0.30` | passed |

Cross-view state recoverability failed in every tune cell. Balanced accuracy
and lower 95% bounds were:

| Cell | Balanced accuracy | Lower 95% bound |
|---|---:|---:|
| `view_1:plus` | `0.359375` | `0.265625` |
| `view_1:minus` | `0.171875` | `0.109375` |
| `view_2:plus` | `0.3125` | `0.21875` |
| `view_2:minus` | `0.234375` | `0.140625` |

The minimum required lower bound was `0.35`. No layer, wrapper, position,
alpha, threshold, control, predictor, or corpus variation was attempted.

## Lock and retention verification

The runner emitted and digested tune predictions before generating tune effects.
The independent validator verified the event order, configuration-lock digest,
shared panel/qualification/model custody, no assessment output, and aggregate-
only result schema. No raw prompts, token sequences, activations, logits,
generated text, transcripts, credentials, or per-family result arrays were
retained in the measurement roots.

## Final interpretation and next gate

V48 provides a negative local development result for the precise cross-view
causal-state-transport target. It does not justify a positive causal-access,
introspection, or self-modeling claim. Astral should not generate another
parameter variation. Any reopening requires a new separately authorized
scientific rationale with new estimand or independently frozen replication,
new data identity, unchanged controls, explicit power/reliability analysis,
prediction locking, and independent review before any assessment.

# HSAI / Astral FSM Autoresearch Report

## Executive Summary

A leakage-controlled direct-HTTP FSM benchmark and paired retry research loop was implemented and run against the local `openresearchtools/Qwen3.5-4B-GGUF:Q4_K_M` model.

The first two curricula were too difficult. A micro-DFA calibration reached a usable 36–46% exact baseline regime. The initial micro retry run showed that explicit correct next-state information helped, while a less precise localization message did not. A fresh replication with a more precise but still non-corrective localization message produced the desired behavioral precursor:

- Control: 5/55 = 9.09%
- Precise localization: 16/55 = 29.09%
- Corrective: 21/55 = 38.18%
- Sham: 2/55 = 3.64%
- Random correct fact: 4/55 = 7.27%

Precise localization improved exact retry success over both control and sham. This establishes a behavioral prerequisite for testing whether actual neural telemetry can supply useful localization. It does **not** yet establish that the localization signal came from internal neural telemetry.

## Experimental Architecture

- Deterministic case generator creates actor-visible FSM specifications only.
- Actor calls use direct stateless HTTP to `http://127.0.0.1:8080/v1/chat/completions`.
- The actor receives no repository, memory, tools, oracle, evaluator, or previous session context.
- Full request and raw HTTP response are persisted before evaluation.
- Oracle and evaluator run only after raw persistence.
- Retry arms use fresh direct requests with the same case and frozen failed answer.
- The served model is recorded as `openresearchtools/Qwen3.5-4B-GGUF:Q4_K_M`.
- Generation uses temperature 0, `max_tokens=1024`, and `enable_thinking=false`.

## Baseline Calibration

### Initial curriculum

Run: `runs/2026-08-10-baseline-v1`

- Exact accuracy: 0%
- Mean state accuracy: 2.44%
- 100 successful HTTP calls

### Easier unseen curriculum

Run: `runs/2026-08-10-easy-v1`

- Exact accuracy: 3%
- Mean state accuracy: 49.18%
- 100 successful HTTP calls

### Micro replication 1

Run: `runs/2026-08-10-micro-v1`

- Exact accuracy: 36%
- Natural failures: 64
- Mean state accuracy: 75.05%

The first retry on this set showed corrective feedback helping, but the initial localization wording did not:

- Control: 7.81%
- Localize: 6.25%
- Corrective: 42.19%
- Sham: 4.69%
- Random correct fact: 3.70%

### Micro replication 2

Run: `runs/2026-08-10-micro-replication-v1`

- Exact accuracy: 46%
- Natural failures: 54
- Mean state accuracy: 79.02%

The pattern replicated:

- Control: 11.11%
- Localize: 9.26%
- Corrective: 33.33%
- Sham: 0%
- Random correct fact: 3.70%

### Short and intermediate calibration

Runs:

- `runs/2026-08-10-short-v1`: 23% exact, below the retry threshold
- `runs/2026-08-10-intermediate-v1`: 6% exact, too difficult

These runs were preserved and not used for retry inference.

## Behavioral Localization Experiment

Run: `runs/2026-08-10-micro-localize-v2`

The baseline contained 55 natural failures from 100 fresh cases. The revised `localize` message disclosed:

- first-divergence position
- input symbol at that transition
- state immediately before the transition
- model-reported next state

It withheld the correct next state. This differs from the corrective arm, which explicitly supplies the correct next state.

| Condition | Exact successes | Accuracy |
|---|---:|---:|
| Control | 5 / 55 | 9.09% |
| Precise Localize | 16 / 55 | 29.09% |
| Corrective | 21 / 55 | 38.18% |
| Sham | 2 / 55 | 3.64% |
| Random correct fact | 4 / 55 | 7.27% |

## Statistics

Deterministic paired bootstrap used seed `20260810` and 10,000 resamples.

| Effect | Estimate | Bootstrap 95% CI |
|---|---:|---:|
| Localize − Control | **+20.00 pp** | [+9.09, +32.73] pp |
| Localize − Sham | **+25.45 pp** | [+14.55, +36.36] pp |
| Corrective − Control | **+29.09 pp** | [+16.36, +43.64] pp |
| Corrective − Localize | +9.09 pp | [0, +18.18] pp |
| Random fact − Control | −1.82 pp | not included in primary table |

Paired McNemar-style comparisons:

- Localize vs Control: 12 localize-only, 1 control-only, two-sided p = 0.00342
- Localize vs Sham: 14 localize-only, 0 sham-only, two-sided p = 0.000122
- Corrective vs Control: 18 corrective-only, 2 control-only, two-sided p = 0.000402
- Random fact vs Control: 2 random-fact-only, 3 control-only, two-sided p = 1.0

## Scientific Interpretation

The strongest current behavioral conclusion is:

> On fresh short-horizon DFA cases, truthful precise localization of the model's first divergence improved exact retry success over generic retry and matched sham feedback, even without revealing the correct next state.

The random-correct-fact control did not improve over control, reducing the explanation that any true structured information is sufficient.

Corrective feedback remained stronger than localization, indicating additional value in supplying the correct next state.

This still does **not** demonstrate:

- Neural telemetry
- Mechanistic Astral evidence
- Introspection
- Self-modeling
- Consciousness
- General HSAI capability
- Transfer beyond this model, prompt, and synthetic task

The result is now sufficient to motivate the next research object: replace the synthetic evaluator's localization message with a localization signal derived from a separate neural telemetry pipeline, while preserving the same direct actor interface and paired controls.

## Threats to Validity

- The behavioral localization result uses very short three-state DFAs.
- Retry cases are selected conditional on baseline failure.
- Only one local model and one decoding configuration were used.
- Responses are mostly recoverable Markdown JSON rather than strict JSON.
- The sham is synthetic and should be strengthened in replication.
- Precise localization includes the model's reported next state, although not the correct state.
- Prompt wording and disabled thinking may affect results.
- Behavioral localization is not evidence that a model internally represented or diagnosed its own computation.

## Artifacts

- `generate_cases.py`
- `actor_client.py`
- `oracle.py`
- `evaluate.py`
- `run_baseline.py`
- `analyze_baseline.py`
- `freeze_failures.py`
- `retry_experiment.py`
- `analyze_retry.py`
- `tests/test_fsm_benchmark.py`
- `runs/2026-08-10-micro-localize-v2/`
- `runs/2026-08-10-micro-replication-v1/`
- `runs/2026-08-10-micro-v1/`
- `reports/baseline_summary.json`
- `retry/analysis.json`
- `RESEARCH_LOG.md`

Canonical deterministic suite:

```bash
pytest -q experiments/astral_fsm/tests
```

## Next Experiments

1. Freeze the precise-localization message and replicate it on a new case-generation seed.
2. Strengthen the sham to match position, state, symbol, and message length while remaining false.
3. Test the effect on a longer calibrated horizon without changing the actor/evaluator boundary.
4. Build a separate small subject-model telemetry pipeline that predicts first-divergence location from hidden activations.
5. Lock telemetry predictions before exposing any corrective effect information.
6. Compare synthetic localization, telemetry localization, corrective feedback, control, and sham on identical fresh cases.
7. Require behavioral replication plus telemetry-vs-synthetic comparison before making any mechanistic Astral claim.

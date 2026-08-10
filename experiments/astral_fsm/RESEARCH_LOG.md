# Research Log - FSM Benchmark Experiment

**Session:** 2026-08-07
**Model:** Qwen3.5-4B-GGUF:Q4_K_M (on llama.cpp:8080)
**Status:** Phase 0 Complete (Audit Done)

---

## 2026-08-07 14:40 - Phase 0: Audit Complete

**Hypothesis:** Existing FSM benchmark infrastructure contains contaminated/experimental code that must be replaced with a clean, leakage-free architecture.

**Action:** Audited existing files:
- `cases.jsonl` - Empty (only header line), contains contaminated `001011` case
- `benchmark.py` - Exists but uses `Qwen3-4B` model name (actual model is `Qwen3.5-4B`)
- `fsm_oracle.py` - Clean, standalone oracle (32 lines)
- `README.md` - Documentation exists but needs cleanup

**Result:**
- Contaminated case `001011` must be retired from benchmark (answer appears in conversation history)
- `benchmark.py` model name mismatch: uses `Qwen3-4B-Q4_K_M.gguf` but server reports `openresearchtools/Qwen3.5-4B-GGUF:Q4_K_M`
- Clean directory structure created:
  - `experiments/astral_fsm/archive/` - Contaminated work
  - `experiments/astral_fsm/runs/2026-08-07/raw/` - Immutable run archives
  - `experiments/astral_fsm/runs/2026-08-07/results/` - Aggregated metrics
  - `experiments/astral_fsm/reports/` - Analysis outputs
  - `experiments/astral_fsm/cases/stage1/` - Stage 1 cases
  - `experiments/astral_fsm/cases/stage2/` - Stage 2 cases
  - `experiments/astral_fsm/cases/stage3/` - Stage 3 cases

**Interpretation:** Need to implement clean architecture from scratch with corrected model name.

**Decision:** Proceed to Phase 1 with clean implementation.

**Next Decision Point:** Implement case generator, actor client, oracle, and evaluator.

---

## 2026-08-10 - Baseline Attempt Blocked by Endpoint

**Action:** Generated 100 cases and launched the direct stateless baseline runner.

**Result:** All 100 requests were persisted, but each failed with `ConnectionRefusedError(61, 'Connection refused')` against `127.0.0.1:8080`. The endpoint was confirmed unavailable after the run.

**Interpretation:** This is an infrastructure failure, not a natural model failure. No accuracy, JSON, or retry conclusions are valid. The run is preserved for audit and must not be included in scientific baseline statistics.

**Decision:** Stop before Experiment 2. Resume only after llama.cpp is started and `/v1/models` confirms the exact served model.

---

## 2026-08-10 - Baseline Calibration and Retry Result

**Action:** Ran the initial, easier, and final micro-DFA unseen baselines. The micro profile reached 36% exact accuracy with 64 natural failures. Frozen those failures and ran 256 paired retry calls across control, localize, corrective, and sham conditions.

**Result:** Control 5/64, localize 4/64, corrective 27/64, sham 3/64. Corrective-minus-control was +34.38 percentage points; localize-minus-control was -1.56 points; localize-minus-sham was +1.56 points.

**Interpretation:** Correct next-state information improved behavioral retry success in this narrow micro-DFA setting. Localization alone did not improve over generic retry or sham. This is not neural telemetry or mechanistic evidence.

**Decision:** Preserve the result as a behavioral precursor. Do not advance to real Astral telemetry or claim localization benefit without a fresh replication and stronger controls.

---

## 2026-08-10 - Precise Localization Effect Found

**Action:** Ran a fresh micro-DFA baseline at case offset 6000 and a five-arm retry experiment with a precise localization message that disclosed divergence position, input symbol, prior state, and reported next state while withholding the correct next state.

**Result:** Baseline exact accuracy was 45% with 55 natural failures. Retry accuracy was control 9.09%, precise localize 29.09%, corrective 38.18%, sham 3.64%, and random correct fact 7.27%. Localize-minus-control was +20.00 percentage points (bootstrap 95% CI [+9.09, +32.73]); paired McNemar p=0.00342. Localize-minus-sham was +25.45 points, p=0.000122.

**Interpretation:** Precise synthetic localization itself now improves behavioral self-correction over generic and sham feedback in this narrow setting. Corrective feedback remains stronger. This is a behavioral prerequisite, not neural telemetry or mechanistic evidence.

**Decision:** Freeze this message and move to a separate telemetry-localization design. Require fresh replication, stronger sham matching, prediction locking, and telemetry-vs-synthetic comparison before any Astral claim.

---

## [Pending] Phase 1: Clean Case Generator
**Hypothesis:** Deterministic case generation will produce useful diversity across curriculum stages.

## [Pending] Phase 2: Stateless Actor Client
**Hypothesis:** Direct llama.cpp API calls will provide clean, leakage-free inference.

## [Pending] Phase 3: Oracle & Evaluator
**Hypothesis:** Ground-truth oracle and metrics evaluation will accurately assess model performance.

## [Pending] Phase 4: 100-Case Baseline
**Hypothesis:** Baseline exact accuracy will fall in 40-80% range (natural failures).

## [Pending] Phase 5: Freeze Failed Cases
**Hypothesis:** Failed cases will be identifiable and can be frozen for retry experiment.

## [Pending] Phase 6: Retry Experiment
**Hypothesis:** Astral-localize feedback will outperform control and sham conditions.

## [Pending] Phase 7: Retry Metrics
**Hypothesis:** Paired statistical tests will show significant effects.

## [Pending] Phase 8: Error Analysis
**Hypothesis:** Failure patterns will be identifiable and actionable.

## [Pending] Phase 9: FST Extension
**Hypothesis:** If DFA is too easy, Finite-State Transducer benchmark will be warranted.

## [Pending] Phase 10: Bridge to Real Astral
**Hypothesis:** Behavioral results will inform design for neural telemetry experiments.

---

**Research Objective:** Determine if precise diagnostic feedback improves model self-correction beyond generic retry and sham feedback.

**Primary Metrics:**
- Baseline exact accuracy (target: 40-80%)
- $\Delta_{\text{HSAI-localize}} = P(\text{success}|\text{localize}) - P(\text{success}|\text{control})$
- $P(\text{success}|\text{localize})$ vs $P(\text{success}|\text{sham})$

**Key Deliverable:** `experiments/astral_fsm/AUTORESEARCH_REPORT.md`

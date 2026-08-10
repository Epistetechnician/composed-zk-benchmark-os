# FSM Benchmark Experiment

## Canonical verification

Run the deterministic canonical suite from the repository root:

```bash
pytest -q experiments/astral_fsm/tests
```

The suite covers deterministic case generation, actor-prompt isolation, request bounds, oracle trajectories, strict/recoverable JSON parsing, exact evaluation, divergence localization, and missing-response handling. Live inference is intentionally separate because it depends on the local llama.cpp service.

## Experiment 0B (Completed)
- **Status:** PASSED ✅
- **Case:** `001011` with 3-state FSM
- **Result:** Qwen3-4B solved correctly
- **Note:** This case is RETIRED from the benchmark due to answer leakage in conversation history

---

# Experiment 1 (In Progress)
**Goal:** 100 fresh, unseen FSM cases with stateless actor inference

## Architecture
```
┌─────────────────────────────────────────────────────────┐
│                    HERMES (Orchestrator)                │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│             DIRECT QWEN API (Stateless Actor)           │
│     http://127.0.0.1:8080/v1/chat/completions           │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                 ORACLE (Ground Truth)                    │
│              fsm_oracle.py (read-only)                   │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              EVALUATOR (Metrics Collection)              │
└─────────────────────────────────────────────────────────┘
```

**Key Constraints:**
- Actor calls llama.cpp directly, NOT via Hermes
- Actor receives NO oracle, NO repo access, NO tools, NO memory
- Each actor call is a fresh stateless HTTP request
- Raw response saved IMMEDIATELY before oracle evaluation

---

## File Tree Structure
```
experiments/astral_fsm/
├── README.md                    # This file
├── cases.jsonl                  # 100 case definitions (stage, input)
├── oracle.py                    # FSM oracle computation
├── evaluate.py                  # Metrics computation
├── runs/                        # Immutable run archives
│   ├── 2026-08-07/
│   │   ├── raw_responses.jsonl # Raw API responses
│   │   └── results.json        # Aggregated metrics
└── config.yaml                  # Experiment configuration

tools/astral-fsm-benchmark/
└── benchmark.py                 # Main orchestration script
```

---

## Case Generator (Curriculum)
**Stage 1:** 3-5 states, 20-40 symbols (25 cases)
**Stage 2:** 5-8 states, 50-100 symbols (40 cases)
**Stage 3:** 8-12 states, 100-200 symbols (35 cases)

---

## Request Schema (Actor API)
```json
{
  "model": "Qwen3-4B-Q4_K_M.gguf",
  "temperature": 0,
  "messages": [
    {
      "role": "system",
      "content": "Solve the deterministic finite-state machine. Return only valid JSON matching the requested schema."
    },
    {
      "role": "user",
      "content": {
        "states": ["A", "B", "C"],
        "alphabet": ["0", "1"],
        "start": "A",
        "accept": ["B"],
        "transitions": {
          "A": {"0": "B", "1": "A"},
          "B": {"0": "C", "1": "A"},
          "C": {"0": "C", "1": "B"}
        },
        "input": "001011"
      }
    }
  ]
}
```

---

## Raw Run Schema
```json
{
  "case_id": 1,
  "stage": 1,
  "input": "001011",
  "model": "Qwen3-4B-Q4_K_M.gguf",
  "endpoint": "http://127.0.0.1:8080/v1/chat/completions",
  "temperature": 0,
  "prompt_sha256": "...",
  "response": {
    "choices": [
      {
        "message": {
          "role": "assistant",
          "content": "{\n  \"trajectory\": [...],\n  \"final_state\": \"...\",\n  \"accepted\": false\n}"
        }
      }
    ],
    "usage": {
      "prompt_tokens": 123,
      "completion_tokens": 45,
      "total_tokens": 168
    }
  },
  "latency_ms": 1234,
  "timestamp": "2026-08-07T12:00:00.000Z",
  "raw_response": "{...}"  // Full HTTP response for audit
}
```

---

## Evaluator Schema
```json
{
  "case_id": 1,
  "oracle_answer": {
    "trajectory": ["A", "B", "C", "B", "C", "B", "A"],
    "final_state": "A",
    "accepted": false
  },
  "actor_response": {
    "trajectory": ["A", "B", "C", "B", "C", "B", "A"],
    "final_state": "A",
    "accepted": false
  },
  "valid_json": true,
  "trajectory_length_match": true,
  "trajectory_exact": true,
  "final_state_exact": true,
  "accepted_exact": true,
  "overall_exact": true,
  "per_state_accuracy": {
    "A": 1.0,
    "B": 1.0,
    "C": 1.0
  },
  "first_divergence_index": null,
  "expected_state_at_divergence": null,
  "reported_state_at_divergence": null,
  "stage": 1,
  "input_length": 6
}
```

---

## Example Case (WITHOUT Oracle Answer)

### Case ID: 1
**Stage:** 1 (3-5 states, 20-40 symbols)

**FSM Specification:**
- **States:** A, B, C
- **Alphabet:** {0, 1}
- **Start State:** A
- **Accepting States:** {C}
- **Transitions:**
  - A + 0 → B
  - A + 1 → A
  - B + 0 → C
  - B + 1 → A
  - C + 0 → C
  - C + 1 → B
- **Input:** 001011

**Question:** What is the trajectory, final state, and acceptance status?

**Schema:**
```json
{
  "trajectory": [...],
  "final_state": "...",
  "accepted": false
}
```

**Note:** Do NOT reveal the oracle answer. The actor must compute this independently.

---

## Next Steps
1. Generate 100 cases per the curriculum
2. Run each case through the direct Qwen API
3. Save raw responses to immutable archives
4. Evaluate against oracle
5. Report aggregate metrics

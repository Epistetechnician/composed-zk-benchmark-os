#!/usr/bin/env python3
"""
FSM Benchmark Experiment - Experiment 1

Runs 100 fresh, unseen FSM cases against Qwen3-4B via direct llama.cpp API.
Each actor call is stateless with NO oracle, NO memory, NO tools.

Architecture:
    Hermes (orchestrator)
         │
         ▼
    Direct Qwen API (llama.cpp:8080) - STATELESS
         │
         ▼
    Oracle (ground truth) - NEVER seen by actor
         │
         ▼
    Evaluator (metrics)
"""
import json
import hashlib
import requests
import time
import re
from pathlib import Path
from datetime import datetime
import argparse


# ============================================================================
# CASE GENERATOR (Curriculum)
# ============================================================================

class FSMCase:
    """A deterministic FSM case for benchmarking."""

    def __init__(self, case_id, stage):
        self.case_id = case_id
        self.stage = stage
        self.states = []
        self.alphabet = ["0", "1"]
        self.start = "A"
        self.accept = ["C"]
        self.transitions = {}
        self.input = ""

    def generate(self, num_states, input_len):
        """Generate states and transitions deterministically."""
        # States
        self.states = [chr(ord('A') + i) for i in range(num_states)]
        self.start = self.states[0]

        # Accept state (cycle through A, B, C based on case_id)
        accept_idx = self.case_id % 3
        self.accept = [self.states[accept_idx]]

        # Transitions (deterministic based on state + input symbol)
        for s in self.states:
            self.transitions[s] = {}
            for sym in ["0", "1"]:
                # Deterministic next state using hash (produces 0-255)
                val = int(hashlib.md5(f"state{self.case_id}state{s}{sym}".encode()).hexdigest(), 16) % 3
                next_idx = val % len(self.states)
                self.transitions[s][sym] = self.states[next_idx]

        # Generate input string
        self.input = ""
        for i in range(input_len):
            # Use hash that produces only 0/1
            val = int(hashlib.md5(f"case{self.case_id}stage{self.stage}sym{i}".encode()).hexdigest(), 16) % 2
            self.input += str(val)

        # Ensure input doesn't exceed length
        self.input = self.input[:input_len]

        return self

    def to_prompt(self, model="Qwen3-4B-Q4_K_M.gguf", temperature=0):
        """Generate a prompt for the direct API call (stateless actor)."""
        transitions_str = ""
        for s in self.states:
            for sym in ["0", "1"]:
                next_s = self.transitions[s][sym]
                transitions_str += f"{s}+{sym}->{next_s}, "

        prompt = f"""Solve the deterministic finite-state machine. Return only valid JSON matching this schema:
{{
  "trajectory": ["{self.start}", ...],
  "final_state": "...",
  "accepted": true|false
}}

States: {", ".join(self.states)}
Alphabet: {", ".join(self.alphabet)}
Start: {self.start}
Accept: {", ".join(self.accept)}
Transitions:
{transitions_str}
Input: {self.input}
"""
        return prompt


def generate_cases(num_cases=100):
    """Generate cases across the three stages."""
    cases = []

    # Stage 1: 25 cases (3-5 states, 20-40 symbols)
    for i in range(25):
        num_states = 3 + (i % 3)
        input_len = 20 + (i % 10) * 3
        cases.append(FSMCase(case_id=i+1, stage=1).generate(num_states, input_len))

    # Stage 2: 40 cases (5-8 states, 50-100 symbols)
    for i in range(40):
        num_states = 5 + (i % 4)
        input_len = 50 + (i % 30) * 2
        cases.append(FSMCase(case_id=i+26, stage=2).generate(num_states, input_len))

    # Stage 3: 35 cases (8-12 states, 100-200 symbols)
    for i in range(35):
        num_states = 8 + (i % 5)
        input_len = 100 + (i % 100)
        cases.append(FSMCase(case_id=i+66, stage=3).generate(num_states, input_len))

    return cases


# ============================================================================
# DIRECT API CALL (Stateless Actor)
# ============================================================================

API_ENDPOINT = "http://127.0.0.1:8080/v1/chat/completions"


def call_direct_api(prompt_content, model="Qwen3-4B-Q4_K_M.gguf", temperature=0):
    """Make a stateless direct API call to llama.cpp."""
    payload = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {
                "role": "system",
                "content": "Solve the deterministic finite-state machine. Return only valid JSON matching the requested schema."
            },
            {
                "role": "user",
                "content": prompt_content
            }
        ]
    }

    try:
        response = requests.post(
            API_ENDPOINT,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            return None, f"API call failed: HTTP {response.status_code} - {response.text}"

        try:
            result = response.json()
            return result, ""
        except json.JSONDecodeError as e:
            return None, f"Failed to parse API response: {e}"
    except requests.exceptions.Timeout:
        return None, "API call timed out"
    except requests.exceptions.RequestException as e:
        return None, f"Request error: {e}"
    except Exception as e:
        return None, f"Unexpected error: {e}"


# ============================================================================
# ORACLE (Ground Truth)
# ============================================================================

def compute_oracle_answer(case):
    """Compute the ground truth answer for a case."""
    state = case.start
    trajectory = [state]

    for sym in case.input:
        state = case.transitions[state][sym]
        trajectory.append(state)

    return {
        "trajectory": trajectory,
        "final_state": state,
        "accepted": state in case.accept
    }


# ============================================================================
# EVALUATOR (Metrics)
# ============================================================================

def extract_json_from_response(content):
    """Extract JSON from model response (handles markdown code blocks)."""
    match = re.search(r'\`\`\`json\s*\n(.*?)\n\`\`\`', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError as e:
            return None
    return None


def normalize_trajectory(trajectory):
    """Normalize trajectory to uppercase letters."""
    return [s.upper() if isinstance(s, str) else s for s in trajectory]


def evaluate_case(case, api_response, oracle_answer):
    """Evaluate actor response against oracle."""
    # Extract actor's JSON
    raw_content = api_response.get("choices", [{}])[0].get("message", {}).get("content", "")
    actor_answer = extract_json_from_response(raw_content)

    valid_json = actor_answer is not None

    if not valid_json:
        return {
            "case_id": case.case_id,
            "stage": case.stage,
            "input": case.input,
            "valid_json": False,
            "error": "Invalid JSON from actor"
        }

    # Normalize trajectories
    expected_traj = normalize_trajectory(oracle_answer["trajectory"])
    reported_traj = normalize_trajectory(actor_answer["trajectory"])

    # Check exact match
    trajectory_exact = expected_traj == reported_traj
    final_state_exact = oracle_answer["final_state"] == actor_answer["final_state"]
    accepted_exact = oracle_answer["accepted"] == actor_answer["accepted"]

    overall_exact = trajectory_exact and final_state_exact and accepted_exact

    return {
        "case_id": case.case_id,
        "stage": case.stage,
        "input": case.input,
        "valid_json": valid_json,
        "trajectory_length_match": len(expected_traj) == len(reported_traj),
        "trajectory_exact": trajectory_exact,
        "final_state_exact": final_state_exact,
        "accepted_exact": accepted_exact,
        "overall_exact": overall_exact,
        "error": None
    }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="FSM Benchmark Experiment 1")
    parser.add_argument("--cases", type=int, default=100, help="Number of cases to run")
    parser.add_argument("--output-dir", type=str, default="experiments/astral_fsm/runs/2026-08-07",
                        help="Output directory for results")
    parser.add_argument("--model", type=str, default="Qwen3-4B-Q4_K_M.gguf",
                        help="Model to use")
    parser.add_argument("--temperature", type=float, default=0,
                        help="Temperature for API calls")
    args = parser.parse_args()

    print("=" * 60)
    print("FSM Benchmark Experiment 1")
    print("=" * 60)
    print(f"Model: {args.model}")
    print(f"Temperature: {args.temperature}")
    print(f"Cases: {args.cases}")
    print(f"Output: {args.output_dir}")
    print("=" * 60)

    # Generate cases
    print("\n[1/4] Generating benchmark cases...")
    cases = generate_cases(args.cases)
    print(f"Generated {len(cases)} cases")

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run all cases
    print("\n[2/4] Running cases through direct Qwen API...")
    start_time = time.time()

    results = []

    for case in cases:
        # Call direct API (stateless)
        api_response, error = call_direct_api(case.to_prompt(), args.model, args.temperature)

        if error:
            print(f"  Case {case.case_id}: {error}")
            results.append({
                "case_id": case.case_id,
                "stage": case.stage,
                "input": case.input,
                "valid_json": False,
                "error": error
            })
            continue

        # Evaluate against oracle
        oracle = compute_oracle_answer(case)
        eval_result = evaluate_case(case, api_response, oracle)
        eval_result["raw_response"] = api_response

        results.append(eval_result)

        if case.case_id % 10 == 0:
            elapsed = time.time() - start_time
            print(f"  Completed {case.case_id}/{len(cases)} cases ({elapsed:.1f}s)")

    elapsed = time.time() - start_time

    # Compute metrics
    print("\n[3/4] Computing aggregate metrics...")
    total = len(results)
    exact_count = sum(1 for r in results if r["overall_exact"])
    valid_json_count = sum(1 for r in results if r["valid_json"])

    # Per-stage metrics
    stage_metrics = {}
    for stage in [1, 2, 3]:
        stage_results = [r for r in results if r["stage"] == stage]
        if stage_results:
            stage_metrics[stage] = {
                "total": len(stage_results),
                "exact": sum(1 for r in stage_results if r["overall_exact"]),
                "valid_json": sum(1 for r in stage_results if r["valid_json"])
            }

    metrics = {
        "total_cases": total,
        "exact_accuracy": exact_count / total,
        "valid_json_rate": valid_json_count / total,
        "per_stage": stage_metrics,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    # Save results
    results_file = output_dir / "results.json"
    with open(results_file, "w") as f:
        json.dump(metrics, f, indent=2)

    # Save raw responses
    raw_dir = output_dir / "raw_responses"
    raw_dir.mkdir(exist_ok=True)

    raw_file = raw_dir / "runs.jsonl"
    with open(raw_file, "w") as f:
        for result in results:
            f.write(f"{json.dumps(result)}\n")

    print(f"\nResults saved to: {results_file}")
    print(f"Raw responses saved to: {raw_file}")

    # Print summary
    print("\n" + "=" * 60)
    print("EXPERIMENT 1 SUMMARY")
    print("=" * 60)
    print(f"Total cases: {metrics['total_cases']}")
    print(f"Exact accuracy: {metrics['exact_accuracy']:.2%}")
    print(f"Valid JSON rate: {metrics['valid_json_rate']:.2%}")
    print(f"\nPer-stage accuracy:")
    for stage, m in metrics['per_stage'].items():
        acc = m['exact'] / m['total'] if m['total'] > 0 else 0
        print(f"  Stage {stage}: {acc:.2%}")
    print(f"\nElapsed time: {elapsed:.1f}s")
    print("=" * 60)

    return metrics


if __name__ == "__main__":
    main()

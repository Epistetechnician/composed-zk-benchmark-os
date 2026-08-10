#!/usr/bin/env python3
"""FSM Case Generator - Experiment 1"""
import hashlib
import json
from pathlib import Path

def generate_deterministic_fsm(case_id, stage, num_states, input_len):
    states = [chr(ord('A') + i) for i in range(num_states)]
    start_state = states[0]
    accept_idx = case_id % num_states
    accepting_states = [states[accept_idx]]

    transitions = {}
    for s in states:
        transitions[s] = {}
        for sym in ["0", "1"]:
            hash_input = f"{s}{case_id}{sym}"
            val = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
            next_idx = val % num_states
            transitions[s][sym] = states[next_idx]

    input_str = ""
    for i in range(input_len):
        hash_input = f"{case_id}stage{stage}sym{i}"
        val = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        input_str += str((val >> 1) & 1)

    input_str = input_str[:input_len]

    return {
        "case_id": case_id, "stage": stage, "states": states,
        "alphabet": ["0", "1"], "start": start_state,
        "accepting": accepting_states, "transitions": transitions,
        "input": input_str
    }

def generate_cases(num_cases=100, profile="initial", case_offset=0):
    if profile == "short":
        return [generate_deterministic_fsm(case_offset + i + 1, 1, 3, 4 + (i % 3)) for i in range(num_cases)]

    if profile == "intermediate":
        return [generate_deterministic_fsm(case_offset + i + 1, 1, 3, 6 + (i % 5)) for i in range(num_cases)]

    if profile == "micro":
        return [generate_deterministic_fsm(case_offset + i + 1, 1, 3, 2 + (i % 4)) for i in range(num_cases)]

    if profile == "easy":
        cases = []
        for i in range(num_cases):
            if i < 50:
                stage, num_states, input_len = 1, 3 + (i % 2), 6 + (i % 5)
            elif i < 80:
                stage, num_states, input_len = 2, 3 + (i % 3), 10 + (i % 7)
            else:
                stage, num_states, input_len = 3, 4 + (i % 3), 16 + (i % 10)
            cases.append(generate_deterministic_fsm(case_offset + i + 1, stage, num_states, input_len))
        return cases

    all_cases = []

    # Stage 1: 25 cases
    for i in range(25):
        num_states = 3 + (i % 3)
        input_len = 20 + (i % 10) * 3
        case = generate_deterministic_fsm(case_id=case_offset+i+1, stage=1, num_states=num_states, input_len=input_len)
        all_cases.append(case)

    # Stage 2: 40 cases
    for i in range(40):
        num_states = 5 + (i % 4)
        input_len = 50 + (i % 30) * 2
        case = generate_deterministic_fsm(case_id=case_offset+i+26, stage=2, num_states=num_states, input_len=input_len)
        all_cases.append(case)

    # Stage 3: 35 cases
    for i in range(35):
        num_states = 8 + (i % 5)
        input_len = 100 + (i % 100)
        case = generate_deterministic_fsm(case_id=case_offset+i+66, stage=3, num_states=num_states, input_len=input_len)
        all_cases.append(case)

    return all_cases

def case_to_prompt(case):
    prompt = f"""Solve the deterministic finite-state machine.

States: {case['states']}
Alphabet: {', '.join(case['alphabet'])}
Start State: {case['start']}
Accepting States: {', '.join(case['accepting'])}
Transitions: {json.dumps(case['transitions'])}
Input: {case['input']}

Return JSON: {{"trajectory": [...], "final_state": "...", "accepted": ...}}
"""
    return prompt

if __name__ == "__main__":
    import sys
    num_cases = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    profile = sys.argv[2] if len(sys.argv) > 2 else "initial"
    print(f"Generating {num_cases} FSM cases...")
    cases = generate_cases(num_cases, profile=profile, case_offset=1000 if profile == "easy" else 0)

    for stage in [1, 2, 3]:
        stage_cases = [c for c in cases if c['stage'] == stage]
        stage_dir = Path(f"experiments/astral_fsm/cases/stage{stage}")
        stage_dir.mkdir(parents=True, exist_ok=True)

        manifest_file = stage_dir / f"manifest.json"
        with open(manifest_file, "w") as f:
            json.dump([c for c in stage_cases], f, indent=2)

        for case in stage_cases:
            case_file = stage_dir / f"case_{case['case_id']}.json"
            with open(case_file, "w") as f:
                json.dump(case, f, indent=2)

        print(f"  Stage {stage}: {len(stage_cases)} cases")

    with open("experiments/astral_fsm/cases/manifest_all.json", "w") as f:
        json.dump(cases, f, indent=2)

    print(f"\nTotal: {len(cases)} cases generated")

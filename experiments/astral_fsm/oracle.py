#!/usr/bin/env python3
"""Pure deterministic FSM oracle; never imported by actor code."""

def run(case):
    state = case["start"]
    trajectory = [state]
    for symbol in case["input"]:
        state = case["transitions"][state][symbol]
        trajectory.append(state)
    return {"trajectory":trajectory,"final_state":state,"accepted":state in case["accepting"]}

import json

TRANSITIONS = {
    "A": {"0": "B", "1": "A"},
    "B": {"0": "C", "1": "A"},
    "C": {"0": "C", "1": "B"}
}

START = "A"
ACCEPT = {"C"}

INPUT = "001011"


def run_fsm(text: str):
    state = START
    trajectory = [state]

    for symbol in text:
        state = TRANSITIONS[state][symbol]
        trajectory.append(state)

    return {
        "trajectory": trajectory,
        "final_state": state,
        "accepted": state in ACCEPT,
    }


if __name__ == "__main__":
    print(json.dumps(run_fsm(INPUT), indent=2))

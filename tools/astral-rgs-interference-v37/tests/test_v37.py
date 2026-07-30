import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("v37_test", ROOT / "v37.py")
assert SPEC and SPEC.loader
V37 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = V37
SPEC.loader.exec_module(V37)


def rows(correct: int, total: int = 8) -> list[dict[str, bool]]:
    return [{"correct": index < correct} for index in range(total)]


def cell(arm: str, seed: int, order_id: str, retained: int) -> dict:
    order = V37.PROTOCOL["orders"][order_id]
    stages = []
    for stage, task_id in enumerate(order, start=1):
        direct = {seen_id: rows(8) for seen_id in order[:stage]}
        if stage == 4:
            direct.update({seen_id: rows(retained) for seen_id in order[:-1]})
        stages.append({"stage": stage, "direct": direct})
    return {
        "arm_id": arm,
        "seed": seed,
        "order_id": order_id,
        "task_order": order,
        "stage_evaluations": stages,
        "final_paraphrase": {task_id: rows(retained if task_id != order[-1] else 8) for task_id in order},
        "protected_after_final": rows(32, 32),
        "reload_max_score_delta": 0,
        "update_tokens": 49152,
        "loss_trace": [{"loss": 1} for _ in range(128)],
    }


def test_fixture_and_useful_difficulty_summary() -> None:
    assert len(V37.fixture()["tasks"]) == 4
    retained = {"no_task_replay": 4, "recent_replay_25": 6, "reservoir_replay_25": 7}
    cells = [
        cell(arm, seed, order_id, retained[arm])
        for arm in V37.PROTOCOL["arms"]
        for seed in V37.PROTOCOL["seeds"]
        for order_id in V37.PROTOCOL["orders"]
    ]
    assert V37.summary(cells)["status"] == "InterferenceStreamQualified"

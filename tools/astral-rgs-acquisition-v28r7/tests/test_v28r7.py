from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v28r7_tested", ROOT / "v28r7.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_expected_family_is_deterministic_and_closed_book() -> None:
    seed = bytes(range(32))
    left = MODULE.expected_family(seed, "nonce_fact", 0)
    right = MODULE.expected_family(seed, "nonce_fact", 0)
    assert left == right
    assert MODULE.stable_hash(left) == "sha256:159da3d49381ad7423fd0cdd26680a80c2ab132eb694b25003b4d4733d318a25"
    assert left["family_id"] == "r7family-6a42481ad60bbe0d4a21f160"
    assert len(left["queries"]) == 12
    assert all(left["source_document"] not in row["prompt"] for row in left["queries"])
    assert {row["expected_label"] for row in left["queries"]} == {"A", "B", "C", "D"}


def test_panel_selector_is_seed_bound_complete_and_deterministic() -> None:
    seed = bytes(range(32))
    selected = MODULE.panel_indices(seed)
    assert selected == MODULE.panel_indices(seed)
    assert selected == [1, 14, 16, 17, 36, 54, 59, 63]
    assert len(selected) == 8
    assert selected == sorted(set(selected))
    assert all(0 <= value < 64 for value in selected)


def test_evaluation_panel_uses_balanced_block_order() -> None:
    families = [
        {"block_index": block, "fact_kind": kind, "family_in_block": position, "family_id": f"{kind}-{block}-{position}"}
        for kind in reversed(MODULE.FACT_KINDS) for block in (1, 2) for position in (1, 0)
    ]
    ordered = MODULE.evaluation_panel(families, [1, 2])
    assert [(row["block_index"], row["fact_kind"], row["family_in_block"]) for row in ordered] == [
        (block, kind, position)
        for block in (1, 2) for kind in MODULE.FACT_KINDS for position in (0, 1)
    ]


def test_pilot_metric_rejects_chance_rows() -> None:
    rows = []
    baseline = {}
    for kind in MODULE.FACT_KINDS:
        for ordinal in range(4):
            family_id = f"{kind}-{ordinal}"
            baseline[family_id] = 0.25
            for query_class in MODULE.QUERY_CLASSES:
                rows.extend({
                    "family_id": family_id, "fact_kind": kind,
                    "query_class": query_class, "correct": variant == 0,
                } for variant in range(4))
    metrics = MODULE.pilot_metrics(rows, baseline)
    assert metrics["paired_mean_gain"] == 0.0
    assert metrics["absolute_gates_pass"] is False

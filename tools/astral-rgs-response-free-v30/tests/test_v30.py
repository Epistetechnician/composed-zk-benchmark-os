from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v30_tested", ROOT / "v30.py")
assert SPEC is not None and SPEC.loader is not None
V30 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = V30
SPEC.loader.exec_module(V30)


def test_fixture_is_stable_and_balanced() -> None:
    fixture = V30.expected_fixture()
    assert len(fixture["cases"]) == 32
    assert [sum(case["rung"] == rung for case in fixture["cases"]) for rung in V30.PROTOCOL["rungs"]] == [8, 8, 8, 8]
    assert fixture["fixture_sha256"] == V30.stable_hash({key: value for key, value in fixture.items() if key != "fixture_sha256"})


def test_rederivation_uses_positive_null_and_next_case_shuffle() -> None:
    fixture = V30.expected_fixture()
    evidence = []
    for index, case in enumerate(fixture["cases"]):
        positive = {word: -10.0 for word in V30.WORDS}
        null = {word: -10.0 for word in V30.WORDS}
        positive[case["target"]] = 0.0
        evidence.append({"case_id": case["case_id"], "positive_word_scores": positive, "null_word_scores": null, "positive_greedy_token_id": index, "positive_greedy_decoded": case["target"], "null_greedy_token_id": -1, "null_greedy_decoded": "absent"})
    rows = V30.rederive_observations("qwen_0_5b", evidence, fixture)
    positive = [row for row in rows if row["method"] == "content_likelihood" and row["condition"] == "positive"]
    shuffled = [row for row in rows if row["method"] == "content_likelihood" and row["condition"] == "shuffled"]
    assert all(row["correct"] for row in positive)
    assert all(row["source_case_id"] == row_case["shuffled_source_case_id"] for row, row_case in zip(shuffled, fixture["cases"], strict=True))


def test_summary_selects_simplest_eligible_method() -> None:
    fixture = V30.expected_fixture()
    rows = []
    for model in V30.PROTOCOL["models"]:
        for method in V30.PROTOCOL["methods"]:
            for condition in ("positive", "null", "shuffled"):
                for case in fixture["cases"]:
                    rows.append({"model_id": model, "method": method, "condition": condition, "case_id": case["case_id"], "rung": case["rung"], "correct": condition == "positive", "permutation_invariant": True})
    summary = V30.summarize(rows)
    assert summary["status"] == "DualCheckpointEvaluatorQualified"
    assert all(value["selected_method"] == "content_likelihood" for value in summary["models"].values())

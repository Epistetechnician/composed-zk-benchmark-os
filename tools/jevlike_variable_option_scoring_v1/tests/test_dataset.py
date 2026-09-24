"""Hermetic contract tests for the Jevlike variable-option scoring V1 slice."""

from tools.jevlike_variable_option_scoring_v1.run_experiment import (
    _baseline,
    _example,
    _permuted,
)


def _case():
    return {
        "case_id": 1,
        "states": ["A", "B"],
        "alphabet": ["0", "1"],
        "start": "A",
        "accepting": ["B"],
        "transitions": {"A": {"0": "B", "1": "A"}, "B": {"0": "A", "1": "B"}},
        "input": "01",
    }


def _evaluated(divergence):
    return {
        "case_id": 1,
        "input_length": 2,
        "first_divergence_index": divergence,
        "parsed_response": {"trajectory": ["A", "B", "A"], "final_state": "A", "accepted": False},
    }


def test_example_has_variable_options_and_hidden_divergence_label():
    row = _example(_case(), _evaluated(2), "run-a")
    assert row["options"] == ["no_divergence", "step_1", "step_2"]
    assert row["label"] == 2
    assert "first_divergence" not in row["context"]


def test_permutation_remaps_label_and_preserves_candidate_set():
    row = _example(_case(), _evaluated(1), "run-a")
    permuted = _permuted([row])[0]
    assert sorted(permuted["options"]) == sorted(row["options"])
    assert permuted["options"][permuted["label"]] == row["options"][row["label"]]


def test_baseline_reports_variable_menu_random_expectation():
    rows = [_example(_case(), _evaluated(None), "run-a"), _example(_case(), _evaluated(2), "run-b")]
    baseline = _baseline(rows)
    assert baseline["uniform_random_expected_top1"] == 1 / 3
    assert baseline["uniform_random_expected_top3"] == 1.0

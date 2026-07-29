from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v29_tested", ROOT / "v29.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def fake_observations(passing_format: str | None) -> list[dict[str, object]]:
    rows = []
    for format_id in MODULE.FORMATS:
        for case in MODULE.expected_fixture()["cases"]:
            correct = format_id == passing_format
            expected_index = MODULE.LABELS.index(case["expected_label"])
            predicted_index = expected_index if correct else (expected_index + 1) % 4
            scores = [-4.0, -4.0, -4.0, -4.0]
            scores[predicted_index] = -1.0
            rows.append(
                {
                    "format_id": format_id,
                    "case_id": case["case_id"],
                    "rung": case["rung"],
                    "expected_label": case["expected_label"],
                    "user_prompt_sha256": case["user_prompt_sha256"],
                    "input_token_ids": [1, 2, 3],
                    "input_token_ids_sha256": MODULE.stable_hash([1, 2, 3]),
                    "label_scores": scores,
                    "predicted_label": MODULE.LABELS[predicted_index],
                    "correct": correct,
                }
            )
    return rows


def test_fixture_is_deterministic_and_balanced() -> None:
    fixture = MODULE.expected_fixture()
    assert fixture == MODULE.expected_fixture()
    assert len(fixture["cases"]) == 64
    for rung in MODULE.RUNGS:
        labels = Counter(row["expected_label"] for row in fixture["cases"] if row["rung"] == rung)
        assert labels == Counter({label: 4 for label in MODULE.LABELS})


def test_observation_validator_recomputes_qualified_decision() -> None:
    errors: list[str] = []
    summary = MODULE.validate_observations(fake_observations("chat_template"), errors)
    assert errors == []
    assert summary["status"] == "PositiveControlInstrumentQualified"
    assert summary["selected_format"] == "chat_template"


def test_observation_validator_rejects_score_argmax_tampering() -> None:
    rows = fake_observations("chat_template")
    rows[0]["predicted_label"] = "D"
    errors: list[str] = []
    MODULE.validate_observations(rows, errors)
    assert "observations[0].argmax" in errors


def test_summary_rejects_missing_case() -> None:
    with pytest.raises(ValueError, match="coverage"):
        MODULE.expected_summary(fake_observations(None)[:-1])

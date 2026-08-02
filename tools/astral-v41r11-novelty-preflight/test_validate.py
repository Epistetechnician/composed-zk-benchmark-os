from __future__ import annotations

import importlib.util
from pathlib import Path


PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v41r11_preflight_validator", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def metric_packet(correct: int) -> dict:
    return {
        "overall_accuracy": correct / 96,
        "accuracy_by_class": {key: (correct // 3) / 32 for key in MODULE.QUERY_CLASSES},
        "correct": correct,
        "total": 96,
    }


def test_preflight_pass_and_fail_decisions() -> None:
    passed = MODULE.decision(metric_packet(24), metric_packet(96))
    assert passed == ("NoveltyPreflightPassed", [])
    failed, errors = MODULE.decision(metric_packet(48), metric_packet(60))
    assert failed == "NoveltyPreflightFailed"
    assert {"no_update_overall", "no_update_class", "context_overall", "context_class"} <= set(errors)


def test_missing_artifact_fails_closed(tmp_path: Path) -> None:
    assert MODULE.validate(tmp_path, tmp_path) == {
        "valid": False,
        "errors": ["preflight artifact files missing"],
    }

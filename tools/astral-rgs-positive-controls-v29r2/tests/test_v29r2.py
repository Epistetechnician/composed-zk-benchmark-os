from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v29r2_tested", ROOT / "v29r2.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def rows(correct: bool) -> list[dict[str, object]]:
    return [{"case_id": case["case_id"], "rung": case["rung"], "correct": correct} for case in MODULE.V29.expected_fixture()["cases"]]


def test_protocol_reuses_exact_v29_fixture() -> None:
    assert MODULE.V29.expected_fixture()["fixture_sha256"] == MODULE.PROTOCOL["fixture_sha256"]


def test_summary_has_locked_pass_and_block_states() -> None:
    assert MODULE.summary(rows(True))["status"] == "CanonicalBoundaryQualified"
    assert MODULE.summary(rows(False))["status"] == "CanonicalBoundaryStillBlocked"


def test_protocol_locks_canonical_leading_space_tokens() -> None:
    assert MODULE.PROTOCOL["prefix_token_ids"] == [16141, 25]
    assert MODULE.PROTOCOL["label_token_ids"] == {"A": 362, "B": 425, "C": 356, "D": 422}

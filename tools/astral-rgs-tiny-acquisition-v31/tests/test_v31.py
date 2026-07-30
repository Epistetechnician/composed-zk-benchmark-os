from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v31_tested", ROOT / "v31.py")
assert SPEC is not None and SPEC.loader is not None
V31 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = V31
SPEC.loader.exec_module(V31)


def phase(correct: int, total: int) -> list[dict[str, bool]]:
    return [{"correct": index < correct} for index in range(total)]


def test_fixture_is_stable() -> None:
    fixture = V31.expected_fixture()
    assert len(fixture["cases"]) == 16
    assert fixture["fixture_sha256"] == V31.V30.stable_hash({key: value for key, value in fixture.items() if key != "fixture_sha256"})


def test_summary_gate() -> None:
    phases = {"pre_direct": phase(4, 16), "no_update_direct": phase(4, 16), "post_direct": phase(16, 16), "reload_direct": phase(16, 16), "reload_paraphrase": phase(14, 16), "pre_protected": phase(32, 32), "reload_protected": phase(32, 32)}
    assert V31.summarize(phases, 0.0, True)["qualified"]

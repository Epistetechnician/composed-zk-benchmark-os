from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v32_test", ROOT / "v32.py")
assert SPEC is not None and SPEC.loader is not None
V32 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = V32
SPEC.loader.exec_module(V32)

def rows(correct, total):
    return [{"correct": i < correct} for i in range(total)]

def test_fixture_and_selection():
    assert len(V32.expected_fixture()["cases"]) == 8
    losses = [{"loss": 2.0 - i / 32} for i in range(32)]
    arms = {name: {"direct": rows(8, 8), "paraphrase": rows(7, 8), "protected": rows(32, 32), "loss_trace": losses} for name in V32.PROTOCOL["arms"]}
    result = V32.summary(rows(32, 32), arms)
    assert result["selected_arm"] == "fp32_clip_lr1e4"

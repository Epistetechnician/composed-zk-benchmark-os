"""Hermetic tests for the V41R28 local surrogate runner (no model access)."""

from __future__ import annotations

import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def _load():
    spec = importlib.util.spec_from_file_location("surrogate_v41r28", HERE / "surrogate_v41r28.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SURROGATE = _load()

FROZEN_CONTRACT = "sha256:ddf7f95ea4bf9b109dbdb1b02b87542a2a8ea56fd694f508c0b8647bc716ed4e"
FROZEN_ACQUISITION = "sha256:0459d3c39e37c1a3fb7a8ffdbee1dca214b75b316dab456ab3e8d82dd98d1f92"
FROZEN_PROTECTED = "sha256:83e873627f55df68f62a90d9847a73e5838eccc76fe48fb3c77109b6122b503e"


def test_frozen_contract_binding():
    assert SURROGATE.frozen_contract_sha256() == FROZEN_CONTRACT
    assert SURROGATE.V41R27.acquisition()["instrument_sha256"] == FROZEN_ACQUISITION
    assert SURROGATE.V41R27.protected()["instrument_sha256"] == FROZEN_PROTECTED


def test_instrument_reconstruction_counts():
    cases = SURROGATE.acquisition_cases()
    rows = SURROGATE.protected_rows()
    assert len(cases) == 64
    assert len(rows) == 256
    assert cases[32]["case_id"] == "v41r27-acquisition-032"
    assert cases[32]["target"] == "bravik"
    assert cases[35]["target"] == "quorin"
    assert rows[128]["case_id"] == "v41r27-protected-128"


def test_run_spec_failing_cell_and_census():
    spec = SURROGATE.run_spec("v41r27-panel-8-seed-412019")
    assert spec["panel_id"] == "v41r27-panel-8"
    assert spec["seed"] == 412019
    assert spec["acquisition_case_ids"] == [
        "v41r27-acquisition-032", "v41r27-acquisition-033",
        "v41r27-acquisition-034", "v41r27-acquisition-035"]
    assert spec["protected_case_ids"][0] == "v41r27-protected-128"
    assert spec["contract_sha256"] == FROZEN_CONTRACT
    for cell in ("v41r27-panel-6-seed-412019", "v41r27-panel-8-seed-412003",
                 "v41r27-panel-8-seed-412007"):
        assert SURROGATE.run_spec(cell)["run_id"] == cell
    for bad in ("v41r27-panel-8-seed-999999", "v41r27-panel-99-seed-412019", "nonsense"):
        try:
            SURROGATE.run_spec(bad)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass


def test_projection_algebra_matches_v41r27():
    assert SURROGATE.V41R27.project([1.0, -2.0], [0.0, 1.0]) == [1.0, 0.0]
    assert SURROGATE.V41R27.project([1.0, 2.0], [0.0, 1.0]) == [1.0, 2.0]
    # dot == 0 is not strictly below zero: no projection, identity return.
    assert SURROGATE.V41R27.project([1.0, -2.0], [0.0, 0.0]) == [1.0, -2.0]


def test_projection_roundoff_tolerance():
    eps = 1.1920928955078125e-07
    assert SURROGATE.projection_roundoff_tolerance(4.0, 9.0, eps) == 64.0 * eps * 6.0
    assert SURROGATE.projection_roundoff_tolerance(0.0, 0.0, eps) == 64.0 * eps * 1.0
    for bad in ((-1.0, 1.0, eps), (1.0, -1.0, eps), (1.0, 1.0, 0.0),
                (float("nan"), 1.0, eps), (1.0, float("inf"), eps)):
        try:
            SURROGATE.projection_roundoff_tolerance(*bad)
            raise AssertionError("expected ValueError")
        except ValueError:
            pass


def _receipt(loss: float, case_id: str = "c", step: int = 0) -> dict:
    return {"step": step, "case_index": 0, "case_id": case_id, "protected_indices": [0, 1, 2, 3],
            "acquisition_examples": 4, "protected_examples": 4, "acquisition_loss": loss,
            "protected_loss": loss, "weighted_loss": loss, "projection_applied": False,
            "pre_projection_dot": 1.0, "post_projection_dot": 1.0,
            "projected_gradient_norm_sq": 1.0, "protected_gradient_norm_sq": 1.0,
            "projection_dtype_epsilon": 1e-7, "projection_roundoff_tolerance": 1e-5,
            "projection_coefficient": 0.0, "gradient_norm": 0.5}


def _score(correct: bool, target_margin: float) -> dict:
    target = "bravik"
    scores = {target: 0.0 + target_margin, "solven": 0.0, "nareth": -1.0, "quorin": -2.0}
    return {"case_id": "c", "target": target, "candidates": list(scores),
            "candidate_log_probabilities": scores,
            "selected": target if correct else "solven",
            "correct": correct}


def test_case_gate_pass_and_each_error():
    receipts = [_receipt(1.0 * (0.5 ** (i / 8))) for i in range(64)]
    gate = SURROGATE.case_gate(_score(True, 2.5), receipts, True)
    assert gate["pass"] is True and gate["errors"] == []
    assert gate["target_margin_nats"] == 2.5

    gate = SURROGATE.case_gate(_score(False, 2.5), receipts, True)
    assert "selected_target" in gate["errors"]

    gate = SURROGATE.case_gate(_score(True, 1.9), receipts, True)
    assert "target_margin" in gate["errors"]

    flat = [_receipt(1.0) for _ in range(64)]
    gate = SURROGATE.case_gate(_score(True, 2.5), flat, True)
    assert "loss_ratio" in gate["errors"]

    gate = SURROGATE.case_gate(_score(True, 2.5), receipts, False)
    assert "reload_exact" in gate["errors"]

    try:
        SURROGATE.case_gate(_score(True, 2.5), receipts[:63], True)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_case_gate_loss_ratio_boundary():
    rising = [_receipt(0.1 if i < 56 else 1.0) for i in range(64)]
    gate = SURROGATE.case_gate(_score(True, 3.0), rising, True)
    assert "loss_ratio" in gate["errors"]
    assert gate["last8_to_first8_acquisition_loss_ratio"] > SURROGATE.LOSS_RATIO_MAXIMUM


def test_selection_tie_break_is_lexicographic():
    scores = {"bravik": -1.0, "solven": -1.0, "nareth": -2.0, "quorin": -3.0}
    candidates = list(scores)
    selected = min(candidates, key=lambda candidate: (-scores[candidate], candidate))
    assert selected == "bravik"


def test_accuracy_census():
    rows = [{"correct": True} for _ in range(16)]
    assert SURROGATE.accuracy(rows) == 1.0
    try:
        SURROGATE.accuracy(rows[:15])
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_canonical_hash_deterministic():
    value = {"b": 1, "a": [1, 2, {"c": None}]}
    assert SURROGATE.canonical_hash(value) == SURROGATE.canonical_hash(
        {"a": [1, 2, {"c": None}], "b": 1})
    assert SURROGATE.canonical_hash(value).startswith("sha256:")


def test_cli_without_execute_is_noop(tmp_path):
    output = tmp_path / "cell"
    completed = subprocess.run(
        [sys.executable, str(HERE / "surrogate_v41r28.py"),
         "--output", str(output), "--run-id", "v41r27-panel-8-seed-412019",
         "--substrate", "qwen2.5-0.5b"],
        capture_output=True, text=True, check=True)
    assert completed.returncode == 0
    assert not output.exists()


def test_substrate_pins_match_preregistration():
    assert SURROGATE.SUBSTRATES["llama-3.2-1b"]["model_safetensors_sha256"].startswith("35e39664")
    assert SURROGATE.SUBSTRATES["qwen2.5-0.5b"]["model_safetensors_sha256"].startswith("ddffab9c")
    for substrate in SURROGATE.SUBSTRATES.values():
        assert len(substrate["model_safetensors_sha256"]) == 64
        assert len(substrate["tokenizer_json_sha256"]) == 64


def test_preregistration_document_exists_and_is_fresh():
    text = SURROGATE.PREREGISTRATION.read_text()
    assert "V41R28LocalSurrogateAcquisitionGateCharacterization" in text
    assert FROZEN_CONTRACT.removeprefix("sha256:") in text
    assert "LocalSurrogateAcquisitionGateCharacterizationV41R28" in text


class _StubTokenizer:
    pad_token_id = 0
    eos_token_id = 2

    def apply_chat_template(self, messages, tokenize=True, add_generation_prompt=False):
        tokens = [10, 11, 12]
        for message in messages[1:]:
            tokens.extend([20] * ((len(message["content"]) + 2) // 3))
        return tokens


def test_collate_pads_unequal_rows_and_masks(tmp_path):
    import mlx.core as mx
    tokenizer = _StubTokenizer()
    rows = [{"prompt": "p", "answer": "sh"},
            {"prompt": "p", "answer": "a-much-longer-answer-here"}]
    inputs, labels = SURROGATE.collate(tokenizer, mx, rows)
    assert inputs.shape[0] == 2
    assert inputs.shape == labels.shape
    short_labels = labels[0].tolist()
    long_labels = labels[1].tolist()
    assert len(short_labels) == len(long_labels)
    # the short row is padded at the tail; padded positions are masked -100
    short_answer_tokens = sum(1 for value in [20] * ((len("sh") + 2) // 3))
    prompt_len = 3
    tail = short_labels[prompt_len + short_answer_tokens:]
    assert tail and all(value == -100 for value in tail)
    # the long row has no padding at the tail
    long_answer_tokens = (len("a-much-longer-answer-here") + 2) // 3
    assert long_labels[-1] != -100

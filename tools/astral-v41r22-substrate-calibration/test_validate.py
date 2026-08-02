from __future__ import annotations

import importlib.util
from pathlib import Path


PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v41r22_validator", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def packet(*, margin=3.0, ratio=0.05, correct=True):
    return {"update": {"receipts": ([{"loss": 10.0}] * 8) + ([{"loss": 10.0 * ratio}] * 8)},
            "exact_after": {"target": "a", "selected": "a" if correct else "b", "correct": correct,
                            "candidate_log_probabilities": {"a": margin, "b": 0.0, "c": -1.0, "d": -2.0}},
            "reload": {"state_exact": True}}


def test_contract_rederived_from_canonical_case() -> None:
    instrument = MODULE.BASE.INSTRUMENT.expected_packet(); case = instrument["cases"][0]
    contract = MODULE.expected_contract(instrument["instrument_sha256"], case)
    assert contract["arms"] == MODULE.ARMS
    assert contract["case_index"] == 0
    assert contract["tune_opened"] is False


def test_gate_recomputes_margin_and_loss_ratio() -> None:
    assert MODULE.gate(packet())["pass"] is True
    assert MODULE.gate(packet(margin=1.0))["errors"] == ["target_margin"]
    assert MODULE.gate(packet(ratio=0.2))["errors"] == ["loss_ratio"]


def test_interpretation_uses_frozen_minimal_order() -> None:
    arms = {name: packet(correct=False) for name in MODULE.ARMS}
    arms["steps512_lr2e4"] = packet()
    assert MODULE.decision(arms)["interpretation"] == "ExposureLimited"
    arms["steps64_lr2e3"] = packet()
    assert MODULE.decision(arms)["interpretation"] == "LearningRateLimited"


def test_runtime_requires_exact_cuda_stack() -> None:
    runtime = {"python": "3.12.3", "torch": "2.10.0", "transformers": "4.57.6",
               "peft": "0.18.1", "cuda": "12.8", "gpu": "NVIDIA H100 80GB HBM3"}
    assert MODULE.valid_runtime(runtime)
    runtime["cuda"] = "12.4"
    assert not MODULE.valid_runtime(runtime)


def test_missing_artifact_fails_closed(tmp_path: Path) -> None:
    assert MODULE.validate(tmp_path, tmp_path) == {"valid": False, "errors": ["calibration artifact files missing"]}

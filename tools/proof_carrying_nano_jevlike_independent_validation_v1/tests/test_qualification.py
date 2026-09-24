"""Qualification harness tests without loading an external checkpoint.

State slice: proof-carrying-nano-jevlike-independent-validation-v1.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.proof_carrying_nano_jevlike_independent_validation_v1.qualification import (
    evaluate_checks,
    prepare_checkpoint_custody,
)


def _action(scores: list[str], quantized: list[int]) -> dict:
    denominator = sum(quantized)
    return {
        "inputs": {
            "external_scores": scores,
            "quantized_scores": quantized,
            "quantization": {
                "rounding": "ROUND_HALF_EVEN",
                "scale": 1000,
            },
        },
        "outputs": {
            "probabilities": [
                {"denominator": denominator, "numerator": value}
                for value in quantized
            ]
        },
    }


def test_qualification_checks_capture_all_required_invariants() -> None:
    original = _action(["0.2", "0.7", "0.1"], [200, 700, 100])
    repeat = _action(["0.2", "0.7", "0.1"], [200, 700, 100])
    permuted = _action(["0.1", "0.2", "0.7"], [100, 200, 700])
    checks = evaluate_checks(
        original,
        repeat,
        permuted,
        host_before=("checkpoint", 2, "toy"),
        host_after=("checkpoint", 2, "toy"),
        independent_valid=True,
    )
    assert checks == {
        "permutation_sensitivity": True,
        "repeatability": True,
        "exact_probability_capture": True,
        "host_unchanged": True,
        "independent_bundle_validation": True,
    }


def test_qualification_checks_fail_closed_on_changed_repeat() -> None:
    original = _action(["0.2", "0.7", "0.1"], [200, 700, 100])
    repeat = _action(["0.2", "0.6", "0.2"], [200, 600, 200])
    permuted = _action(["0.1", "0.2", "0.7"], [100, 200, 700])
    checks = evaluate_checks(
        original,
        repeat,
        permuted,
        host_before=("checkpoint", 2, "toy"),
        host_after=("checkpoint", 3, "toy"),
        independent_valid=False,
    )
    assert checks["repeatability"] is False
    assert checks["host_unchanged"] is False
    assert checks["independent_bundle_validation"] is False


def test_custody_preparer_rejects_repository_checkpoint(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    source = repo_root / "checkpoint.pt"
    source.write_bytes(b"checkpoint")
    with pytest.raises(ValueError, match="outside the repository"):
        prepare_checkpoint_custody(
            source,
            tmp_path / "custody",
            repo_root=repo_root,
        )

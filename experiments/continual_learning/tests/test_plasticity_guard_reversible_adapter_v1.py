"""Hermetic contract tests for the plasticity-guard adapter slice."""

from pathlib import Path

import pytest

from experiments.continual_learning import plasticity_guard_reversible_adapter_v1 as runner
from experiments.continual_learning import validate_plasticity_guard_reversible_adapter_v1 as validator


def test_state_slice_and_guard_are_frozen():
    assert runner.STATE_SLICE == "continual-learning-plasticity-guard-reversible-adapter-v1"
    assert runner.plasticity_guard_accept(0, -100.0, 100.0) is True
    assert runner.plasticity_guard_accept(1, runner.MIN_CURRENT_GAIN, runner.MAX_PROTECTED_DEGRADATION) is True
    assert runner.plasticity_guard_accept(1, runner.MIN_CURRENT_GAIN - 1e-9, 0.0) is False
    assert runner.plasticity_guard_accept(1, runner.MIN_CURRENT_GAIN, runner.MAX_PROTECTED_DEGRADATION + 1e-9) is False


def test_guard_rejects_non_finite_inputs():
    with pytest.raises(ValueError, match="finite"):
        runner.plasticity_guard_accept(1, float("nan"), 0.0)
    with pytest.raises(ValueError, match="non-negative"):
        runner.plasticity_guard_accept(-1, 0.0, 0.0)


def test_training_command_is_adapter_only_and_offline():
    command = runner.training_command(
        Path("/cached/model"),
        Path("/external/data"),
        Path("/external/adapter"),
        1739,
        None,
    )
    assert "experiments.continual_learning.safe_mlx_lora" in command
    assert "--fine-tune-type" in command
    assert command[command.index("--fine-tune-type") + 1] == "lora"
    assert "--mask-prompt" not in command
    assert "--resume-adapter-file" not in command


def test_bootstrap_is_deterministic_and_independent_implementation_matches():
    values = (-0.2, 0.1, 0.3, -0.05)
    assert runner.bootstrap_interval(values, 20260828, 1000) == validator.bootstrap_interval(
        values, 20260828, 1000
    )
    assert runner.bootstrap_interval(values, 20260828, 1000) == runner.bootstrap_interval(
        values, 20260828, 1000
    )


def test_external_output_cannot_be_repository_path(tmp_path: Path):
    with pytest.raises(ValueError, match="outside the repository"):
        runner.external_path(runner.REPO_ROOT / "generated", "output")
    with pytest.raises(ValueError, match="outside the repository"):
        validator.artifact_root_is_external(validator.REPO_ROOT / "generated")

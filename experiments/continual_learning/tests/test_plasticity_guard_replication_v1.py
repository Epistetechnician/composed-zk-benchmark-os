"""Hermetic contract tests for the plasticity-guard replication slice."""

import gzip
import json
from pathlib import Path

import pytest

from experiments.continual_learning import plasticity_guard_replication_v1 as runner
from experiments.continual_learning import validate_plasticity_guard_replication_v1 as validator


def test_new_state_slice_and_frozen_decision_rules():
    assert runner.STATE_SLICE == "continual-learning-plasticity-guard-replication-v1"
    assert runner.SEEDS == (1747, 1749)
    assert runner.ORDERS == {
        "interleave": (0, 3, 1, 4, 2, 5),
        "outer_in": (0, 5, 1, 4, 2, 3),
    }
    assert runner.classify_replication(True, True) == "DevelopmentCandidate"
    assert runner.classify_replication(False, True) == "RollbackInfrastructureOnly"
    assert runner.classify_replication(False, False) == "ReplicationFailureClosed"


def test_guard_thresholds_are_inherited_without_tuning():
    assert runner.plasticity_guard_accept(0, -100.0, 100.0) is True
    assert runner.plasticity_guard_accept(1, runner.MIN_CURRENT_GAIN, runner.MAX_PROTECTED_DEGRADATION) is True
    assert runner.plasticity_guard_accept(1, runner.MIN_CURRENT_GAIN - 1e-9, 0.0) is False
    assert runner.plasticity_guard_accept(1, runner.MIN_CURRENT_GAIN, runner.MAX_PROTECTED_DEGRADATION + 1e-9) is False


def test_selection_is_after_prior_cohort_and_disjoint(tmp_path: Path):
    source = tmp_path / "input.jsonl.gz"
    with gzip.open(source, "wt", encoding="utf-8") as handle:
        for index in range(1, 33):
            handle.write(json.dumps({"text": f"document-{index} ", "url": f"https://example.test/{index}"}) + "\n")

    class FakeTokenizer:
        def encode(self, text: str, add_special_tokens: bool = False):
            del add_special_tokens
            return list(range(256))

    selected, prior = runner.select_records(source, FakeTokenizer())
    assert [item["document_id"] for item in prior] == [f"newsroom-test-line-{index:07d}" for index in range(9, 21)]
    assert [item["document_id"] for item in selected] == [f"newsroom-test-line-{index:07d}" for index in range(21, 33)]
    assert not {item["document_id"] for item in prior} & {item["document_id"] for item in selected}


def test_training_command_is_adapter_only_and_offline_contract_is_explicit():
    command = runner.training_command(
        Path("/cached/model"),
        Path("/external/data"),
        Path("/external/adapter"),
        1747,
        None,
    )
    assert command[command.index("--fine-tune-type") + 1] == "lora"
    assert command[command.index("--iters") + 1] == str(runner.TRAIN_ITERS)
    assert "--mask-prompt" not in command


def test_bootstrap_is_deterministic_and_independent_implementation_matches():
    values = (-0.2, 0.1, 0.3, -0.05)
    assert runner.bootstrap_interval(values, runner.BOOTSTRAP_SEED, 1000) == validator.bootstrap_interval(
        values, runner.BOOTSTRAP_SEED, 1000
    )
    assert runner.bootstrap_interval(values, runner.BOOTSTRAP_SEED, 1000) == runner.bootstrap_interval(
        values, runner.BOOTSTRAP_SEED, 1000
    )


def test_external_output_cannot_be_repository_path(tmp_path: Path):
    with pytest.raises(ValueError, match="outside the repository"):
        runner.external_path(runner.REPO_ROOT / "generated", "output")
    with pytest.raises(ValueError, match="outside the repository"):
        validator.artifact_root_is_external(validator.REPO_ROOT / "generated")

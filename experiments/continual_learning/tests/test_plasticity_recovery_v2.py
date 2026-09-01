"""Hermetic tests for the continual-learning-plasticity-recovery-v2 slice."""

from __future__ import annotations

from experiments.continual_learning import plasticity_recovery_v2 as runner
from experiments.continual_learning import validate_plasticity_recovery_v2 as validator


def test_v2_uses_fresh_panel_and_order_namespace():
    panel = runner.make_panel(runner.SEEDS[0])
    assert runner.STATE_SLICE != "continual-learning-plasticity-recovery-v1"
    assert runner.SEEDS != (20260901, 20260902, 20260903, 20260904)
    assert runner.ORDER_SEEDS != (8111, 8112, 8113)
    assert len(panel) == 32
    assert len({shard.payload_sha256 for shard in panel}) == 32
    assert sorted(shard.shard_id for shard in panel if shard.split == "fit") == [f"fit-{index:03d}" for index in range(16)]


def test_protected_replay_reserves_four_shards_and_uses_them():
    panel = runner.make_panel(runner.SEEDS[0])
    case = runner._run_case(panel, "protected_replay", runner.SEEDS[0], runner.ORDER_SEEDS[0])
    assert len(case["protected_replay_shard_ids"]) == runner.PROTECTED_REPLAY_CAPACITY
    assert len(set(case["protected_replay_shard_ids"])) == runner.PROTECTED_REPLAY_CAPACITY
    assert all(shard_id.startswith("fit-") for shard_id in case["protected_replay_shard_ids"])
    assert any(update["target_shard_ids"][1] != update["source_shard_id"] for update in case["updates"])
    assert case["gradient_evaluations"] == 32
    assert case["shadow_gradient_evaluations"] == 32


def test_v2_factorial_and_independent_validator_pass_structure():
    result = runner.run_factorial()
    runner.validate_result(result)
    validator.validate_result(result)
    assert len(result["cases"]) == 72
    assert result["summaries"]["protected_replay"]["case_count"] == 12
    assert result["prediction_lock"]["body"]["assessment_started"] is False

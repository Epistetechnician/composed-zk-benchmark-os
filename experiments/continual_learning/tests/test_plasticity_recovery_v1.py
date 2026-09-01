"""Hermetic tests for the continual-learning-plasticity-recovery-v1 slice."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from experiments.continual_learning import plasticity_recovery_v1 as runner
from experiments.continual_learning import diagnose_plasticity_recovery_v1 as diagnosis
from experiments.continual_learning import validate_plasticity_recovery_diagnosis_v1 as diagnosis_validator
from experiments.continual_learning import validate_plasticity_recovery_v1 as validator


def test_panel_is_fresh_structured_and_disjoint_by_split():
    panel = runner.make_panel(runner.SEEDS[0])
    assert len(panel) == runner.FIT_COUNT + runner.TUNE_COUNT + runner.ASSESSMENT_COUNT
    assert [sum(shard.split == split for shard in panel) for split in runner.SPLITS] == [16, 8, 8]
    assert len({shard.payload_sha256 for shard in panel}) == len(panel)
    assert runner.panel_digest(panel) != runner.panel_digest(runner.make_panel(runner.SEEDS[1]))


def test_all_arms_use_equal_compute_and_only_non_control_arms_commit():
    panel = runner.make_panel(runner.SEEDS[0])
    cases = {
        arm: runner._run_case(panel, arm, runner.SEEDS[0], runner.ORDER_SEEDS[0])
        for arm in runner.ARMS
    }
    for case in cases.values():
        assert case["gradient_evaluations"] == runner.UPDATE_BUDGET * runner.GRADIENT_SLOTS
        assert case["shadow_gradient_evaluations"] == runner.UPDATE_BUDGET * runner.GRADIENT_SLOTS
        assert case["equal_compute_passed"] is True
        assert case["base_weights_unchanged"] is True
        assert case["adapter_restore_passed"] is True
        assert case["rollback_max_abs_error"] <= runner.ROLLBACK_TOLERANCE
    assert cases["no_update"]["final_weights"] == [0.0] * runner.DIMENSION
    assert cases["fixed_adapter"]["final_weights"] != cases["no_update"]["final_weights"]


def test_replay_and_reinitialization_have_observable_mechanically_known_effects():
    panel = runner.make_panel(runner.SEEDS[0])
    replay = runner._run_case(panel, "replay", runner.SEEDS[0], runner.ORDER_SEEDS[0])
    reinit = runner._run_case(panel, "selective_reinit", runner.SEEDS[0], runner.ORDER_SEEDS[0])
    combined = runner._run_case(panel, "replay_selective_reinit", runner.SEEDS[0], runner.ORDER_SEEDS[0])
    assert any(len(update["target_shard_ids"]) == 2 and update["target_shard_ids"][0] != update["target_shard_ids"][1] for update in replay["updates"])
    assert reinit["reinitializations"] > 0
    assert combined["reinitializations"] == reinit["reinitializations"]
    assert combined["final_weights"] != reinit["final_weights"]


def test_factorial_is_sealed_and_self_validating():
    result = runner.run_factorial()
    runner.validate_result(result)
    assert len(result["cases"]) == len(runner.SEEDS) * len(runner.ORDER_SEEDS) * len(runner.ARMS)
    assert result["prediction_lock"]["body"]["assessment_started"] is False
    assert len(result["prediction_lock"]["body"]["predictions"]) == len(result["cases"])
    assert all(summary["case_count"] == 12 for summary in result["summaries"].values())


def test_external_artifact_manifest_is_independently_validated(tmp_path: Path):
    result = runner.run_factorial()
    runner.write_artifact(tmp_path, result)
    validated = validator.validate_artifact_root(tmp_path)
    assert validated["result_sha256"] == result["result_sha256"]


def test_validator_rejects_mutated_case_digest():
    result = runner.run_factorial()
    tampered = deepcopy(result)
    tampered["cases"][0]["adaptation_gain"] += 1.0
    with pytest.raises(runner.ProtocolError, match="case digest mismatch"):
        runner.validate_result(tampered)


def test_read_only_diagnosis_accounts_for_forgetting_and_order(tmp_path: Path):
    result = runner.run_factorial()
    result_path = tmp_path / "result.json"
    result_path.write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
    report = diagnosis.diagnose(result_path)
    diagnosis_validator.validate_result(report)
    diagnosis.write_artifact(tmp_path / "diagnosis", report)
    diagnosis_validator.validate_artifact_root(tmp_path / "diagnosis", result_path)
    assert report["classification"] == "NoCandidate"
    assert report["arms"]["replay"]["replay_target_slot_count"] > 0
    assert report["arms"]["selective_reinit"]["reinitialization_count"] > 0
    assert report["arms"]["fixed_adapter"]["affected_protected_shards"]

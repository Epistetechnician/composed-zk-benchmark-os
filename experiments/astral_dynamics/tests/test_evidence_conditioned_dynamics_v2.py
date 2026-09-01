from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.astral_dynamics import evidence_conditioned_dynamics_v2 as dynamics
from experiments.astral_dynamics import validate_factorial_v2 as validator


def test_exact_panel_is_fresh_split_disjoint_and_reproducible():
    config = dynamics.ProtocolConfig()
    first = dynamics.make_panel(config, dynamics.PREREGISTERED_REPLICATE_SEEDS[0])
    second = dynamics.make_panel(config, dynamics.PREREGISTERED_REPLICATE_SEEDS[0])

    assert first == second
    assert [shard.split for shard in first] == ["fit"] * 24 + ["tune"] * 12 + ["assessment"] * 12
    assert len({shard.payload_sha256 for shard in first}) == len(first)
    assert len({shard.shard_id for shard in first}) == len(first)
    assert dynamics.panel_digest(first) == dynamics.panel_digest(second)
    assert dynamics.panel_digest(first) != dynamics.panel_digest(
        dynamics.make_panel(config, dynamics.PREREGISTERED_REPLICATE_SEEDS[1])
    )


def test_update_effect_and_interference_are_exactly_replayable():
    config = dynamics.ProtocolConfig()
    panel = dynamics.make_panel(config)
    fit = [shard for shard in panel if shard.split == "fit"]
    fit_by_id = {shard.shard_id: shard for shard in fit}
    state = dynamics._initial_state(config)
    state, first_decision = dynamics._process_shard(
        state,
        fit[0],
        fit_by_id,
        fit,
        "oracle",
        "fixed_cadence",
        "deterministic",
        dynamics.PREREGISTERED_REPLICATE_SEEDS[0],
        dynamics.PREREGISTERED_ORDER_SEEDS[0],
        0,
        config,
    )
    update = state.updates[0]
    assert tuple(state.parameters[index] - update.before_parameters[index] for index in range(config.dimension)) == update.applied_delta
    assert first_decision["interference"] == update.interference
    assert update.effect_sha256 == dynamics._effect_digest(
        update.shard_id,
        update.before_parameters,
        update.after_parameters,
        update.learning_rate,
        update.interference,
    )


def test_factorial_has_locked_panel_and_equal_learning_compute():
    result = dynamics.run_factorial()
    dynamics.validate_result(result)
    validator.validate_result(result)

    assert result["factorial_cell_count"] == 32
    assert len(result["cells"]) == 32
    assert result["prediction_lock"]["assessment_started"] is False
    all_replicates = [replicate for cell in result["cells"].values() for replicate in cell["replicates"]]
    assert len(all_replicates) == 288
    assert {(item["update_attempts"], item["gradient_compute_units"], item["shadow_compute_units"]) for item in all_replicates} == {(24, 144, 144)}
    assert all(item["prediction_locked_before_assessment"] for item in all_replicates)


def test_taxonomy_controls_have_distinct_calibration_signatures():
    result = dynamics.run_factorial()
    oracle = result["cells"]["adaptive_verification|deterministic|oracle"]
    noisy = result["cells"]["adaptive_verification|deterministic|noisy"]
    shuffled = result["cells"]["adaptive_verification|deterministic|shuffled"]
    absent = result["cells"]["adaptive_verification|deterministic|absent"]

    assert max(item["calibration_brier"] for item in oracle["replicates"]) == 0.0
    assert max(item["calibration_brier"] for item in noisy["replicates"]) <= dynamics.ProtocolConfig().taxonomy_noise_bound**2 + 1e-12
    assert any(item["calibration_brier"] > 0.0 for item in shuffled["replicates"])
    assert any(item["calibration_brier"] > 0.0 for item in absent["replicates"])


def test_rollback_is_exact_and_order_guard_is_reported():
    result = dynamics.run_factorial()
    for cell in result["cells"].values():
        assert all(item["rollback_max_abs_error"] <= dynamics.ROLLBACK_TOLERANCE for item in cell["replicates"])
        assert cell["max_order_range"] >= 0.0
        assert cell["guards"]["shard_order_stability"] == (cell["max_order_range"] <= dynamics.MAX_ORDER_RANGE)


def test_independent_validator_rejects_tampered_primary_and_accepts_json_round_trip(tmp_path: Path):
    result = dynamics.run_factorial()
    result_path = tmp_path / "result.json"
    result_path.write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
    dynamics.validate_result(json.loads(result_path.read_text(encoding="utf-8")))
    validator.validate_file(result_path)

    tampered = json.loads(result_path.read_text(encoding="utf-8"))
    key = "fixed_cadence|deterministic|oracle"
    tampered["cells"][key]["replicates"][0]["primary_endpoint_value"] += 0.01
    with pytest.raises(validator.ValidationError, match="cell digest mismatch|primary endpoint mismatch|result digest mismatch"):
        validator.validate_result(tampered)

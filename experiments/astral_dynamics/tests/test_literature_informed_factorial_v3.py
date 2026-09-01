from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.astral_dynamics import literature_informed_factorial_v3 as experiment
from experiments.astral_dynamics import validate_literature_factorial_v3 as validator


def test_literature_mechanisms_are_explicit_and_panel_is_fresh():
    config = experiment.ProtocolConfig()
    panel = experiment.make_panel(config, experiment.PREREGISTERED_REPLICATE_SEEDS[0])

    assert experiment.MEMORY_POLICIES == ("single", "fast_slow", "replay", "ewc", "plasticity_guard", "integrated")
    assert experiment.SCHEDULE_POLICIES == ("fixed", "single_frequency", "dual_frequency", "bounded_stochastic_dual")
    assert len(panel) == 48
    assert len({shard.payload_sha256 for shard in panel}) == 48
    assert len({shard.shard_id for shard in panel}) == 48
    assert experiment.panel_digest(panel) != experiment.panel_digest(
        experiment.make_panel(config, experiment.PREREGISTERED_REPLICATE_SEEDS[1])
    )


def test_schedule_is_bounded_and_dual_frequency_is_not_single_frequency():
    config = experiment.ProtocolConfig()
    fixed = [experiment.schedule_multiplier("fixed", step, 0, "fit-000", config) for step in range(32)]
    single = [experiment.schedule_multiplier("single_frequency", step, 0, "fit-000", config) for step in range(32)]
    dual = [experiment.schedule_multiplier("dual_frequency", step, 0, "fit-000", config) for step in range(32)]
    stochastic = [experiment.schedule_multiplier("bounded_stochastic_dual", step, 1, "fit-000", config) for step in range(32)]

    assert fixed == [1.0] * 32
    assert len(set(single)) > 4
    assert len(set(dual)) > 4
    assert single != dual
    assert stochastic != dual
    assert all(config.min_schedule_multiplier <= value <= config.max_schedule_multiplier for value in dual + stochastic)


def test_replay_and_consolidation_change_exact_state_but_not_compute_budget():
    config = experiment.ProtocolConfig()
    panel = experiment.make_panel(config)
    prepared_single = experiment._prepare_trial(
        panel,
        "single",
        "fixed",
        "fixed_admission",
        "oracle",
        experiment.PREREGISTERED_REPLICATE_SEEDS[0],
        experiment.PREREGISTERED_ORDER_SEEDS[0],
        config,
    )
    prepared_integrated = experiment._prepare_trial(
        panel,
        "integrated",
        "fixed",
        "fixed_admission",
        "oracle",
        experiment.PREREGISTERED_REPLICATE_SEEDS[0],
        experiment.PREREGISTERED_ORDER_SEEDS[0],
        config,
    )

    assert prepared_single.state.update_attempts == prepared_integrated.state.update_attempts == 48
    assert prepared_single.state.gradient_compute_units == prepared_integrated.state.gradient_compute_units == 288
    assert prepared_single.state.fast != prepared_integrated.state.fast
    assert prepared_integrated.state.slow != prepared_single.state.slow
    assert prepared_integrated.state.importance != prepared_single.state.importance


def test_full_factorial_and_independent_validator():
    result = experiment.run_factorial()
    experiment.validate_result(result)
    validator.validate_result(result)

    assert result["factorial_cell_count"] == 192
    assert len(result["cells"]) == 192
    assert len(result["prediction_lock"]["predictions"]) == 1728
    assert all(cell["replicate_count"] == 9 for cell in result["cells"].values())
    assert result["decision_diagnostics"]["all_learning_compute_equal"] is True


def test_prediction_lock_and_guard_fields_are_bound():
    result = experiment.run_factorial()
    for cell in result["cells"].values():
        for replicate in cell["replicates"]:
            assert replicate["prediction_locked_before_assessment"] is True
            assert replicate["prediction_lock_sha256"] == result["prediction_lock_sha256"]
            assert replicate["rollback_max_abs_error"] <= experiment.ROLLBACK_TOLERANCE
            assert replicate["update_attempts"] == 48
            assert replicate["gradient_compute_units"] == 288
            assert replicate["shadow_compute_units"] == 288


def test_independent_validator_rejects_tampering_after_json_round_trip(tmp_path: Path):
    result = experiment.run_factorial()
    result_path = tmp_path / "result.json"
    result_path.write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
    validator.validate_file(result_path)

    tampered = json.loads(result_path.read_text(encoding="utf-8"))
    key = "integrated|dual_frequency|evidence_conditioned|oracle"
    tampered["cells"][key]["replicates"][0]["primary_endpoint_value"] += 0.01
    with pytest.raises(validator.ValidationError, match="cell digest mismatch|assessment final mismatch|primary endpoint mismatch|result digest mismatch"):
        validator.validate_result(tampered)

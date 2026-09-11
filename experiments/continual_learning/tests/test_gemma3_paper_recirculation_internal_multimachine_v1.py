"""Hermetic tests for the internal multi-instance lane.

State slice: continual-learning-gemma3-paper-recirculation-internal-multimachine-v1.
"""

import json
from pathlib import Path

import pytest

from experiments.continual_learning import (
    gemma3_paper_recirculation_internal_multimachine_v1 as runner,
)
from experiments.continual_learning import (
    validate_gemma3_paper_recirculation_internal_multimachine_v1 as validator,
)


def _instance(instance_id: str, machine_id: str = "host-a", pair=None):
    value = {
        "schema": validator.INSTANCE_SCHEMA,
        "state_slice": validator.STATE_SLICE,
        "claim_ceiling": validator.CLAIM_CEILING,
        "instance_id": instance_id,
        "machine_id": machine_id,
        "selected_pair": pair or [11, 4],
        "assessment_deltas": [-0.2] * 16,
        "assessment_mean_delta": -0.2,
        "assessment_bootstrap_upper_95": -0.05,
        "candidate_pairs": [[7, 2], [9, 3], [11, 4], [12, 5]],
        "fit_window_count": 16,
        "assessment_window_count": 16,
        "window_limit": 16,
        "execution_mode": "replication",
        "evaluation_alpha": 0.15,
        "evaluation_beta": 0.85,
        "temperature_control": {"temperature": 1.2, "baseline_mean_nll": 3.0},
        "zero_alpha_parity": {"passed": True, "max_abs_logit_delta": 0.0},
        "deterministic_repeat_max_abs_delta": 0.0,
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "model_manifest_sha256": "model",
        "corpus_manifest_sha256": "corpus",
        "runner_sha256": "runner",
        "protocol_sha256": "protocol",
        "implementation_manifest_sha256": validator.validate_implementation_manifest(),
    }
    value["result_sha256"] = runner.digest(value)
    return value


def _write(path: Path, value: dict):
    path.write_text(json.dumps(value), encoding="utf-8")


def test_instance_digest_is_checked(tmp_path):
    value = _instance("i1")
    value["assessment_mean_delta"] = -0.1
    path = tmp_path / "instance.json"
    _write(path, value)
    with pytest.raises(ValueError, match="digest mismatch"):
        validator.validate_instance(path)


def test_three_same_host_instances_are_not_called_multimachine(tmp_path):
    paths = []
    for index in range(3):
        path = tmp_path / f"{index}.json"
        _write(path, _instance(f"i{index}"))
        paths.append(path)
    result = validator.aggregate(paths)
    assert result["decision"] == "InternalReplicatedEffect"
    assert result["disposition"] == "SingleMachineMultiInstanceOnly"
    assert result["independent_review"] is False
    assert result["scientific_claim_authorized"] is False


def test_distinct_hosts_can_reach_internal_multimachine_disposition(tmp_path):
    paths = []
    for index, host in enumerate(("host-a", "host-b", "host-c")):
        path = tmp_path / f"{index}.json"
        _write(path, _instance(f"i{index}", host))
        paths.append(path)
    result = validator.aggregate(paths)
    assert result["machine_count"] == 3
    assert result["disposition"] == "MultiMachineInternalReplication"


def test_pair_disagreement_is_no_candidate(tmp_path):
    paths = []
    for index, pair in enumerate(([11, 4], [9, 3], [11, 4])):
        path = tmp_path / f"{index}.json"
        _write(path, _instance(f"i{index}", f"host-{index}", pair))
        paths.append(path)
    assert validator.aggregate(paths)["decision"] == "NoCandidate"


def test_nonfinite_delta_is_rejected(tmp_path):
    value = _instance("i1")
    value["assessment_deltas"][0] = float("nan")
    value["result_sha256"] = runner.digest(value)
    path = tmp_path / "instance.json"
    _write(path, value)
    with pytest.raises(ValueError, match="digest mismatch"):
        validator.validate_instance(path)


def test_smoke_results_cannot_be_aggregated(tmp_path):
    paths = []
    for index in range(3):
        value = _instance(f"i{index}")
        value["fit_window_count"] = 4
        value["assessment_window_count"] = 4
        value["window_limit"] = 4
        value["execution_mode"] = "engineering-smoke"
        value["assessment_deltas"] = [-0.2] * 4
        value["assessment_mean_delta"] = -0.2
        value.pop("result_sha256")
        value["result_sha256"] = runner.digest(value)
        path = tmp_path / f"{index}.json"
        _write(path, value)
        paths.append(path)
    with pytest.raises(ValueError, match="smoke"):
        validator.aggregate(paths)

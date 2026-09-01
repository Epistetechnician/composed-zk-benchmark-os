from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest

from experiments.continual_learning import autoresearch_information_budget_frontier_v1 as search
from experiments.continual_learning import information_budget_frontier_v1 as experiment
from experiments.continual_learning import validate_information_budget_frontier_v1 as validator


def _approved_receipt(path: Path) -> Path:
    receipt_dir = path / "continual-learning"
    receipt_dir.mkdir(parents=True)
    receipt = receipt_dir / "approved.json"
    receipt.write_text(json.dumps({
        "schema_version": experiment.REVIEW_RECEIPT_SCHEMA_VERSION,
        "state_slice": experiment.STATE_SLICE,
        "review_packet_path": str(experiment.REVIEW_PACKET_PATH),
        "review_packet_sha256": hashlib.sha256(experiment.REVIEW_PACKET_PATH.read_bytes()).hexdigest(),
        "reviewer_role": "independent",
        "disposition": "APPROVED_FOR_SYNTHETIC_RUN",
        "blocking_defects": [],
        "checks": {item: "PASS" for item in experiment.REVIEW_CHECKS},
    }), encoding="utf-8")
    return receipt


def test_projection_removes_protected_component():
    basis = experiment._orthonormal_basis(((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
    residual = experiment._project_out((1.0, 2.0, 3.0), basis)
    assert residual == pytest.approx((0.0, 0.0, 3.0))


def test_campaign_is_exact_and_independently_validated():
    result = experiment.run_campaign(experiment.candidate_config("grid5_lr032"), ("tune",))
    experiment.validate_result(result)
    validator.validate_result(json.loads(json.dumps(result)))
    assert result["state_slice"] == experiment.STATE_SLICE
    assert result["summary"]["by_split_arm"]["tune:cpsp_frontier"]["all_hard_guards_pass"]


def test_assessment_requires_review_receipt_and_prediction_lock():
    with pytest.raises(experiment.ProtocolError, match="independent review receipt"):
        experiment.run_campaign(experiment.candidate_config("grid5_lr032"), ("assessment",))


def test_approved_review_receipt_is_bound_to_packet_identity(tmp_path: Path):
    receipt = _approved_receipt(tmp_path)
    assert len(experiment._validate_review_receipt(receipt)) == 64


def test_tampered_review_packet_digest_is_rejected(tmp_path: Path):
    receipt = _approved_receipt(tmp_path)
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    payload["review_packet_sha256"] = "0" * 64
    receipt.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(experiment.ProtocolError, match="packet digest"):
        experiment._validate_review_receipt(receipt)


def test_tampered_prediction_lock_is_rejected(tmp_path: Path):
    lock = tmp_path / "prediction-lock.json"
    lock.write_text(
        json.dumps({
            "state_slice": experiment.STATE_SLICE,
            "lock_type": "fit_tune_prediction_lock",
            "candidate": {
                "name": "grid3_lr032",
                "alpha_grid_name": "grid3",
                "alpha_grid": [0.0, 0.5, 1.0],
                "learning_rate": 0.32,
            },
            "selection_split": "tune",
        }),
        encoding="utf-8",
    )
    with pytest.raises(experiment.ProtocolError, match="prediction lock path"):
        experiment._validate_prediction_lock(lock, experiment.candidate_config("grid5_lr032"))


def test_lock_rejects_fit_tune_artifact_for_different_candidate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    custody_root = tmp_path / "custody"
    (custody_root / "candidates").mkdir(parents=True)
    monkeypatch.setattr(experiment, "CUSTODY_RUN_ROOT", custody_root)
    result = experiment.run_campaign(experiment.candidate_config("grid3_lr032"), ("fit", "tune"))
    fit_path = custody_root / "candidates" / "grid3.json"
    fit_path.write_text(json.dumps(result), encoding="utf-8")
    receipt = _approved_receipt(tmp_path / "receipt-root")
    lock = custody_root / "prediction-lock.json"
    lock.write_text(json.dumps({
        "state_slice": experiment.STATE_SLICE,
        "lock_type": "fit_tune_prediction_lock",
        "candidate": {
            "name": "grid5_lr032",
            "alpha_grid_name": "grid5",
            "alpha_grid": [0.0, 0.25, 0.5, 0.75, 1.0],
            "learning_rate": 0.32,
        },
        "selection_metric": experiment.PRIMARY_ENDPOINT,
        "selection_split": "tune",
        "selected_value": 0.0,
        "candidate_order": ["grid5_lr032"],
        "review_packet_path": str(experiment.REVIEW_PACKET_PATH),
        "review_packet_sha256": hashlib.sha256(experiment.REVIEW_PACKET_PATH.read_bytes()).hexdigest(),
        "review_receipt_path": str(receipt.resolve()),
        "review_receipt_sha256": experiment._validate_review_receipt(receipt),
        "fit_tune_result_path": str(fit_path.resolve()),
        "fit_tune_result_sha256": hashlib.sha256(fit_path.read_bytes()).hexdigest(),
    }), encoding="utf-8")
    with pytest.raises(experiment.ProtocolError, match="fit/tune candidate"):
        experiment._validate_prediction_lock(lock, experiment.candidate_config("grid5_lr032"))


def test_lock_rejects_selected_value_tampering(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    custody_root = tmp_path / "custody"
    (custody_root / "candidates").mkdir(parents=True)
    monkeypatch.setattr(experiment, "CUSTODY_RUN_ROOT", custody_root)
    config = experiment.candidate_config("grid3_lr032")
    result = experiment.run_campaign(config, ("fit", "tune"))
    fit_path = custody_root / "candidates" / "grid3.json"
    fit_path.write_text(json.dumps(result), encoding="utf-8")
    receipt = _approved_receipt(tmp_path / "receipt-root")
    lock = custody_root / "prediction-lock.json"
    lock.write_text(json.dumps({
        "state_slice": experiment.STATE_SLICE,
        "lock_type": "fit_tune_prediction_lock",
        "candidate": {"name": config.name, "alpha_grid_name": config.alpha_grid_name, "alpha_grid": list(config.alpha_grid), "learning_rate": config.learning_rate},
        "selection_metric": experiment.PRIMARY_ENDPOINT,
        "selection_split": "tune",
        "selected_value": 999.0,
        "candidate_order": [config.name],
        "review_packet_path": str(experiment.REVIEW_PACKET_PATH),
        "review_packet_sha256": hashlib.sha256(experiment.REVIEW_PACKET_PATH.read_bytes()).hexdigest(),
        "review_receipt_path": str(receipt.resolve()),
        "review_receipt_sha256": experiment._validate_review_receipt(receipt),
        "fit_tune_result_path": str(fit_path.resolve()),
        "fit_tune_result_sha256": hashlib.sha256(fit_path.read_bytes()).hexdigest(),
    }), encoding="utf-8")
    with pytest.raises(experiment.ProtocolError, match="selected value"):
        experiment._validate_prediction_lock(lock, config)


def test_untouched_arm_is_identity_and_compute_matched():
    trial = experiment.run_trial(
        arm="untouched",
        split="assessment",
        seed=experiment.PREREGISTERED_REPLICATE_SEEDS[0],
        order_seed=experiment.PREREGISTERED_ORDER_SEEDS[0],
        order_direction="forward",
        risk_price=experiment.RISK_PRICES[0],
        config=experiment.candidate_config("grid5_lr032"),
    )
    assert trial.adaptation_gain == pytest.approx(0.0, abs=1e-12)
    assert trial.forgetting_value == pytest.approx(0.0, abs=1e-12)
    assert trial.compute_guard_pass
    assert trial.gradient_compute_units == experiment.UPDATE_BUDGET
    assert trial.shadow_compute_units == experiment.UPDATE_BUDGET * 5


def test_rollback_is_exact_after_nonzero_update():
    trial = experiment.run_trial(
        arm="fixed_adapter",
        split="assessment",
        seed=experiment.PREREGISTERED_REPLICATE_SEEDS[0],
        order_seed=experiment.PREREGISTERED_ORDER_SEEDS[0],
        order_direction="forward",
        risk_price=experiment.RISK_PRICES[0],
        config=experiment.candidate_config("grid5_lr032"),
    )
    assert trial.adaptation_gain > 0.0
    assert trial.rollback_max_abs_error == pytest.approx(0.0, abs=1e-12)


def test_candidate_guard_requires_fit_and_tune():
    result = {
        "summary": {
            "by_split_arm": {
                "fit:cpsp_frontier": {"all_hard_guards_pass": False},
                "tune:cpsp_frontier": {"all_hard_guards_pass": True},
            }
        }
    }
    assert search._candidate_guards(result) == (False, True, False)


def test_tampering_is_rejected_by_both_validators():
    result = experiment.run_campaign(experiment.candidate_config("grid3_lr032"), ("tune",))
    tampered = json.loads(json.dumps(result))
    tampered["trials"][0]["adaptation_gain"] += 0.01
    with pytest.raises((experiment.ProtocolError, validator.ValidationError)):
        experiment.validate_result(tampered)
    with pytest.raises(validator.ValidationError):
        validator.validate_result(tampered)


def test_validator_rejects_incomplete_coverage():
    result = experiment.run_campaign(experiment.candidate_config("grid3_lr032"), ("tune",))
    incomplete = json.loads(json.dumps(result))
    incomplete["trials"].pop()
    with pytest.raises(validator.ValidationError, match="coverage"):
        validator.validate_result(incomplete)


def test_writer_rejects_non_custody_path(tmp_path: Path):
    result = experiment.run_campaign(experiment.candidate_config("grid3_lr032"), ("tune",))
    with pytest.raises(experiment.ProtocolError, match="declared custody root"):
        experiment.write_result(result, tmp_path / "result.json")


def test_driver_rejects_fit_guard_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    custody_root = tmp_path / "driver-custody"
    monkeypatch.setattr(search, "CUSTODY_RUN_ROOT", custody_root)
    monkeypatch.setattr(experiment, "CUSTODY_RUN_ROOT", custody_root)
    monkeypatch.setattr(validator, "CUSTODY_RUN_ROOT", str(custody_root))
    monkeypatch.setattr(search, "_guard", lambda _result, split, _arm: split != "fit")
    with pytest.raises(RuntimeError, match="no guarded candidate"):
        search.run_search(custody_root, tmp_path / "unused.json", max_iterations=1)


def test_driver_completes_approved_receipt_to_assessment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    custody_root = tmp_path / "driver-custody"
    monkeypatch.setattr(search, "CUSTODY_RUN_ROOT", custody_root)
    monkeypatch.setattr(experiment, "CUSTODY_RUN_ROOT", custody_root)
    monkeypatch.setattr(validator, "CUSTODY_RUN_ROOT", str(custody_root))
    receipt = _approved_receipt(tmp_path / "receipt-root")
    summary = search.run_search(custody_root, receipt, max_iterations=1)
    assert summary["state_slice"] == experiment.STATE_SLICE
    assert (custody_root / "prediction_lock.json").exists()
    assert (custody_root / "assessment.json").exists()

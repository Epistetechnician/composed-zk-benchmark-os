from __future__ import annotations

import json

import pytest

from experiments.continual_learning.qwen_inference_recirculation_v1 import (
    CLAIM_CEILING,
    STATE_SLICE,
    RecirculationConfig,
    candidate_configs,
    digest,
)
from experiments.continual_learning.validate_qwen_inference_recirculation_v1 import (
    validate,
)


def _valid_artifact(root):
    config = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "model_manifest_sha256": "m" * 64,
    }
    config["config_sha256"] = digest(
        {key: item for key, item in config.items() if key != "config_sha256"}
    )
    results = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "parity": {"passed": True, "max_abs_logit_delta": 0.0},
    }
    results["results_sha256"] = digest(
        {key: item for key, item in results.items() if key != "results_sha256"}
    )
    manifest_body = {"model_name": "synthetic-qwen", "files": []}
    manifest = {"manifest": manifest_body, "manifest_sha256": "m" * 64}
    receipt = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "config_sha256": config["config_sha256"],
        "results_sha256": results["results_sha256"],
        "model_manifest_sha256": manifest["manifest_sha256"],
        "zero_alpha_parity_passed": True,
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "deterministic_repeat_passed": True,
        "performance_improved_on_assessment": False,
    }
    receipt["receipt_sha256"] = digest(
        {key: item for key, item in receipt.items() if key != "receipt_sha256"}
    )
    (root / "config.json").write_text(json.dumps(config), encoding="utf-8")
    (root / "results.json").write_text(json.dumps(results), encoding="utf-8")
    (root / "model-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")


def test_config_requires_deep_to_shallow_pair():
    RecirculationConfig(11, 4, 0.10).validate(14)
    with pytest.raises(ValueError, match="destination < source"):
        RecirculationConfig(4, 11, 0.10).validate(14)


def test_candidate_grid_is_frozen_and_layer_bounded():
    configs = candidate_configs(14)
    assert [(item.source_layer, item.destination_layer) for item in configs] == [
        (7, 2),
        (9, 3),
        (11, 4),
        (12, 5),
    ]
    assert all(item.alpha == 0.10 for item in configs)


def test_validator_accepts_structurally_valid_external_artifact(tmp_path):
    _valid_artifact(tmp_path)
    # The synthetic manifest's digest is intentionally resealed for this test.
    manifest = json.loads((tmp_path / "model-manifest.json").read_text())
    manifest["manifest_sha256"] = digest(manifest["manifest"])
    (tmp_path / "model-manifest.json").write_text(json.dumps(manifest))
    for filename in ("config.json", "receipt.json"):
        value = json.loads((tmp_path / filename).read_text())
        value["model_manifest_sha256"] = manifest["manifest_sha256"]
        if filename == "receipt.json":
            value["receipt_sha256"] = digest(
                {key: item for key, item in value.items() if key != "receipt_sha256"}
            )
        else:
            value["config_sha256"] = digest(
                {key: item for key, item in value.items() if key != "config_sha256"}
            )
        (tmp_path / filename).write_text(json.dumps(value))
    receipt = json.loads((tmp_path / "receipt.json").read_text())
    config = json.loads((tmp_path / "config.json").read_text())
    receipt["config_sha256"] = config["config_sha256"]
    receipt["receipt_sha256"] = digest(
        {key: item for key, item in receipt.items() if key != "receipt_sha256"}
    )
    (tmp_path / "receipt.json").write_text(json.dumps(receipt))
    assert validate(tmp_path)["valid"] is True


def test_validator_rejects_result_digest_drift(tmp_path):
    _valid_artifact(tmp_path)
    results_path = tmp_path / "results.json"
    results = json.loads(results_path.read_text())
    results["parity"]["passed"] = False
    results_path.write_text(json.dumps(results))
    with pytest.raises(ValueError, match="results digest mismatch"):
        validate(tmp_path)

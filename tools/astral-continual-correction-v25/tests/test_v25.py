from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


V25 = load("astral_v25_test_subject", "v25.py")
sys.path.insert(0, str(ROOT))
VALIDATOR = load("astral_v25_validator_test_subject", "validator_v25.py")


def contract():
    return json.loads((ROOT / "experiment-contract.json").read_text())


def test_positive_sensitivity_and_null_specificity_are_deterministic():
    first = V25.simulate(contract())
    second = V25.simulate(contract())
    assert first == second
    result = first["result"]
    assert result["classification"] == "SyntheticDockerContinualCorrectionHarnessQualified"
    assert result["worlds"]["positive_control"]["gates"]["passed"] is True
    assert result["worlds"]["null_control"]["gates"]["passed"] is False
    assert result["null_specificity_passed"] is True
    assert result["external_states"]["thesis"] == "NotValidated"


def test_record_census_and_update_budgets_are_frozen():
    frozen = contract()
    run = V25.simulate(frozen)
    counts = VALIDATOR.verify_counts(
        frozen,
        run["adaptation"],
        run["updates"],
        run["observations"],
        run["replay"],
    )
    assert counts == {
        "adaptation": 768,
        "updates": 1536,
        "observations": 73728,
        "replay": 11520,
    }
    assert all(
        row["update_slots_consumed"] == (0 if row["condition"] == "frozen" else 8)
        for row in run["updates"]
    )


def test_primary_gate_fails_when_positive_telemetry_predictions_are_destroyed():
    frozen = contract()
    run = V25.simulate(frozen)
    observations = [dict(row) for row in run["observations"]]
    for row in observations:
        if row["world"] == "positive_control" and row["condition"] == "telemetry":
            row["prediction"] = 1 - row["label"]
            row["probability"] = 1.0 - row["label"]
    result = V25.summarize(observations, run["replay"], frozen)
    assert result["qualified"] is False
    assert result["classification"] == "SyntheticDockerContinualCorrectionHarnessNoCandidate"


def test_content_addressed_artifact_validates_and_tampering_fails(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRAL_V25_BASE_IMAGE_DIGEST", "python@sha256:" + "a" * 64)
    monkeypatch.setenv("ASTRAL_V25_IMAGE_ID", "sha256:" + "b" * 64)
    outcome = V25.execute(tmp_path / "astral-v25-building")
    artifact = Path(outcome["artifact"])
    validated = VALIDATOR.validate(artifact)
    assert validated["classification"] == "SyntheticDockerContinualCorrectionHarnessQualified"
    result = artifact / "result.json"
    result.write_text(result.read_text().replace("NotValidated", "Validated", 1))
    try:
        VALIDATOR.validate(artifact)
    except ValueError as exc:
        assert "digest mismatch" in str(exc)
    else:
        raise AssertionError("tampered artifact was accepted")


def test_docker_contract_is_digest_pinned_and_network_free():
    dockerfile = (ROOT / "Dockerfile").read_text()
    runner = (ROOT / "run_docker.py").read_text()
    assert "FROM python@sha256:" in dockerfile
    assert "apt-get" not in dockerfile
    assert "pip install" not in dockerfile
    assert '"--network=none"' in runner
    assert '"--read-only"' in runner
    assert '"--cap-drop=ALL"' in runner
    assert '"--security-opt=no-new-privileges"' in runner
    assert "--pull=false" in runner
    assert os.path.isabs(str(ROOT))

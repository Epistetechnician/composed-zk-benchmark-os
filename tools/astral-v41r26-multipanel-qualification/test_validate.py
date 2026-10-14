from __future__ import annotations

import importlib.util
from pathlib import Path


PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v41r26_validator", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)
WORKER_PATH = Path(__file__).with_name("validate_worker.py")
WORKER_SPEC = importlib.util.spec_from_file_location("v41r26_worker_validator", WORKER_PATH)
assert WORKER_SPEC and WORKER_SPEC.loader
WORKER = importlib.util.module_from_spec(WORKER_SPEC); WORKER_SPEC.loader.exec_module(WORKER)
PREFLIGHT_PATH = Path(__file__).with_name("validate_preflight.py")
PREFLIGHT_SPEC = importlib.util.spec_from_file_location("v41r26_preflight_validator", PREFLIGHT_PATH)
assert PREFLIGHT_SPEC and PREFLIGHT_SPEC.loader
PREFLIGHT = importlib.util.module_from_spec(PREFLIGHT_SPEC); PREFLIGHT_SPEC.loader.exec_module(PREFLIGHT)
CAMPAIGN_PATH = Path(__file__).with_name("validate_campaign.py")
CAMPAIGN_SPEC = importlib.util.spec_from_file_location("v41r26_campaign_validator", CAMPAIGN_PATH)
assert CAMPAIGN_SPEC and CAMPAIGN_SPEC.loader
CAMPAIGN = importlib.util.module_from_spec(CAMPAIGN_SPEC); CAMPAIGN_SPEC.loader.exec_module(CAMPAIGN)


def test_contract_has_sixteen_disjoint_panels_and_fortyeight_runs() -> None:
    packet = MODULE.expected_contract()
    assert packet["run_count"] == 48 and len(packet["panels"]) == 16
    assert [i for panel in packet["panels"] for i in panel["acquisition_indices"]] == list(range(64))
    assert [i for panel in packet["panels"] for i in panel["protected_indices"]] == list(range(256))


def test_gate_requires_all_sixteen_independent_panels() -> None:
    assert MODULE.wilson_lower(16, 16) > 0.80
    assert MODULE.wilson_lower(15, 16) < 0.80


def test_missing_producer_fails_closed(tmp_path: Path) -> None:
    report = MODULE.validate(tmp_path)
    assert report["valid"] is False and report["runtime_authorized"] is False


def test_worker_specs_cover_exact_cross_product() -> None:
    specs = WORKER.expected_specs()
    assert len(specs) == 48
    assert "v41r26-panel-0-seed-411017" in specs
    assert "v41r26-panel-15-seed-411043" in specs


def test_missing_worker_bundle_fails_closed(tmp_path: Path) -> None:
    assert WORKER.validate(tmp_path, tmp_path) == {"valid": False, "errors": ["worker artifact files missing"]}


def test_preflight_expected_rows_cover_full_frozen_instrument() -> None:
    assert len(PREFLIGHT.expected_acquisition_rows()) == 64
    assert len(PREFLIGHT.CONTRACT.expected_protected()["rows"]) == 256


def test_missing_preflight_bundle_fails_closed(tmp_path: Path) -> None:
    assert PREFLIGHT.validate(tmp_path, tmp_path) == {"valid": False, "errors": ["preflight artifact files missing"]}


def test_preflight_decision_rejects_one_protected_failure() -> None:
    acquisition = [{"correct": False} for _ in range(64)]
    protected = [{"correct": True} for _ in range(256)]
    assert PREFLIGHT.decision(acquisition, protected)["training_authorized"] is True
    protected[0]["correct"] = False
    assert PREFLIGHT.decision(acquisition, protected)["errors"] == ["protected_accuracy"]


def test_campaign_aggregate_requires_all_fortyeight_runs() -> None:
    rows = [{"run_spec": spec, "pass": True, "governance_violations": 0}
            for spec in WORKER.expected_specs().values()]
    assert CAMPAIGN.aggregate(rows)["candidate_keep"] is True
    rows[-1]["pass"] = False
    assert CAMPAIGN.aggregate(rows)["candidate_keep"] is False


def test_missing_campaign_bundle_fails_closed(tmp_path: Path) -> None:
    assert CAMPAIGN.validate(tmp_path, tmp_path) == {
        "valid": False, "errors": ["campaign artifact files missing"]}

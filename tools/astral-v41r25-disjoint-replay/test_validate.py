from __future__ import annotations

import importlib.util
from pathlib import Path


PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v41r25_validator", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)

ARTIFACT_PATH = Path(__file__).with_name("validate_artifact.py")
ARTIFACT_SPEC = importlib.util.spec_from_file_location("v41r25_artifact_validator", ARTIFACT_PATH)
assert ARTIFACT_SPEC and ARTIFACT_SPEC.loader
ARTIFACT = importlib.util.module_from_spec(ARTIFACT_SPEC); ARTIFACT_SPEC.loader.exec_module(ARTIFACT)


def test_frozen_panels_are_disjoint() -> None:
    assert not set(MODULE.ACQUISITION) & set(MODULE.PRIOR_ACQUISITION)
    assert not set(MODULE.PROTECTED) & set(MODULE.PRIOR_PROTECTED)


def test_missing_sources_fail_closed(tmp_path: Path) -> None:
    report = MODULE.validate(tmp_path)
    assert report["valid"] is False
    assert report["runtime_authorized"] is False


def test_artifact_contract_independently_rederives_disjoint_bindings() -> None:
    packet = ARTIFACT.expected_contract(ARTIFACT.BASE.INSTRUMENT.expected_packet())
    assert packet["acquisition_case_indices"] == [4, 5, 6, 7]
    assert packet["protected_case_indices"] == list(range(16, 32))
    assert packet["corpus_sha256"] == ARTIFACT.CORPUS_SHA256
    assert packet["panel_weights"] == {"acquisition": 0.75, "protected": 0.25}
    assert packet["gates"]["protected_accuracy_minimum"] == 0.98


def test_artifact_validator_fails_closed_without_complete_bundle(tmp_path: Path) -> None:
    assert ARTIFACT.validate(tmp_path, tmp_path) == {
        "valid": False,
        "errors": ["disjoint replay artifact files missing"],
    }


def test_expected_protected_rows_are_fresh_and_exact() -> None:
    rows = ARTIFACT.expected_protected_rows()
    assert len(rows) == 16
    assert rows[0] == {"case_id": "v41-protected-16",
                       "prompt": "Compute 27 + 20. Return only the integer.",
                       "target": "47", "candidates": ["47", "48", "46", "49"]}
    assert rows[-1]["case_id"] == "v41-protected-31"

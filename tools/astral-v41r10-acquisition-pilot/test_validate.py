from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("validate.py")
SPEC = importlib.util.spec_from_file_location("v41r10_validator", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def rows(correct_per_class: int, *, context: bool) -> list[dict]:
    result = []
    for query_class in MODULE.QUERY_CLASSES:
        for index in range(16):
            result.append(
                {
                    "query_class": query_class,
                    "source_context_present": context,
                    "correct": index < correct_per_class,
                }
            )
    return result


def test_metrics_and_classification() -> None:
    no_update = MODULE.metrics(rows(4, context=False))
    context = MODULE.metrics(rows(15, context=True))
    persistent = MODULE.metrics(rows(12, context=False))
    assert MODULE.classification(
        no_update, context, persistent, 1.0, 1.0, True, 32
    ) == ("PilotAcquisitionSignal", [])
    classification, errors = MODULE.classification(
        no_update, context, MODULE.metrics(rows(8, context=False)), 1.0, 0.875, False, 31
    )
    assert classification == "PilotNoSignal"
    assert {"acquisition_overall", "protected_drop", "reload_exact", "optimizer_steps"} <= set(errors)


def test_contract_and_missing_artifact_fail_closed(tmp_path: Path) -> None:
    contract = MODULE.expected_contract()
    body = {key: value for key, value in contract.items() if key != "contract_sha256"}
    assert contract["contract_sha256"] == MODULE.canonical_hash(body)
    assert MODULE.validate(tmp_path, tmp_path) == {
        "valid": False,
        "errors": ["pilot artifact files missing"],
    }

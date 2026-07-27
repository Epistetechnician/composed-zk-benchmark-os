from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("astral_v25_holistic_test", ROOT / "validate_all.py")
HOLISTIC = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = HOLISTIC
assert SPEC.loader
SPEC.loader.exec_module(HOLISTIC)


def test_claim_contract_is_complete_and_keeps_thesis_unvalidated():
    contract = json.loads((ROOT / "claim-contract.json").read_text())
    expected = contract["expected_claim_statuses"]
    assert list(expected) == [f"C{index:03d}" for index in range(1, 46)]
    assert expected["C003"] == "Proposed"
    assert expected["C005"] == "Proposed"
    assert expected["C014"] == "Proposed"
    assert expected["C045"] == "Not refuted"
    assert contract["thesis_status"] == "NotValidated"


def test_claim_parser_applies_append_only_status_update():
    ledger = """
| C001 | claim | lane | operation | artifact | source | In test | ceiling |
| C001 | In test | Not refuted | artifact | reviewer | reason | ceiling |
| C002 | claim | lane | operation | artifact | source | Refuted | ceiling |
"""
    current, history = HOLISTIC.parse_claim_statuses(ledger)
    assert current == {"C001": "Not refuted", "C002": "Refuted"}
    assert history["C001"] == ["In test", "Not refuted"]


def test_claim_dispositions_do_not_convert_not_refuted_to_proven():
    assert HOLISTIC.claim_disposition("C001", "Not refuted", set()) == "LedgerEvidenceNotRefutedNotProven"
    assert HOLISTIC.claim_disposition("C016", "Refuted", set()) == "RetainedSetupScopedRefutation"
    assert HOLISTIC.claim_disposition("C045", "Not refuted", set()) == "MachineValidatedSyntheticHarnessOnly"

from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.continual_learning import gemma3_paper_recirculation_development_v2 as harness


ROOT = Path(__file__).parents[3]
FIXTURES = ROOT / "experiments/continual_learning/fixtures"
REFERENCE = FIXTURES / "gemma3_recirculation_v2_reference.json"
CANDIDATE = FIXTURES / "gemma3_recirculation_v2_candidate.json"


def _write_mutation(tmp_path: Path, mutation, *, refresh_digest: bool = True) -> Path:
    value = json.loads(CANDIDATE.read_text(encoding="utf-8"))
    mutation(value)
    if refresh_digest:
        value["fixture_sha256"] = harness._payload_digest(value)
    path = tmp_path / "candidate.json"
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def test_frozen_reference_and_candidate_pass_exact_semantic_oracle() -> None:
    result = harness.run_oracle(REFERENCE, CANDIDATE)
    assert result["status"] == "PASS"
    assert result["metric"] == 125.0
    assert len(result["receipt_sha256"]) == 64


@pytest.mark.parametrize(
    "mutation,reason",
    [
        (lambda value: value["measurement"].update({"throughput_windows_per_second": 9999.0}), "throughput_is_not_reproducible"),
        (lambda value: value["policy"].update({"discovery_ids": ["discovery-001", "discovery-001"]}), "duplicate_discovery_detected"),
        (lambda value: value["policy"].update({"assessment_rows_read": ["assessment-001"]}), "assessment_leakage_detected"),
        (lambda value: value["semantic"]["logits"][0].__setitem__(0, 0.250001), "semantic_drift_detected"),
    ],
)
def test_misleading_successes_fail_closed(tmp_path: Path, mutation, reason: str) -> None:
    mutated = _write_mutation(tmp_path, mutation)
    result = harness.run_oracle(REFERENCE, mutated)
    assert result["status"] == "REJECT"
    assert reason in result["reason_codes"]
    assert result["receipt_sha256"] == harness.run_oracle(REFERENCE, mutated)["receipt_sha256"]


def test_malformed_digest_fails_closed(tmp_path: Path) -> None:
    mutated = _write_mutation(
        tmp_path,
        lambda value: value.update({"fixture_sha256": "0" * 64}),
        refresh_digest=False,
    )
    result = harness.run_oracle(REFERENCE, mutated)
    assert result["status"] == "REJECT"
    assert "fixture_digest_does_not_match_canonical_payload" in result["reason_codes"]


def test_duplicate_json_keys_fail_closed(tmp_path: Path) -> None:
    raw = CANDIDATE.read_text(encoding="utf-8").replace(
        '"fixture_id": "candidate-v2",',
        '"fixture_id": "candidate-v2",\n  "fixture_id": "candidate-v2",',
    )
    path = tmp_path / "duplicate.json"
    path.write_text(raw, encoding="utf-8")
    result = harness.run_oracle(REFERENCE, path)
    assert result["status"] == "REJECT"
    assert "duplicate_json_key" in result["reason_codes"][0]


def test_fixtures_have_distinct_measurements_but_identical_semantics() -> None:
    reference = harness.load_fixture(REFERENCE, "reference-v2")
    candidate = harness.load_fixture(CANDIDATE, "candidate-v2")
    assert reference["semantic"] == candidate["semantic"]
    assert reference["measurement"] != candidate["measurement"]

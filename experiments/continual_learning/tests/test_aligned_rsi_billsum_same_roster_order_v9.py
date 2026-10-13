"""Focused contract tests for the V9 local-only experiment.

State slice: aligned-rsi-billsum-same-roster-order-curriculum-v9.
Governance slice: global-experiment-assurance-lifecycle-v1.
"""

import hashlib
from unittest.mock import patch

import pytest

from experiments.continual_learning import aligned_rsi_billsum_same_roster_order_v9 as experiment


def _fit_rows(count=128):
    rows = []
    for index in range(count):
        identifier = hashlib.sha256(f"bill-{index}".encode()).hexdigest()
        rows.append(
            {
                "doc_id": identifier,
                "prompt_token_count": 100 + index,
                "target_token_count": 20 + index % 5,
            }
        )
    return rows


def test_json_loader_rejects_duplicate_contract_keys(tmp_path):
    path = tmp_path / "duplicate.json"
    path.write_text('{"same": 1, "same": 2}', encoding="utf-8")
    with pytest.raises(experiment.ExperimentError, match="duplicate JSON key"):
        experiment.load_json(path)


def test_same_roster_order_arms_keep_identical_ids_and_tokens():
    rows = _fit_rows()
    nll = {row["doc_id"]: float(index % 9) for index, row in enumerate(rows)}
    first = experiment._make_orders(rows, nll, 607)
    repeat = experiment._make_orders(rows, nll, 607)
    other = experiment._make_orders(rows, nll, 701)

    treatment_ids = [row["doc_id"] for row in first[experiment.PRIMARY_ARM]]
    random_ids = [row["doc_id"] for row in first[experiment.CONTROL_ARM]]
    assert treatment_ids == sorted(nll, key=lambda identifier: (nll[identifier], identifier))
    assert set(treatment_ids) == set(random_ids) == set(nll)
    assert treatment_ids != random_ids
    assert [row["doc_id"] for row in repeat[experiment.CONTROL_ARM]] == random_ids
    assert [row["doc_id"] for row in other[experiment.CONTROL_ARM]] != random_ids
    for field in ("prompt_token_count", "target_token_count"):
        assert sum(row[field] for row in first[experiment.PRIMARY_ARM]) == sum(
            row[field] for row in first[experiment.CONTROL_ARM]
        )


def test_ordering_uses_source_id_as_tie_breaker_and_rejects_missing_scores():
    rows = _fit_rows()
    nll = {row["doc_id"]: 1.0 for row in rows}
    orders = experiment._make_orders(rows, nll, 809)
    assert [row["doc_id"] for row in orders[experiment.PRIMARY_ARM]] == sorted(nll)
    with pytest.raises(experiment.ExperimentError, match="complete exact fit roster"):
        experiment._make_orders(rows, dict(list(nll.items())[:-1]), 809)


def test_bootstrap_interval_is_deterministic_and_fail_closed():
    values = [0.08, 0.03, -0.02, 0.11, 0.05]
    assert experiment._bootstrap_interval(values) == experiment._bootstrap_interval(values)
    with pytest.raises(experiment.ExperimentError, match="empty or non-finite"):
        experiment._bootstrap_interval([0.1, float("nan")])


def test_candidate_requires_each_preregistered_gate():
    inputs = {
        "effect_mean": 0.025,
        "ci_low": 0.004,
        "selected_rouge_l": 0.31,
        "base_rouge_l": 0.28,
        "selected_nll": 1.01,
        "base_nll": 1.00,
        "outputs_finite_and_complete": True,
        "identity_patch_max_error": 1e-6,
    }
    assert all(experiment._candidate_gates(**inputs).values())
    for key, value in (
        ("effect_mean", 0.019),
        ("ci_low", 0.0),
        ("selected_rouge_l", 0.27),
        ("selected_nll", 1.051),
        ("outputs_finite_and_complete", False),
        ("identity_patch_max_error", 1.1e-5),
    ):
        altered = dict(inputs)
        altered[key] = value
        assert not all(experiment._candidate_gates(**altered).values())
    with pytest.raises(experiment.ExperimentError, match="non-finite"):
        experiment._candidate_gates(**{**inputs, "ci_low": float("nan")})


def test_frozen_machine_contract_and_local_dependency_identity():
    manifest = experiment._verify_contract()
    assert manifest["state_slice"] == experiment.STATE_SLICE
    assert manifest["governance_slice"] == experiment.GOVERNANCE_SLICE
    assert manifest["independent_acceptance_requested"] is False
    assert manifest["cohorts"]["fit_roster_sha256"] == "7beba247d474ca17858aa7b156c863bf869ee3bec3f0f98ed045bcf2152771aa"
    assert manifest["cohorts"]["assessment_roster_sha256"] == "a0d2608ccc9af7aeaede2e13a07df0e6b29abaff7b831835211116d5411d1f09"
    assert manifest["implementation_dependency"]["sha256"] == experiment.V8_MODULE_SHA256
    assert manifest["implementation_dependency"]["resolved_runtime_lock_sha256"] == experiment.V8_LOCK_SHA256


def test_source_manifest_binds_contract_code_tests_and_authorization():
    with patch.object(experiment, "MANIFEST_SHA256", experiment.sha256_file(experiment.MANIFEST_PATH)):
        source = experiment._source_manifest()
    assert set(source) == {
        "runner",
        "protocol",
        "machine_contract",
        "focused_tests",
        "repository_instructions",
        "pinned_v8_helper",
        "pinned_v8_resolved_runtime_lock",
    }
    assert source["pinned_v8_helper"] == experiment.V8_MODULE_SHA256
    assert source["pinned_v8_resolved_runtime_lock"] == experiment.V8_LOCK_SHA256

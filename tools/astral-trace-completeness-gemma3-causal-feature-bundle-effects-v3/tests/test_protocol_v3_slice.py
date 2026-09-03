"""State slice: astral-trace-completeness-gemma3-causal-feature-bundle-effects-v3."""

import pytest

import protocol_v3_slice as protocol


def test_contract_freezes_new_theory_and_execution_boundary() -> None:
    contract = protocol.public_contract()
    assert contract["contract_sha256"] == protocol.digest_json({key: value for key, value in contract.items() if key != "contract_sha256"})
    assert contract["state_slice"] == "astral-trace-completeness-gemma3-causal-feature-bundle-effects-v3"
    assert contract["estimand"]["interaction"].startswith("kappa_B")
    assert contract["corpus"]["feature_stability"]["minimum_intersection"] == protocol.FEATURE_STABILITY_MIN_INTERSECTION
    assert contract["corpus"]["feature_stability"]["bundle_size"] == protocol.FEATURE_SELECTION_COUNT
    assert contract["node"]["hard_spend_ceiling_usd"] is None
    assert contract["assessment_opened"] is False


def test_bundle_event_replay_accounts_for_typed_intervention() -> None:
    digest = "0" * 64
    metadata = {
        "intervention_kind": "bundle_ablation",
        "operator": "exact-bundle_ablation-v3",
        "feature_index": None,
        "feature_indices": [7, 11, 19],
        "path_id": None,
        "donor_trial_id": "v3-family-000",
    }
    metadata["operator_digest"] = protocol.digest_json({
        "operator": metadata["operator"],
        "module_path": "m",
        "step": 0,
        "feature_indices": metadata["feature_indices"],
        "feature_index": metadata["feature_index"],
        "path_id": metadata["path_id"],
    })
    events = [
        protocol.TraceEvent("run", "trial", 0, "run_start", metadata={"runner": "test"}),
        protocol.TraceEvent("run", "trial", 1, "generation_step_start", step=0),
        protocol.TraceEvent("run", "trial", 2, "input_token", step=0, token_index=0, value_sha256=digest),
        protocol.TraceEvent("run", "trial", 3, "module_input", step=0, module_path="m", value_sha256=digest),
        protocol.TraceEvent("run", "trial", 4, "module_output", step=0, module_path="m", value_sha256=digest, parent_sequence=3),
        protocol.TraceEvent("run", "trial", 5, "intervention", step=0, module_path="m", value_sha256=digest, metadata=metadata),
        protocol.TraceEvent("run", "trial", 6, "cache_read", step=0, value_sha256=digest, metadata={"operation": "get_seq_length"}),
        protocol.TraceEvent("run", "trial", 7, "rng_state", step=0, value_sha256=digest),
        protocol.TraceEvent("run", "trial", 8, "output_distribution", step=0, value_sha256=digest),
        protocol.TraceEvent("run", "trial", 9, "sampled_token", step=0, token_index=1, value_sha256=digest),
        protocol.TraceEvent("run", "trial", 10, "behavioral_outcome", step=0, value_sha256=digest),
        protocol.TraceEvent("run", "trial", 11, "generation_step_end", step=0, value_sha256=digest),
        protocol.TraceEvent("run", "trial", 12, "run_end", value_sha256=digest),
    ]
    expectation = protocol.RunExpectation(1, 1, ("m",), ("m",), (), cache_updates_per_step=0, interventions=1)
    aggregate = protocol.validate_event_stream(events, expectation)
    assert aggregate["missing_event_count"] == 0


def test_node_admission_fails_closed_before_cap_and_identity_are_frozen() -> None:
    receipt = {
        "provider": protocol.NODE_PROVIDER,
        "state_slice": protocol.STATE_SLICE,
        "mission": protocol.STATE_SLICE,
        "execution_authorized": True,
    }
    with pytest.raises(protocol.ProtocolError, match="node identity is not frozen"):
        protocol.require_node_admission(receipt, spend_ceiling_usd=50.0)

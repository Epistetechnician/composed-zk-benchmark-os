"""State slice: astral-trace-completeness-gemma3-causal-feature-effects-v2."""

import sys
import inspect
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import protocol_v2_slice as protocol
import custody_v2_slice as custody


def test_contract_freezes_estimand_and_external_admission_boundary():
    contract = protocol.public_contract()
    assert contract["contract_sha256"] == protocol.digest_json(
        {key: value for key, value in contract.items() if key != "contract_sha256"}
    )
    assert contract["state_slice"] == "astral-trace-completeness-gemma3-causal-feature-effects-v2"
    assert contract["estimand"]["positivity"].startswith("all finite sealed families")
    assert contract["statistics"]["multiplicity"].startswith("Holm")
    assert contract["assessment_opened"] is False
    assert contract["node"]["provider"] == "GiveMeANode"
    assert contract["interchange_operator"]["constant_feature_value"] == 1.0
    assert contract["statistics"]["power"]["simulations"] == 10_000
    assert contract["corpus"]["feature_stability"]["minimum_intersection"] == protocol.FEATURE_SELECTION_COUNT
    assert contract["corpus"]["feature_stability"]["v1_scientific_inputs"] is False


def test_nested_raw_fields_are_rejected():
    try:
        protocol.reject_raw_fields({"statistics": {"logits": [0.1]}})
    except protocol.ProtocolError:
        pass
    else:
        raise AssertionError("nested raw field escaped aggregate validation")


def test_validate_root_uses_canonical_custody_receipt(tmp_path: Path) -> None:
    root = tmp_path / protocol.CUSTODY_ROOT.name
    root.mkdir()
    for name in protocol.SUBROOTS:
        (root / name).mkdir()
    root.chmod(0o700)
    for name in protocol.SUBROOTS:
        (root / name).chmod(0o700)
    assert custody.validate_root(root, tmp_path) == protocol.custody_receipt(root, tmp_path)


def test_runtime_binding_helper_uses_current_runtime_digest_name() -> None:
    source = inspect.getsource(custody.write_identity_bindings)
    assert "V4_RUNTIME_MANIFEST_SHA256" not in source
    assert "RUNTIME_MANIFEST_SHA256" in source


def test_event_replay_accounts_for_typed_intervention_metadata():
    digest = "0" * 64
    intervention_metadata = {
        "intervention_kind": "feature_ablation",
        "operator": "exact-feature_ablation-v2",
        "feature_index": 7,
        "path_id": None,
        "donor_trial_id": "trial",
    }
    intervention_metadata["operator_digest"] = protocol.digest_json(
        {
            "operator": intervention_metadata["operator"],
            "module_path": "m",
            "step": 0,
            "feature_index": intervention_metadata["feature_index"],
            "path_id": intervention_metadata["path_id"],
        }
    )
    events = [
        protocol.TraceEvent("run", "trial", 0, "run_start", metadata={"runner": "test"}),
        protocol.TraceEvent("run", "trial", 1, "generation_step_start", step=0),
        protocol.TraceEvent("run", "trial", 2, "input_token", step=0, token_index=0, value_sha256=digest),
        protocol.TraceEvent("run", "trial", 3, "module_input", step=0, module_path="m", value_sha256=digest),
        protocol.TraceEvent("run", "trial", 4, "module_output", step=0, module_path="m", value_sha256=digest, parent_sequence=3),
        protocol.TraceEvent("run", "trial", 5, "intervention", step=0, module_path="m", value_sha256=digest, metadata=intervention_metadata),
        protocol.TraceEvent("run", "trial", 6, "cache_read", step=0, value_sha256=digest, metadata={"operation": "get_seq_length"}),
        protocol.TraceEvent("run", "trial", 7, "rng_state", step=0, value_sha256=digest),
        protocol.TraceEvent("run", "trial", 8, "output_distribution", step=0, value_sha256=digest),
        protocol.TraceEvent("run", "trial", 9, "sampled_token", step=0, token_index=1, value_sha256=digest),
        protocol.TraceEvent("run", "trial", 10, "behavioral_outcome", step=0, value_sha256=digest),
        protocol.TraceEvent("run", "trial", 11, "generation_step_end", step=0, value_sha256=digest),
        protocol.TraceEvent("run", "trial", 12, "run_end", value_sha256=digest),
    ]
    expectation = protocol.RunExpectation(
        generation_steps=1,
        input_token_count=1,
        module_input_paths=("m",),
        module_output_paths=("m",),
        attention_modules=(),
        cache_updates_per_step=0,
        interventions=1,
    )
    aggregate = protocol.validate_event_stream(events, expectation)
    assert aggregate["event_counts"]["intervention"] == 1
    assert aggregate["missing_event_count"] == 0

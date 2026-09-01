"""State slice: astral-trace-completeness-gemma3-causal-feature-effects-v1."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import adapter_v1 as adapter
import protocol_v1 as protocol


def test_intervention_kinds_are_typed_and_validated():
    import torch

    plan = adapter.CausalIntervention(
        protocol.FEATURE_OUTPUT_PATH,
        0,
        "feature_ablation",
        donor=torch.zeros(1, 2, protocol.HIDDEN_WIDTH),
        feature_index=17,
    )
    plan.validate((protocol.FEATURE_OUTPUT_PATH,))
    assert plan.mode == "replace"
    assert adapter.intervention_metadata(plan)["operator"] == "exact-feature_ablation-v1"


def test_controls_are_typed_without_a_donor():
    plan = adapter.CausalIntervention(protocol.FEATURE_OUTPUT_PATH, 0, "zero")
    emitter = adapter.TraceEmitter("run", "trial")
    adapter._ACTIVE_INTERVENTION_METADATA = adapter.intervention_metadata(plan)
    try:
        event = emitter.emit(
            "intervention",
            step=0,
            module_path=protocol.FEATURE_OUTPUT_PATH,
            value_sha256="0" * 64,
        )
    finally:
        adapter._ACTIVE_INTERVENTION_METADATA = None
    assert event.metadata["intervention_kind"] == "zero"


def test_run_metadata_binds_repeat_index():
    emitter = adapter.TraceEmitter("run", "trial")
    adapter._ACTIVE_RUN_METADATA = {"repeat_index": 2}
    try:
        event = emitter.emit("run_start")
    finally:
        adapter._ACTIVE_RUN_METADATA = None
    assert event.metadata["repeat_index"] == 2


def test_constant_feature_donor_is_distinct_from_ablation():
    import torch

    class FakeTranscoder:
        dtype = torch.float32

        def encode(self, value):
            return value

        def decode(self, features, _model_input):
            return features

    input_activation = torch.zeros(1, 2, protocol.HIDDEN_WIDTH)
    recipient = torch.zeros_like(input_activation)
    donor = adapter.feature_donor(
        FakeTranscoder(),
        input_activation,
        recipient,
        feature_index=3,
        mode="constant",
        donor_features=input_activation,
    )
    assert float(donor[0, -1, 3]) == 1.0


def test_repeated_treatment_helper_checks_all_repeats(monkeypatch):
    import torch

    import run_v1

    family = __import__("corpus_v1").PromptFamily("v1-family-000", "fit", 0, 2, 1, "sum")
    baseline = type("Run", (), {"logits": (torch.zeros(1, 10),), "trial_id": "v1-family-000:natural"})()
    calls = []

    def fake_run(*_args, repeat_index, intervention, **_kwargs):
        calls.append(repeat_index)
        return type(
            "Run",
            (),
            {
                "logits": (torch.zeros(1, 10),),
                "trial_id": f"v1-family-000:{intervention.kind}",
            },
        )(), None

    monkeypatch.setattr(run_v1, "_run_one", fake_run)
    tokenizer = type("Tokenizer", (), {"encode": staticmethod(lambda value, add_special_tokens=False: [int(value)])})()
    rows = run_v1._repeated_effect_rows(
        family,
        (baseline, baseline, baseline),
        adapter.CausalIntervention(protocol.FEATURE_OUTPUT_PATH, 0, "noop"),
        split="fit",
        feature_index=None,
        generator=None,
        tokenizer=tokenizer,
        transcoder_model=None,
        custody_root=Path("/tmp"),
    )
    assert calls == [0, 1, 2]
    assert [row["repeat_index"] for row in rows] == [0, 1, 2]


def test_control_gate_uses_full_logit_delta():
    import run_v1

    rows = [
        {"kind": "noop", "max_abs_logit_delta": 2e-5, "margin_delta": 0.0, "output_tv": 0.0},
        {"kind": "exact_copy", "max_abs_logit_delta": 0.0, "margin_delta": 0.0, "output_tv": 0.0},
        {"kind": "feature_ablation", "max_abs_logit_delta": 0.1, "margin_delta": 0.1, "output_tv": 0.1},
    ]
    result = run_v1._control_gate(rows)
    assert result["controls"]["noop"]["pass"] is False

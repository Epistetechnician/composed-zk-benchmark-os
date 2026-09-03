"""State slice: astral-trace-completeness-gemma3-causal-feature-bundle-effects-v3."""

from __future__ import annotations

import torch

import adapter_v3_slice as adapter
import protocol_v3_slice as protocol


def test_joint_and_singleton_interventions_are_typed() -> None:
    donor = torch.zeros(1, 2, protocol.HIDDEN_WIDTH)
    bundle = adapter.CausalIntervention(
        protocol.FEATURE_OUTPUT_PATH,
        0,
        "bundle_ablation",
        donor=donor,
        feature_indices=(7, 11, 19),
        donor_trial_id="v3-family-000",
    )
    bundle.validate((protocol.FEATURE_OUTPUT_PATH,))
    singleton = adapter.CausalIntervention(
        protocol.FEATURE_OUTPUT_PATH,
        0,
        "singleton_ablation",
        donor=donor,
        feature_index=7,
        feature_indices=(7,),
        donor_trial_id="v3-family-000",
    )
    singleton.validate((protocol.FEATURE_OUTPUT_PATH,))
    metadata = adapter.intervention_metadata(bundle)
    assert metadata["operator"] == "exact-bundle_ablation-v3"
    assert metadata["feature_indices"] == [7, 11, 19]


def test_bundle_donor_changes_only_locked_position() -> None:
    class FakeTranscoder:
        dtype = torch.float32

        def encode(self, value: torch.Tensor) -> torch.Tensor:
            features = torch.zeros(value.shape[0], value.shape[1], protocol.FEATURE_WIDTH)
            features[..., -1, 7] = 2.0
            features[..., -1, 11] = 3.0
            features[..., -1, 19] = 4.0
            return features

        def decode(self, value: torch.Tensor, _residual: torch.Tensor) -> torch.Tensor:
            output = torch.zeros(value.shape[0], value.shape[1], protocol.HIDDEN_WIDTH)
            output[..., -1, 0] = value[..., -1, 7]
            output[..., -1, 1] = value[..., -1, 11]
            output[..., -1, 2] = value[..., -1, 19]
            return output

    transcoder = FakeTranscoder()
    recipient = torch.zeros(1, 3, protocol.HIDDEN_WIDTH)
    donor = adapter.bundle_donor(
        transcoder,
        recipient,
        recipient,
        feature_indices=(7, 11, 19),
        mode="ablate",
    )
    assert torch.equal(donor[..., :-1, :], recipient[..., :-1, :])
    assert torch.equal(donor[..., -1, 3:], recipient[..., -1, 3:])
    assert torch.equal(donor[..., -1, :3], torch.tensor([[-2.0, -3.0, -4.0]]))

"""Behavioral tests for the proof-carrying nano interpretability V1 slice."""

from tools.proof_carrying_nano_interp_v1.runtime import FeatureDetectorNano, ToyHostSlice


def test_attached_nano_emits_replayable_read_only_action():
    host = ToyHostSlice(checkpoint_id="toy-host-checkpoint-v1")
    nano = FeatureDetectorNano(
        identity="feature-detector-v1",
        feature_id="feature-0",
        feature_index=0,
        threshold=2,
    )
    attachment = nano.attach(host, layer=1, site="residual")
    trace = host.capture(prompt="alpha", activation=(3, 1), seed=7, layer=1, site="residual")

    before = host.snapshot()
    first = attachment.run(trace, timestamp="2026-09-16T12:00:00Z")
    second = attachment.run(trace, timestamp="2026-09-16T12:00:00Z")

    assert first.action_digest == second.action_digest
    assert first.outputs == {"detected": True, "feature_value": 3}
    assert first.inputs == {"activation": [3, 1], "prompt": "alpha", "seed": 7}
    assert first.host_context_hash.startswith("sha256:")
    assert first.nano_identity == "feature-detector-v1"
    assert first.layer == 1
    assert first.site == "residual"
    assert host.snapshot() == before

    revised = attachment.run(trace, timestamp="2026-09-16T12:00:00Z", action_version=2)
    assert revised.action_digest != first.action_digest
    assert revised.action_version == 2

    replayed = attachment.replay(first)
    assert replayed.to_dict() == first.to_dict()

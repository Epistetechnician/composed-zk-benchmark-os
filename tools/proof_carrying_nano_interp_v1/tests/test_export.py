"""Audit export behavior for the proof-carrying nano interpretability V1 slice."""

from tools.proof_carrying_nano_interp_v1.proof import LeanProofEngine
from tools.proof_carrying_nano_interp_v1.runtime import FeatureDetectorNano, ToyHostSlice
from tools.proof_carrying_nano_interp_v1.store import ConcurrentStore


def test_exported_bundle_is_digest_bound_and_human_readable(tmp_path):
    host = ToyHostSlice(checkpoint_id="toy-host-checkpoint-v1")
    attachment = FeatureDetectorNano(
        identity="feature-detector-v1",
        feature_id="feature-0",
        feature_index=0,
        threshold=2,
    ).attach(host, layer=1, site="residual")
    action = attachment.run(
        host.capture(
            prompt="alpha",
            activation=(3, 1),
            seed=7,
            layer=1,
            site="residual",
        ),
        timestamp="2026-09-16T12:00:00Z",
    )
    proof = LeanProofEngine().attempt(action)

    with ConcurrentStore(tmp_path / "store.sqlite3") as store:
        store.commit_action(action)
        store.commit_proof(proof)
        bundle = store.export_bundle(action_digest=action.action_digest)
        output_path = tmp_path / "bundle.json"
        written_digest = store.write_bundle(output_path, action_digest=action.action_digest)

    assert proof.status == "checked", proof.diagnostics
    assert written_digest == bundle["bundle_digest"]
    assert bundle["summary"] == "feature-0 at layer 1 residual observed value 3; 1/1 proof attempts kernel-checked."
    assert bundle["proofs"][0]["source"].startswith("import Std")
    assert output_path.read_bytes().decode("utf-8").startswith('{"action":')
    ConcurrentStore.assert_bundle_digest(bundle)
    assert ConcurrentStore.validate_bundle(bundle)["proof_attempts"] == 1
    tampered = {**bundle, "summary": "tampered"}
    try:
        ConcurrentStore.assert_bundle_digest(tampered)
    except ValueError as error:
        assert str(error) == "bundle digest mismatch"
    else:
        raise AssertionError("tampered bundle was accepted")
